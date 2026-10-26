// spu13_neuro_sidecar_adapter.v -- SPI-visible neuro epoch sidecar adapter.
//
// Translates 64-bit SPI instruction words (CMD 0xB1) into epoch sidecar
// control.  Follows the same pattern as spu13_lucas_sidecar.v for QR commit
// and inst_claimed handshake.
//
// Opcode map:
//   0xE0 NEURO_CFG    — load weight+threshold for one neuron
//                        [55:52] neuron_index   0..NUM_NEURONS-1
//                        [51:42] weight           POT_WIDTH bits
//                        [41:32] threshold        POT_WIDTH bits
//   0xE1 NEURO_START  — start an epoch with given envelope
//                        [51:42] expected_norm    L_P_BITS
//                        [41:32] fallback_a       L_P_BITS
//                        [31:22] fallback_b       L_P_BITS
//                        [21:12] initial_spike    NUM_NEURONS bits (cycle 0)
//   0xE2 NEURO_SPIKE  — inject spike pattern (may be sent repeatedly)
//                        [31:22] spike_in         NUM_NEURONS bits
//   0xE3 NEURO_READ   — commit epoch result to QR, read status
//                        [55:52] target QR lane
//                        QR commit A: {commit_b, 32'd0, commit_a, 32'd0}
//                        QR commit B: [63]=accepted [62]=rejected
//                                      [61]=overflow [60]=norm_ok
//                                      [47:32]=spike_total [31:22]=norm_value
//
// When NEURO_READ is issued before an epoch completes, busy=1 is reflected
// in the commit B status word and commit A is zeroed.

