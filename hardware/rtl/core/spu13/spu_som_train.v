// spu_som_train.v — SOM Weight Update Engine (v1.0)
//
// Dyadic weight update after BMU classification:
//   w_bmu ← w_bmu + (x − w_bmu) >> shift
//
// Reuses spu_som_bmu for BMU finding, then applies the update.
// Weights stored in writable BRAM (replaces hardcoded ROM).
//
// Pipeline:
//   1. SOM_CLASSIFY finds BMU (existing path)
//   2. SOM_TRAIN reads BMU weight from BRAM
//   3. Computes delta = feature − weight (4 subtractors, 1 cycle)
//   4. Arithmetic right-shift by `shift` (1 cycle)
//   5. Adds to weight, writes back to BRAM (1 cycle)
//
// Total: BMU scan (~56 cycles) + 5 cycles update (read + 2 BRAM wait + delta + shift + write)
//
// Parameters:
//   NUM_FEATURES = 4    feature dimensions
//   MAX_NODES    = 9    nodes in writable map
//   WIDTH        = 18   surd coefficient width
//
// CC0 1.0 Universal.

module spu_som_train #(
    parameter NUM_FEATURES = 4,
    parameter MAX_NODES    = 9,
    parameter WIDTH        = 18
)(
    input  wire        clk,
    input  wire        rst_n,

    // ── Control ──────────────────────────────────────────────
    input  wire        train_start,     // pulse to begin update
    output reg         train_done,      // pulses when complete
    input  wire [3:0]  shift_amount,    // dyadic shift (0-15, 0 = no shift)

    // ── BMU result from classifier ──────────────────────────
    input  wire        bmu_valid,
    input  wire [15:0] bmu_node_id,

    // ── Feature vector (from QR regfile, same packing as spu_som_bmu) ──
    input  wire [(2*WIDTH*NUM_FEATURES)-1:0] features,

    // ── Weight BRAM interface (true dual-port, port A = this module) ──
    // Port A: read/write weights for training
    output reg  [$clog2(MAX_NODES)-1:0] bram_addr,
    output reg                          bram_we,
    output reg  [3:0]                   bram_be,     // per-feature byte-enable
    output reg  [(2*WIDTH*NUM_FEATURES)-1:0] bram_wdata,
    input  wire [(2*WIDTH*NUM_FEATURES)-1:0] bram_rdata
);

    localparam SURD_W = 2 * WIDTH;
    localparam VEC_W  = SURD_W * NUM_FEATURES;

    // ── FSM ──────────────────────────────────────────────────
    localparam S_IDLE   = 0;
    localparam S_READ   = 1;   // issue BRAM read for BMU node
    localparam S_BWAIT  = 2;   // wait for BRAM addr to propagate through BMU reg
    localparam S_DREAD  = 3;   // read BRAM data into w_a/w_b
    localparam S_DELTA  = 4;   // compute delta = feature − weight (combinational)
    localparam S_SHIFT  = 5;   // arithmetic right-shift by shift_amount
    localparam S_WRITE  = 6;   // write updated weight back

    reg [2:0] state;

    // ── Registered weight (from BRAM read) ───────────────────
    reg signed [WIDTH-1:0] w_a [0:NUM_FEATURES-1];
    reg signed [WIDTH-1:0] w_b [0:NUM_FEATURES-1];

    // ── Combinational delta and update ──────────────────────
    wire signed [WIDTH-1:0] delta_a [0:NUM_FEATURES-1];
    wire signed [WIDTH-1:0] delta_b [0:NUM_FEATURES-1];

    genvar j;
    generate
        for (j = 0; j < NUM_FEATURES; j = j + 1) begin : gen_feat
            // Extract feature j from flat vector
            wire signed [WIDTH-1:0] feat_a = features[j*SURD_W +: WIDTH];
            wire signed [WIDTH-1:0] feat_b = features[j*SURD_W + WIDTH +: WIDTH];

            // Combinational delta (available in S_DELTA)
            assign delta_a[j] = feat_a - w_a[j];
            assign delta_b[j] = feat_b - w_b[j];
        end
    endgenerate

    // ── Registered update values (computed in S_SHIFT) ───────
    reg signed [WIDTH-1:0] update_a [0:NUM_FEATURES-1];
    reg signed [WIDTH-1:0] update_b [0:NUM_FEATURES-1];
    reg        have_bmu;
    reg [15:0] last_bmu_node_id;
    reg [15:0] train_node_id;

    wire [15:0] selected_bmu_node_id = bmu_valid ? bmu_node_id : last_bmu_node_id;

    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state      <= S_IDLE;
            train_done <= 0;
            bram_addr  <= 0;
            bram_we    <= 0;
            bram_be    <= 4'b0000;
            bram_wdata <= 0;
            have_bmu   <= 0;
            last_bmu_node_id <= 0;
            train_node_id <= 0;
            for (i = 0; i < NUM_FEATURES; i = i + 1) begin
                w_a[i] <= 0; w_b[i] <= 0;
                update_a[i] <= 0; update_b[i] <= 0;
            end
        end else begin
            train_done <= 0;
            bram_we    <= 0;

            if (bmu_valid) begin
                have_bmu <= 1;
                last_bmu_node_id <= bmu_node_id;
            end

            case (state)
                S_IDLE: begin
                    if (train_start && (bmu_valid || have_bmu)) begin
                        train_node_id <= selected_bmu_node_id;
                        bram_addr <= selected_bmu_node_id[$clog2(MAX_NODES)-1:0];
                        state <= S_READ;
                    end
                end

                S_READ: begin
                    // BRAM read issued in S_IDLE, data available in 2 cycles
                    // (registered address in BMU + registered address in BRAM).
                    // Wait one cycle for the address to propagate.
                    state <= S_BWAIT;
                end

                S_BWAIT: begin
                    // BRAM address propagating through rd_addr_r
                    state <= S_DREAD;
                end

                S_DREAD: begin
                    // BRAM data for bmu_node_id is now stable on bram_rdata
                    // (3 cycles after bram_addr was set in S_IDLE).
                    for (i = 0; i < NUM_FEATURES; i = i + 1) begin
                        w_a[i] <= bram_rdata[i*SURD_W +: WIDTH];
                        w_b[i] <= bram_rdata[i*SURD_W + WIDTH +: WIDTH];
                    end
                    state <= S_DELTA;
                end

                S_DELTA: begin
                    // Delta is combinational using w_a/w_b from S_DREAD.
                    // Arithmetic right shift (>>>) rounds toward -infinity,
                    // diverging from the exact-rational Python oracle.
                    // Max single-step divergence is 1 LSB per component
                    // (fixed-point limitation, see audit M2).
                    for (i = 0; i < NUM_FEATURES; i = i + 1) begin
                        update_a[i] <= delta_a[i] >>> shift_amount;
                        update_b[i] <= delta_b[i] >>> shift_amount;
                    end
                    state <= S_SHIFT;
                end

                S_SHIFT: begin
                    // Write updated weight = w + update
                    bram_we   <= 1;
                    bram_be   <= 4'b1111;
                    bram_addr <= train_node_id[$clog2(MAX_NODES)-1:0];
                    for (i = 0; i < NUM_FEATURES; i = i + 1) begin
                        bram_wdata[i*SURD_W +: WIDTH]            <= w_a[i] + update_a[i];
                        bram_wdata[i*SURD_W + WIDTH +: WIDTH]    <= w_b[i] + update_b[i];
                    end
                    state <= S_WRITE;
                end

                S_WRITE: begin
                    train_done <= 1;
                    state      <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
