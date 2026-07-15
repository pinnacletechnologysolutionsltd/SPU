`timescale 1ns / 1ps

// spu_som_sidecar_top.v — Standalone SOM edge classifier sidecar.
//
// Decoupled from the 13-axis SPU-13 manifold.  Exposes the rational SOM/BMU
// classifier over the existing SPI 0xA5 config-write path (no changes to
// spu_spi_slave.v needed):
//
//   sel=4  — write one SOM weight feature   (cfg_addr=node, cfg_material=feat,
//             cfg_data[35:0]={Q[17:0],P[17:0]})
//   sel=5  — load one input feature vector   (cfg_material=feat,
//             cfg_data[35:0]={Q[17:0],P[17:0]})
//   sel=6  — run classification, commit BMU  (pulses start as combinatorial
//             one-shot, registers done to avoid NBA race)
//             results to QR readback
//
// Results read back through SPI 0xAE (QR Commit):
//   A[63:0] = {best_node_id[15:0], second_node_id[15:0],
//              cluster_label[15:0], 12'b0, has_second}
//   B[63:0] = best_q[63:0]
//   C[63:0] = second_q[63:0]
//   D[63:0] = confidence_gap[63:0]
//
// Fits Tang 25K: ~14k LUT, 4 BRAM, 0 DSP (SOM BMU probe was 15k LUT with
// self-test sequencer; this omits the sequencer).

module spu_som_sidecar_top #(
    parameter NUM_FEATURES = 4,
    parameter MAX_NODES    = 7,
    parameter WIDTH        = 18
) (
    input  wire        clk,
    input  wire        rst_n,

    // Config writes from SPI slave (0xA5 decode)
    input  wire        cfg_wr_en,
    input  wire [2:0]  cfg_sel,
    input  wire [7:0]  cfg_material,
    input  wire [9:0]  cfg_addr,
    input  wire [63:0] cfg_data,

    // QR commit readback (SPI 0xAE path)
    output reg         qr_commit_valid,
    output reg  [3:0]  qr_commit_lane,
    output reg  [63:0] qr_commit_A,
    output reg  [63:0] qr_commit_B,
    output reg  [63:0] qr_commit_C,
    output reg  [63:0] qr_commit_D,

    // Status
    output wire [7:0]  debug_status,
    output wire [2:0]  debug_state
);

    localparam FEATURE_W = 2 * WIDTH;                // 36
    localparam VEC_W     = NUM_FEATURES * FEATURE_W; // 144
    localparam ADDR_W    = $clog2(MAX_NODES);        // 3
    localparam NODE_W    = VEC_W;

    localparam [2:0] SEL_WEIGHT    = 3'd4;
    localparam [2:0] SEL_FEATURE   = 3'd5;
    localparam [2:0] SEL_CLASSIFY  = 3'd6;

    localparam [1:0] S_IDLE    = 2'd0;
    localparam [1:0] S_BUSY    = 2'd1;
    localparam [1:0] S_COMMIT  = 2'd2;

    reg [1:0] state;
    reg       bmu_done_r;

    // Feature vector register file (4 features, each {Q[17:0], P[17:0]})
    reg [FEATURE_W-1:0] feature_reg [0:NUM_FEATURES-1];

    // ── BMU instantiation ─────────────────────────────────────────────
    reg  [VEC_W-1:0] feat_vec_r;  // registered feature vector for BMU

    // bmu_start: true one-shot pulse on the rising edge of run.
    // Using a shift-register edge detector avoids holding start high
    // throughout the BMU scan (which would cause immediate re-trigger
    // when the BMU re-enters SCAN_IDLE after SCAN_DONE).
    reg         run;
    reg         run_prev;
    wire        bmu_start = run && !run_prev;
    wire        bmu_done;

    wire [VEC_W-1:0] feature_weights;
    genvar gf;
    generate
        for (gf = 0; gf < NUM_FEATURES; gf = gf + 1) begin : g_fw
            assign feature_weights[gf*FEATURE_W +: WIDTH]       = {WIDTH{1'b0}};
            assign feature_weights[gf*FEATURE_W + WIDTH +: WIDTH] = {{(WIDTH-1){1'b0}}, 1'b1};
        end
    endgenerate

    // Training port (driven combinatorially for weight writes)
    // Training port (registered to avoid NBA race with combinatorial train_we)
    reg  [ADDR_W-1:0] train_addr_r;
    reg  [3:0]        train_be_r;
    reg  [NODE_W-1:0] train_wdata_r;
    reg               train_we_r;
    wire              train_we = train_we_r;
    wire [ADDR_W-1:0] train_addr = train_addr_r;
    wire [3:0]        train_be   = train_be_r;
    wire [NODE_W-1:0] train_wdata = train_wdata_r;

    wire        bmu_valid;
    wire [15:0] best_node_id;
    wire [15:0] second_node_id;
    wire [15:0] cluster_label;
    wire [63:0] best_q;
    wire [63:0] second_q;
    wire [63:0] confidence_gap;
    wire        has_second;

    spu_som_bmu #(
        .NUM_FEATURES(NUM_FEATURES),
        .MAX_NODES(MAX_NODES),
        .WIDTH(WIDTH)
    ) u_bmu (
        .clk(clk),
        .rst_n(rst_n),
        .start(bmu_start),
        .done(bmu_done),
        .features(feat_vec_r),
        .feature_weights(feature_weights),
        .bmu_valid(bmu_valid),
        .best_node_id(best_node_id),
        .second_node_id(second_node_id),
        .cluster_label(cluster_label),
        .best_q(best_q),
        .second_q(second_q),
        .confidence_gap(confidence_gap),
        .has_second(has_second),
        .axiomatic_level(2'b00),
        .axiomatic_fault(),
        .fault_type(),
        .fault_count(),
        .train_we(train_we),
        .train_addr(train_addr),
        .train_be(train_be),
        .train_wdata(train_wdata),
        .train_rdata()
    );

    // ── Latched result registers ──────────────────────────────────────
    reg [15:0] r_best_node_id;
    reg [15:0] r_second_node_id;
    reg [15:0] r_cluster_label;
    reg [63:0] r_best_q;
    reg [63:0] r_second_q;
    reg [63:0] r_confidence_gap;
    reg        r_has_second;

    // ── Pack 36-bit feature from cfg_data ─────────────────────────────
    //  cfg_data[35:0] = {Q[17:0], P[17:0]}
    wire [FEATURE_W-1:0] unpacked_feature = cfg_data[FEATURE_W-1:0];

    // ── Main FSM ──────────────────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state          <= S_IDLE;
            run            <= 1'b0;
            run_prev       <= 1'b0;
            bmu_done_r     <= 1'b0;
            feat_vec_r     <= {VEC_W{1'b0}};
            train_addr_r   <= {ADDR_W{1'b0}};
            train_be_r     <= 4'b0000;
            train_wdata_r  <= {NODE_W{1'b0}};
            train_we_r     <= 1'b0;
            qr_commit_valid <= 1'b0;
            qr_commit_lane  <= 4'd0;
            qr_commit_A     <= 64'd0;
            qr_commit_B     <= 64'd0;
            qr_commit_C     <= 64'd0;
            qr_commit_D     <= 64'd0;
            r_best_node_id  <= 16'd0;
            r_second_node_id <= 16'd0;
            r_cluster_label <= 16'd0;
            r_best_q        <= 64'd0;
            r_second_q      <= 64'd0;
            r_confidence_gap <= 64'd0;
            r_has_second    <= 1'b0;
            feature_reg[0]  <= {FEATURE_W{1'b0}};
            feature_reg[1]  <= {FEATURE_W{1'b0}};
            feature_reg[2]  <= {FEATURE_W{1'b0}};
            feature_reg[3]  <= {FEATURE_W{1'b0}};
        end else begin
            // Defaults
            qr_commit_valid <= 1'b0;
            bmu_done_r      <= bmu_done;
            run_prev        <= run;
            train_we_r      <= 1'b0;

            case (state)
                S_IDLE: begin
                    if (cfg_wr_en) begin
                        case (cfg_sel)
                            SEL_WEIGHT: begin
                                // Latch data this cycle; assert train_we next cycle
                                train_addr_r <= cfg_addr[ADDR_W-1:0];
                                train_be_r   <= 4'b0001 << cfg_material[1:0];
                                train_wdata_r <= pack_weight(
                                    cfg_material[1:0],
                                    unpacked_feature
                                );
                                train_we_r   <= 1'b1;
                            end

                            SEL_FEATURE: begin
                                feature_reg[cfg_material[1:0]] <= unpacked_feature;
                            end

                            SEL_CLASSIFY: begin
                                // Register feature vector, raise run flag
                                feat_vec_r <= {
                                    feature_reg[3],
                                    feature_reg[2],
                                    feature_reg[1],
                                    feature_reg[0]
                                };
                                run   <= 1'b1;
                                state <= S_BUSY;
                            end
                        endcase
                    end
                end

                S_BUSY: begin
                    if (bmu_done) begin
                        r_best_node_id   <= best_node_id;
                        r_second_node_id <= second_node_id;
                        r_cluster_label  <= cluster_label;
                        r_best_q         <= best_q;
                        r_second_q       <= second_q;
                        r_confidence_gap <= confidence_gap;
                        r_has_second     <= has_second;
                        run              <= 1'b0;
                        state            <= S_COMMIT;
                    end
                end

                S_COMMIT: begin
                    qr_commit_valid <= 1'b1;
                    qr_commit_lane  <= 4'd0;
                    qr_commit_A     <= {
                        r_best_node_id,
                        r_second_node_id,
                        r_cluster_label,
                        15'd0,          // 64 - 16*3 - 1 = 15 bits padding
                        r_has_second
                    };
                    qr_commit_B     <= r_best_q;
                    qr_commit_C     <= r_second_q;
                    qr_commit_D     <= r_confidence_gap;
                    state           <= S_IDLE;
                end
            endcase
        end
    end

    // ── Debug outputs ─────────────────────────────────────────────────
    assign debug_state = state;
    assign debug_status = {
        3'd0,
        bmu_done,
        run,
        train_we_r,
        cfg_sel
    };

    // ── Helper: pack a single feature into a node-width vector ─────────
    function [NODE_W-1:0] pack_weight;
        input [3:0]             feat;
        input [FEATURE_W-1:0]   val;
        integer i;
        begin
            pack_weight = {NODE_W{1'b0}};
            for (i = 0; i < NUM_FEATURES; i = i + 1) begin
                if (i == feat)
                    pack_weight[i*FEATURE_W +: FEATURE_W] = val;
            end
        end
    endfunction

endmodule
