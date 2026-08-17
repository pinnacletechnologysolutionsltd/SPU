`timescale 1ns / 1ps

// spu4_som_edge_wrapper.v — the SPU-4 SOM edge-node product contract (v1.0)
//
// This is the module a customer integrates against for the standalone
// anomaly-detection edge node: sensor features in, exact BMU classification
// out. Local pins only -- no networked reporting, no class-label mapping,
// no cluster-link. Deliberately minimal, matching the same discipline
// spu4_customer_wrapper.v applied to the arithmetic ABI: this is a
// prototype-stage product, and the smallest contract that is actually
// useful beats a larger one nobody has exercised yet.
//
// ── What this wrapper guarantees ─────────────────────────────────────
//  1. Every declared output is driven. No port reads X or Z, ever.
//  2. Weights are hydrated from external SPI flash automatically, once,
//     after reset -- no host is present at runtime. See
//     spu4_som_flash_loader.v and tools/gen_spu4_som_boot_image.py for the
//     other half of this path.
//  3. `features` is CAPTURED on an accepted `start`. The customer may
//     change it on the very next cycle without corrupting a classification
//     in flight.
//  4. Results (`best_node`, `best_quadrance`) are REGISTERED and held
//     stable from `done` until the next accepted `start`.
//  5. `start` asserted while `busy` -- which covers both boot hydration and
//     an in-flight classification -- is ignored, and the violation is
//     reported in `status` rather than silently corrupting state.
//  6. `rst_n` may be driven asynchronously. It is synchronised here -- see
//     spu4_customer_wrapper.v's G6 for the three-week outage this guards
//     against.
//  7. `id` is a synthesis-time constant identifying this module's own ABI
//     version and wrapper variant. WRAPPER_ID=2 in the shared registry
//     docs/SPU4_ABI.md §2a started (1=spu4_customer_wrapper). A different
//     module, a different id word, its own independent major.minor -- see
//     that section for why this one doesn't just reuse spu4_customer_wrapper's.
//
// ── Deliberately NOT in this contract ────────────────────────────────
//  * A node -> semantic class label mapper. spu4_som_edge.v's header calls
//    this out as deployment-specific; hard-coding one now would be
//    guessing at a downstream application this repo doesn't have yet.
//    `best_node` is the raw 2-bit winner, same as the bare classifier.
//  * spu4_cluster_bridge.v / any "report to a controller" path. That
//    module exists for SPU-4's OTHER role -- a per-axis satellite
//    reporting to an SPU-13 governor -- and is a different product with a
//    governor already at the other end. This edge node has none. Decided
//    2026-08-17, explicitly against feature creep: v1 is local pins only.
//  * A live weight-override port. Weights are flash-boot only in v1 --
//    retraining means reprogramming the flash chip and resetting, not a
//    live protocol. An override port is a cheap additive append later
//    (v1.x, this module's own promise below) if a real need shows up.
//
// ── Compatibility promise ────────────────────────────────────────────
// Within v1.x: ports are added only at the end of the list, reserved
// status bits read 0 and may gain meaning, and the meaning of an existing
// port never changes. A breaking change is v2.0 and a new module name --
// same promise spu4_customer_wrapper.v makes, applied to this module.

module spu4_som_edge_wrapper #(
    // Overrides spu4_som_edge's own NUM_FEATURES=3 default. 4 is the
    // decided value (the INA226 capture contract's feature count) used
    // throughout the flash-loader and packer work -- a silent
    // hardware/dataset mismatch here is the exact defect class the 08-16
    // session was hardening against. Do not instantiate this at 3 without
    // a deliberate reason, restated the way spu4_som_edge.v's own header
    // once had to.
    parameter integer NUM_FEATURES = 4,
    parameter integer WIDTH        = 16
) (
    input  wire        clk,
    // Active-low. May be driven asynchronously: released synchronously here.
    input  wire        rst_n,

    // ── Classification handshake ────────────────────────────────────
    // Assert `start` for one cycle to begin. Ignored while `busy` --
    // including during the one-time boot hydration after reset.
    input  wire         start,
    output wire          busy,
    // Level, not a pulse: asserted when results are valid, held until the
    // next accepted `start`. Low from reset until the first classification.
    output wire          done,

    // Feature vector, captured on an accepted start. Same packing
    // spu4_som_edge.v itself uses: feature 0 in the low bits, each feature
    // as {P, Q} with P in the upper WIDTH bits (RationalSurd convention).
    input  wire [NUM_FEATURES * 2 * WIDTH - 1:0] features,

    // Results, registered, valid while `done`.
    output wire [1:0]   best_node,
    output wire [31:0]  best_quadrance,

    // status[0] busy
    // status[1] done
    // status[2] hydrated       -- boot weight-load from flash has completed
    // status[3] start_ignored  -- a start arrived while busy (handshake misuse)
    // status[7:4] reserved, read 0
    output wire [7:0]   status,

    // See header comment 7 and docs/SPU4_ABI.md §2a.
    output wire [15:0]  id,

    // ── Physical SPI pins toward the external weight-flash chip ───────
    // Owned exclusively by the internal spu4_som_flash_loader. Do not
    // share this bus with another consumer without redesigning as an
    // arbiter -- see spu4_som_flash_loader.v's single-owner note.
    output wire         flash_sclk,
    output wire         flash_cs_n,
    output wire         flash_mosi,
    input  wire         flash_miso
);

    localparam integer NODE_W = NUM_FEATURES * 2 * WIDTH;

    localparam [3:0] SPU4_SOM_ID_ABI_MAJOR  = 4'h1;
    localparam [3:0] SPU4_SOM_ID_ABI_MINOR  = 4'h0;
    localparam [3:0] SPU4_SOM_ID_WRAPPER_ID = 4'h2;   // registry: docs/SPU4_ABI.md §2a
    localparam [3:0] SPU4_SOM_ID_RESERVED   = 4'h0;

    assign id = {SPU4_SOM_ID_ABI_MAJOR, SPU4_SOM_ID_ABI_MINOR,
                 SPU4_SOM_ID_WRAPPER_ID, SPU4_SOM_ID_RESERVED};

    // ── Reset synchroniser ─────────────────────────────────────────────
    // Same lesson as spu4_customer_wrapper.v G6: a raw asynchronous reset
    // pad driving internal resets cost this project a three-week board
    // outage (docs/hardware_evidence.md, A7 reset post-mortem).
    reg rst_meta, rst_sync_n;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rst_meta   <= 1'b0;
            rst_sync_n <= 1'b0;
        end else begin
            rst_meta   <= 1'b1;
            rst_sync_n <= rst_meta;
        end
    end

    // ── Boot hydration: one shot, automatic, no host involved ─────────
    reg boot_kicked;
    reg loader_start;
    always @(posedge clk) begin
        if (!rst_sync_n) begin
            boot_kicked  <= 1'b0;
            loader_start <= 1'b0;
        end else begin
            loader_start <= 1'b0;
            if (!boot_kicked) begin
                loader_start <= 1'b1;
                boot_kicked  <= 1'b1;
            end
        end
    end

    wire loader_busy, loader_done;
    wire loader_weight_we;
    wire [1:0] loader_weight_node;
    wire [NODE_W-1:0] loader_weight_data;

    spu4_som_flash_loader #(
        .NUM_FEATURES(NUM_FEATURES), .WIDTH(WIDTH)
    ) u_loader (
        .clk(clk), .rst_n(rst_sync_n),
        .start(loader_start), .busy(loader_busy), .done(loader_done),
        .weight_we(loader_weight_we), .weight_node(loader_weight_node),
        .weight_data(loader_weight_data),
        .flash_sclk(flash_sclk), .flash_cs_n(flash_cs_n),
        .flash_mosi(flash_mosi), .flash_miso(flash_miso)
    );

    reg hydrated_q;
    always @(posedge clk) begin
        if (!rst_sync_n) hydrated_q <= 1'b0;
        else if (loader_done) hydrated_q <= 1'b1;
    end

    // ── Classifier ──────────────────────────────────────────────────
    reg  [NODE_W-1:0] features_q;
    reg                som_start_q;
    wire               som_done;
    wire [1:0]         som_best_node;
    wire [31:0]        som_best_quadrance;

    spu4_som_edge #(
        .NUM_FEATURES(NUM_FEATURES), .WIDTH(WIDTH)
    ) u_som (
        .clk(clk), .rst_n(rst_sync_n),
        .start(som_start_q), .done(som_done),
        .features(features_q),
        .weight_we(loader_weight_we), .weight_node(loader_weight_node),
        .weight_data(loader_weight_data),
        .bmu_valid(), .best_node(som_best_node), .best_quadrance(som_best_quadrance)
    );

    // ── Control ─────────────────────────────────────────────────────
    localparam S_BOOT = 2'd0;
    localparam S_IDLE = 2'd1;
    localparam S_RUN  = 2'd2;

    reg [1:0] state;
    reg       busy_q, done_q, start_ignored_q;
    reg [1:0] best_node_r;
    reg [31:0] best_quadrance_r;

    wire accept = start && (state == S_IDLE);

    always @(posedge clk) begin
        if (!rst_sync_n) begin
            state            <= S_BOOT;
            busy_q           <= 1'b1;
            done_q           <= 1'b0;
            start_ignored_q  <= 1'b0;
            som_start_q      <= 1'b0;
            features_q       <= {NODE_W{1'b0}};
            best_node_r      <= 2'd0;
            best_quadrance_r <= 32'd0;
        end else begin
            som_start_q <= 1'b0;

            // Handshake misuse is reported, never silently absorbed --
            // this includes a start during boot hydration.
            if (start && state != S_IDLE)
                start_ignored_q <= 1'b1;

            case (state)
                S_BOOT: begin
                    if (loader_done) begin
                        busy_q <= 1'b0;
                        state  <= S_IDLE;
                    end
                end

                S_IDLE: begin
                    if (accept) begin
                        features_q      <= features;
                        som_start_q     <= 1'b1;
                        busy_q          <= 1'b1;
                        done_q          <= 1'b0;
                        start_ignored_q <= 1'b0;
                        state           <= S_RUN;
                    end
                end

                S_RUN: begin
                    if (som_done) begin
                        best_node_r      <= som_best_node;
                        best_quadrance_r <= som_best_quadrance;
                        busy_q           <= 1'b0;
                        done_q           <= 1'b1;
                        state            <= S_IDLE;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

    assign busy           = busy_q;
    assign done           = done_q;
    assign best_node      = best_node_r;
    assign best_quadrance = best_quadrance_r;

    assign status = {4'b0000, start_ignored_q, hydrated_q, done_q, busy_q};

endmodule