module spu13_neuro_sidecar_adapter #(
    parameter NUM_NEURONS      = 8,
    parameter POT_WIDTH        = 12,
    parameter COUNT_WIDTH      = 8,
    parameter EPOCH_CYCLES     = 16,
    parameter EPOCH_COUNT_WIDTH = 8,
    parameter L_P              = 521,
    parameter L_P_BITS         = 10,
    parameter RESET_VAL        = 0,
    parameter LEAK             = 1
) (
    input  wire        clk,
    input  wire        rst_n,

    // SPI instruction interface (from spi_slave, CMD 0xB1)
    input  wire        inst_valid,
    input  wire [63:0] inst_word,
    output wire        inst_claimed,

    // Adapter status
    output reg         busy,
    output reg         error,

    // QR commit (epoch result from NEURO_READ)
    output reg         qr_commit_valid,
    output reg  [3:0]  qr_commit_lane,
    output reg  [63:0] qr_commit_A,
    output reg  [63:0] qr_commit_B,
    output reg  [63:0] qr_commit_C,
    output reg  [63:0] qr_commit_D,

    // Live epoch status (observable without NEURO_READ)
    output wire        epoch_busy,
    output wire        epoch_done,
    output wire        accepted,        // 1-cycle valid only
    output wire        rejected,        // 1-cycle valid only
    output wire        norm_ok,         // 1-cycle valid only
    output wire        overflow_fault,  // 1-cycle valid only
    output wire        epoch_latched_accepted,   // held until next epoch
    output wire        epoch_latched_rejected,   // held until next epoch
    output wire        epoch_latched_overflow,   // held until next epoch
    output wire        epoch_latched_norm_ok,    // held until next epoch
    output wire [NUM_NEURONS-1:0] epoch_token_mask,
    output wire [15:0] epoch_spike_total,
    output wire [L_P_BITS-1:0]    epoch_norm_value,
    output wire [L_P_BITS-1:0]    epoch_commit_a,
    output wire [L_P_BITS-1:0]    epoch_commit_b
);

    localparam [7:0] OP_NEURO_CFG   = 8'hE0;
    localparam [7:0] OP_NEURO_START = 8'hE1;
    localparam [7:0] OP_NEURO_SPIKE = 8'hE2;
    localparam [7:0] OP_NEURO_READ  = 8'hE3;

    wire [7:0] op = inst_word[63:56];
    wire sidecar_op = (op == OP_NEURO_CFG)   || (op == OP_NEURO_START) ||
                       (op == OP_NEURO_SPIKE) || (op == OP_NEURO_READ);
    assign inst_claimed = inst_valid && sidecar_op;

    // ── SPI command handler state ────────────────────────────────
    localparam [2:0] IDLE   = 3'd0;
    localparam [2:0] CFG    = 3'd1;
    localparam [2:0] LAUNCH = 3'd2;
    localparam [2:0] READY  = 3'd3;

    reg [2:0]       state;

    // ── Config registers ─────────────────────────────────────────────
    // These registers hold persistent config between commands.  The _comb
    // variants provide a combinatorial fast-path from NEURO_START so the
    // epoch sidecar sees the correct value on the same posedge that fires
    // epoch_start.
    reg [POT_WIDTH-1:0] cfg_weights   [0:NUM_NEURONS-1];
    reg [POT_WIDTH-1:0] cfg_thresholds [0:NUM_NEURONS-1];
    reg [L_P_BITS-1:0]  cfg_expected_norm_r;
    reg [L_P_BITS-1:0]  cfg_fallback_a_r;
    reg [L_P_BITS-1:0]  cfg_fallback_b_r;

    wire [L_P_BITS-1:0] cfg_expected_norm =
        (inst_valid && sidecar_op && op == OP_NEURO_START) ? inst_word[51:42] : cfg_expected_norm_r;
    wire [L_P_BITS-1:0] cfg_fallback_a =
        (inst_valid && sidecar_op && op == OP_NEURO_START) ? inst_word[41:32] : cfg_fallback_a_r;
    wire [L_P_BITS-1:0] cfg_fallback_b =
        (inst_valid && sidecar_op && op == OP_NEURO_START) ? inst_word[31:22] : cfg_fallback_b_r;

    // ── Epoch sidecar instance ───────────────────────────────────────
    // epoch_start is combinatorial: fires in the same cycle NEURO_START
    // is decoded so the sidecar sees it on the same posedge.
    wire epoch_start;
    assign epoch_start = (state == IDLE && inst_valid && sidecar_op && op == OP_NEURO_START);

    // epoch_spike has combinatorial override from both NEURO_START and
    // NEURO_SPIKE, plus a registered hold so the last pattern persists.
    reg  [NUM_NEURONS-1:0] epoch_spike_r;
    wire [NUM_NEURONS-1:0] epoch_spike =
        (inst_valid && sidecar_op && op == OP_NEURO_SPIKE) ? inst_word[31:22] :
        (inst_valid && sidecar_op && op == OP_NEURO_START) ? inst_word[21:12] :
        epoch_spike_r;

    reg [NUM_NEURONS*POT_WIDTH-1:0] epoch_weights_bus;
    reg [NUM_NEURONS*POT_WIDTH-1:0] epoch_thresholds_bus;

    spu13_neuro_epoch_sidecar #(
        .NUM_NEURONS(NUM_NEURONS),
        .POT_WIDTH(POT_WIDTH),
        .COUNT_WIDTH(COUNT_WIDTH),
        .EPOCH_CYCLES(EPOCH_CYCLES),
        .EPOCH_COUNT_WIDTH(EPOCH_COUNT_WIDTH),
        .LEAK(LEAK),
        .RESET_VAL(RESET_VAL),
        .L_P(L_P),
        .L_P_BITS(L_P_BITS)
    ) u_epoch (
        .clk(clk),
        .rst_n(rst_n),
        .clk_en(1'b1),
        .start_epoch(epoch_start),
        .spike_in(epoch_spike),
        .weights(epoch_weights_bus),
        .thresholds(epoch_thresholds_bus),
        .expected_norm(cfg_expected_norm),
        .fallback_a(cfg_fallback_a),
        .fallback_b(cfg_fallback_b),
        .busy(epoch_busy),
        .done(epoch_done),
        .accepted(accepted),
        .rejected(rejected),
        .norm_ok(norm_ok),
        .overflow_fault(overflow_fault),
        .token_mask(epoch_token_mask),
        .spike_total(epoch_spike_total),
        .proposal_a(),
        .proposal_b(),
        .norm_value(epoch_norm_value),
        .commit_a(epoch_commit_a),
        .commit_b(epoch_commit_b)
    );

    // ── Pack config bus helper ───────────────────────────────────────
    integer ci;
    always @* begin
        epoch_weights_bus = {NUM_NEURONS*POT_WIDTH{1'b0}};
        epoch_thresholds_bus = {NUM_NEURONS*POT_WIDTH{1'b0}};
        for (ci = 0; ci < NUM_NEURONS; ci = ci + 1) begin
            epoch_weights_bus[ci*POT_WIDTH +: POT_WIDTH] = cfg_weights[ci];
            epoch_thresholds_bus[ci*POT_WIDTH +: POT_WIDTH] = cfg_thresholds[ci];
        end
    end

    // ── Result capture registers for NEURO_READ ─────────────────────
    // Auto-latched on epoch_done so the values persist after the 1-cycle
    // accepted/rejected window closes.
    reg [L_P_BITS-1:0] res_commit_a;
    reg [L_P_BITS-1:0] res_commit_b;
    reg             res_accepted;
    reg             res_rejected;
    reg             res_norm_ok;
    reg             res_overflow;
    reg  [15:0]     res_spike_total;
    reg  [L_P_BITS-1:0] res_norm_value;
    reg  [3:0]      read_lane;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            res_commit_a <= {L_P_BITS{1'b0}};
            res_commit_b <= {L_P_BITS{1'b0}};
            res_accepted <= 1'b0;
            res_rejected <= 1'b0;
            res_norm_ok <= 1'b0;
            res_overflow <= 1'b0;
            res_spike_total <= 16'd0;
            res_norm_value <= {L_P_BITS{1'b0}};
        end else if (epoch_done) begin
            res_commit_a <= epoch_commit_a;
            res_commit_b <= epoch_commit_b;
            res_accepted <= accepted;
            res_rejected <= rejected;
            res_norm_ok <= norm_ok;
            res_overflow <= overflow_fault;
            res_spike_total <= epoch_spike_total;
            res_norm_value <= epoch_norm_value;
        end
    end

    assign epoch_latched_accepted = res_accepted;
    assign epoch_latched_rejected = res_rejected;
    assign epoch_latched_overflow = res_overflow;
    assign epoch_latched_norm_ok  = res_norm_ok;

    integer ri;
    reg [POT_WIDTH-1:0] wval, tval;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            busy <= 1'b0;
            error <= 1'b0;
            epoch_spike_r <= {NUM_NEURONS{1'b0}};
            cfg_expected_norm_r <= {L_P_BITS{1'b0}};
            cfg_fallback_a_r <= {L_P_BITS{1'b0}};
            cfg_fallback_b_r <= {L_P_BITS{1'b0}};
            read_lane <= 4'd0;
            qr_commit_valid <= 1'b0;
            qr_commit_lane <= 4'd0;
            qr_commit_A <= 64'd0;
            qr_commit_B <= 64'd0;
            qr_commit_C <= 64'd0;
            qr_commit_D <= 64'd0;
            for (ri = 0; ri < NUM_NEURONS; ri = ri + 1) begin
                cfg_weights[ri] <= {POT_WIDTH{1'b0}};
                cfg_thresholds[ri] <= {POT_WIDTH{1'b0}};
            end
        end else begin
            qr_commit_valid <= 1'b0;

            case (state)
                IDLE: begin
                    if (inst_valid && sidecar_op) begin
                        busy <= 1'b1;
                        error <= 1'b0;
                        if (op == OP_NEURO_CFG) begin
                            wval = inst_word[51:42];
                            tval = inst_word[41:32];
                            if (inst_word[55:52] < NUM_NEURONS) begin
                                cfg_weights[inst_word[55:52]] <= wval;
                                cfg_thresholds[inst_word[55:52]] <= tval;
                            end
                            state <= CFG;
                        end else if (op == OP_NEURO_START) begin
                            // epoch_start is combinatorial; epoch_spike
                            // uses combinatorial mux.  Just latch config.
                            cfg_expected_norm_r <= inst_word[51:42];
                            cfg_fallback_a_r <= inst_word[41:32];
                            cfg_fallback_b_r <= inst_word[31:22];
                            epoch_spike_r <= inst_word[21:12];
                            state <= LAUNCH;
                        end else if (op == OP_NEURO_SPIKE) begin
                            epoch_spike_r <= inst_word[31:22];
                            state <= IDLE;
                            busy <= 1'b0;
                        end else if (op == OP_NEURO_READ) begin
                            read_lane <= (inst_word[55:52] < 13) ? inst_word[55:52] : 4'd0;
                            state <= READY;
                        end else begin
                            error <= 1'b1;
                            state <= IDLE;
                            busy <= 1'b0;
                        end
                    end
                end

                CFG: begin
                    state <= IDLE;
                    busy <= 1'b0;
                end

                LAUNCH: begin
                    // Epoch now running under combinatorial epoch_start.
                    // NEURO_SPIKE commands will update epoch_spike.
                    busy <= 1'b0;
                    state <= IDLE;
                end

                READY: begin
                    qr_commit_valid <= 1'b1;
                    qr_commit_lane <= read_lane;
                    qr_commit_A <= {22'd0, res_commit_b, 22'd0, res_commit_a};
                    qr_commit_B <= {res_accepted, res_rejected, res_overflow,
                                    res_norm_ok, 12'd0,
                                    res_spike_total,
                                    res_norm_value, 22'd0};
                    qr_commit_C <= 64'd0;
                    qr_commit_D <= 64'd0;
                    state <= IDLE;
                    busy <= 1'b0;
                end
            endcase
        end
    end
endmodule
