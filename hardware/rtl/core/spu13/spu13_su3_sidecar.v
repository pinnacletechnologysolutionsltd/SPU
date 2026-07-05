// spu13_su3_sidecar.v -- SPI-visible SU3 matrix multiply adapter.
//
// Probe instruction format, delivered through the existing SPI CMD 0xB1 path:
//   EA SU3_START   [51:48]=result element 0..8 to capture, starts load phase
//   E8 SU3_LOAD_A  [55:52]=element 0..8, [50:48]=word 0..7, [31:0]=data
//   E9 SU3_LOAD_B  [55:52]=element 0..8, [50:48]=word 0..7, [31:0]=data
//   EB SU3_READ    [55:52]=QR lane, [51:48]=captured element; commits 256-bit result
//
// LOAD_A and LOAD_B are streaming commands. After START, send elements in row-major
// order, each as word 0..7. The sidecar forwards each completed 256-bit element
// directly into spu13_su3_mult; it does not duplicate the multiplier's matrix store.
//
// Element word order matches spu13_su3_mult:
//   word 0..3 = real c0,c1,c2,c3
//   word 4..7 = imag c0,c1,c2,c3
//
// Result commit maps one 256-bit element to QR components:
//   A = bits  63:0, B = 127:64, C = 191:128, D = 255:192

module spu13_su3_sidecar #(
    parameter EXTERNAL_MULT = 0
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        inst_valid,
    input  wire [63:0] inst_word,
    output wire        inst_claimed,
    output reg         busy,
    output reg         error,
    output reg         qr_commit_valid,
    output reg  [3:0]  qr_commit_lane,
    output reg  [63:0] qr_commit_A,
    output reg  [63:0] qr_commit_B,
    output reg  [63:0] qr_commit_C,
    output reg  [63:0] qr_commit_D,
    output wire [7:0]  debug_status,
    output wire [2:0]  debug_state,

    // Optional external M31 multiplier interface. When EXTERNAL_MULT=0, the
    // sidecar instantiates its own multiplier and these request pins stay idle.
    output wire        shared_mult_start,
    output wire [31:0] shared_mult_a0,
    output wire [31:0] shared_mult_a1,
    output wire [31:0] shared_mult_a2,
    output wire [31:0] shared_mult_a3,
    output wire [31:0] shared_mult_b0,
    output wire [31:0] shared_mult_b1,
    output wire [31:0] shared_mult_b2,
    output wire [31:0] shared_mult_b3,
    input  wire [31:0] shared_mult_r0,
    input  wire [31:0] shared_mult_r1,
    input  wire [31:0] shared_mult_r2,
    input  wire [31:0] shared_mult_r3,
    input  wire        shared_mult_done,
    input  wire        shared_mult_busy
);
    localparam [7:0] OP_SU3_LOAD_A = 8'hE8;
    localparam [7:0] OP_SU3_LOAD_B = 8'hE9;
    localparam [7:0] OP_SU3_START  = 8'hEA;
    localparam [7:0] OP_SU3_READ   = 8'hEB;

    localparam [2:0] SIDE_IDLE   = 3'd0;
    localparam [2:0] SIDE_LOAD_A = 3'd1;
    localparam [2:0] SIDE_LOAD_B = 3'd2;
    localparam [2:0] SIDE_WAIT   = 3'd3;

    wire [7:0] op = inst_word[63:56];
    wire sidecar_op = (op == OP_SU3_LOAD_A) || (op == OP_SU3_LOAD_B) ||
                      (op == OP_SU3_START)  || (op == OP_SU3_READ);
    assign inst_claimed = inst_valid && sidecar_op;

    reg [255:0] elem_buffer;
    reg [255:0] selected_result;
    reg [3:0]   selected_elem;
    reg         result_ready;

    reg [2:0] state;
    reg [3:0] stream_idx;
    reg [2:0] chunk_idx;
    reg [4:0] result_idx;

    wire [3:0] cmd_elem = inst_word[55:52];
    wire [3:0] cmd_lane = inst_word[55:52];
    wire [3:0] cmd_read_elem = inst_word[51:48];
    wire [2:0] cmd_word = inst_word[50:48];
    wire [31:0] cmd_data = inst_word[31:0];
    wire cmd_elem_ok = (cmd_elem < 4'd9);
    wire cmd_read_elem_ok = (cmd_read_elem < 4'd9);
    wire cmd_stream_match = cmd_elem_ok && (cmd_elem == stream_idx) && (cmd_word == chunk_idx);

    function [255:0] merge_chunk;
        input [255:0] current;
        input [2:0] word_idx;
        input [31:0] data;
        reg [255:0] merged;
        begin
            merged = current;
            case (word_idx)
                3'd0: merged[31:0]    = data;
                3'd1: merged[63:32]   = data;
                3'd2: merged[95:64]   = data;
                3'd3: merged[127:96]  = data;
                3'd4: merged[159:128] = data;
                3'd5: merged[191:160] = data;
                3'd6: merged[223:192] = data;
                3'd7: merged[255:224] = data;
            endcase
            merge_chunk = merged;
        end
    endfunction

    wire [255:0] merged_elem = merge_chunk(elem_buffer, cmd_word, cmd_data);
    wire         su3_start = inst_valid && (state == SIDE_IDLE) &&
                             (op == OP_SU3_START) && cmd_read_elem_ok;
    wire         su3_load_a = inst_valid && (state == SIDE_LOAD_A) &&
                              (op == OP_SU3_LOAD_A) && cmd_stream_match &&
                              (chunk_idx == 3'd7);
    wire         su3_load_b = inst_valid && (state == SIDE_LOAD_B) &&
                              (op == OP_SU3_LOAD_B) && cmd_stream_match &&
                              (chunk_idx == 3'd7);
    wire [255:0] su3_elem_data = (su3_load_a || su3_load_b) ? merged_elem : 256'd0;
    wire [4:0]   su3_elem_idx;
    wire         su3_done;
    wire         su3_busy;
    wire [255:0] su3_result_data;
    wire         su3_result_valid;
    wire [3:0]   su3_debug_mult_state;

    wire [7:0] debug_load_status = {stream_idx[3:0], chunk_idx[2:0], result_ready};
    wire [7:0] debug_wait_status = {su3_debug_mult_state, result_idx[3:0]};
    assign debug_status = (state == SIDE_WAIT) ? debug_wait_status : debug_load_status;
    assign debug_state = state;

    // ── Shared M31 multiplier ───────────────────────────────────
    wire [31:0] sm_r0, sm_r1, sm_r2, sm_r3;
    wire        sm_done, sm_busy;
    wire        sm_start;
    wire [31:0] sm_a0, sm_a1, sm_a2, sm_a3;
    wire [31:0] sm_b0, sm_b1, sm_b2, sm_b3;
    wire [31:0] sm_local_r0, sm_local_r1, sm_local_r2, sm_local_r3;
    wire        sm_local_done, sm_local_busy;

    assign shared_mult_start = (EXTERNAL_MULT != 0) ? sm_start : 1'b0;
    assign shared_mult_a0 = sm_a0;
    assign shared_mult_a1 = sm_a1;
    assign shared_mult_a2 = sm_a2;
    assign shared_mult_a3 = sm_a3;
    assign shared_mult_b0 = sm_b0;
    assign shared_mult_b1 = sm_b1;
    assign shared_mult_b2 = sm_b2;
    assign shared_mult_b3 = sm_b3;

    assign sm_r0 = (EXTERNAL_MULT != 0) ? shared_mult_r0 : sm_local_r0;
    assign sm_r1 = (EXTERNAL_MULT != 0) ? shared_mult_r1 : sm_local_r1;
    assign sm_r2 = (EXTERNAL_MULT != 0) ? shared_mult_r2 : sm_local_r2;
    assign sm_r3 = (EXTERNAL_MULT != 0) ? shared_mult_r3 : sm_local_r3;
    assign sm_done = (EXTERNAL_MULT != 0) ? shared_mult_done : sm_local_done;
    assign sm_busy = (EXTERNAL_MULT != 0) ? shared_mult_busy : sm_local_busy;

    generate
        if (EXTERNAL_MULT == 0) begin : gen_internal_mult
            spu13_m31_multiplier u_mult (
                .clk(clk), .rst_n(rst_n),
                .start(sm_start), .done(sm_local_done), .busy(sm_local_busy),
                .a0(sm_a0), .a1(sm_a1), .a2(sm_a2), .a3(sm_a3),
                .b0(sm_b0), .b1(sm_b1), .b2(sm_b2), .b3(sm_b3),
                .r0(sm_local_r0), .r1(sm_local_r1),
                .r2(sm_local_r2), .r3(sm_local_r3),
                .rns_error()
            );
        end else begin : gen_external_mult
            assign sm_local_r0 = 32'd0;
            assign sm_local_r1 = 32'd0;
            assign sm_local_r2 = 32'd0;
            assign sm_local_r3 = 32'd0;
            assign sm_local_done = 1'b0;
            assign sm_local_busy = 1'b0;
        end
    endgenerate

    spu13_su3_mult u_su3_mult (
        .clk(clk),
        .rst_n(rst_n),
        .start(su3_start),
        .load_a(su3_load_a),
        .load_b(su3_load_b),
        .elem_data(su3_elem_data),
        .elem_idx(su3_elem_idx),
        .done(su3_done),
        .busy(su3_busy),
        .result_data(su3_result_data),
        .result_valid(su3_result_valid),
        .debug_state(su3_debug_mult_state),
        .m_start(sm_start),
        .ma0(sm_a0), .ma1(sm_a1), .ma2(sm_a2), .ma3(sm_a3),
        .mb0(sm_b0), .mb1(sm_b1), .mb2(sm_b2), .mb3(sm_b3),
        .mr0(sm_r0), .mr1(sm_r1), .mr2(sm_r2), .mr3(sm_r3),
        .m_done(sm_done), .m_busy(sm_busy)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            busy <= 1'b0;
            error <= 1'b0;
            qr_commit_valid <= 1'b0;
            qr_commit_lane <= 4'd0;
            qr_commit_A <= 64'd0;
            qr_commit_B <= 64'd0;
            qr_commit_C <= 64'd0;
            qr_commit_D <= 64'd0;
            state <= SIDE_IDLE;
            stream_idx <= 4'd0;
            chunk_idx <= 3'd0;
            result_idx <= 5'd0;
            elem_buffer <= 256'd0;
            selected_result <= 256'd0;
            selected_elem <= 4'd0;
            result_ready <= 1'b0;
        end else begin
            error <= 1'b0;
            qr_commit_valid <= 1'b0;

            case (state)
                SIDE_IDLE: begin
                    busy <= 1'b0;
                    if (inst_claimed) begin
                        if (op == OP_SU3_START) begin
                            if (cmd_read_elem_ok) begin
                                busy <= 1'b1;
                                stream_idx <= 4'd0;
                                chunk_idx <= 3'd0;
                                result_idx <= 5'd0;
                                elem_buffer <= 256'd0;
                                selected_elem <= cmd_read_elem;
                                selected_result <= 256'd0;
                                result_ready <= 1'b0;
                                state <= SIDE_LOAD_A;
                            end else begin
                                error <= 1'b1;
                            end
                        end else if (op == OP_SU3_READ) begin
                            if (result_ready && cmd_read_elem_ok && cmd_read_elem == selected_elem) begin
                                qr_commit_valid <= 1'b1;
                                qr_commit_lane <= (cmd_lane > 4'd12) ? 4'd0 : cmd_lane;
                                qr_commit_A <= selected_result[63:0];
                                qr_commit_B <= selected_result[127:64];
                                qr_commit_C <= selected_result[191:128];
                                qr_commit_D <= selected_result[255:192];
                            end else begin
                                error <= 1'b1;
                            end
                        end else begin
                            error <= 1'b1;
                        end
                    end
                end

                SIDE_LOAD_A: begin
                    busy <= 1'b1;
                    if (inst_claimed) begin
                        if ((op == OP_SU3_LOAD_A) && cmd_stream_match) begin
                            if (chunk_idx == 3'd7) begin
                                elem_buffer <= 256'd0;
                                chunk_idx <= 3'd0;
                                if (stream_idx == 4'd8) begin
                                    stream_idx <= 4'd0;
                                    state <= SIDE_LOAD_B;
                                end else begin
                                    stream_idx <= stream_idx + 4'd1;
                                end
                            end else begin
                                elem_buffer <= merged_elem;
                                chunk_idx <= chunk_idx + 3'd1;
                            end
                        end else begin
                            error <= 1'b1;
                        end
                    end
                end

                SIDE_LOAD_B: begin
                    busy <= 1'b1;
                    if (inst_claimed) begin
                        if ((op == OP_SU3_LOAD_B) && cmd_stream_match) begin
                            if (chunk_idx == 3'd7) begin
                                elem_buffer <= 256'd0;
                                chunk_idx <= 3'd0;
                                if (stream_idx == 4'd8) begin
                                    stream_idx <= 4'd0;
                                    state <= SIDE_WAIT;
                                end else begin
                                    stream_idx <= stream_idx + 4'd1;
                                end
                            end else begin
                                elem_buffer <= merged_elem;
                                chunk_idx <= chunk_idx + 3'd1;
                            end
                        end else begin
                            error <= 1'b1;
                        end
                    end
                end

                SIDE_WAIT: begin
                    busy <= 1'b1;
                    if (inst_claimed)
                        error <= 1'b1;
                    if (su3_result_valid) begin
                        if (result_idx == selected_elem) begin
                            selected_result <= su3_result_data;
                            result_ready <= 1'b1;
                        end
                        if (result_idx == 5'd8) begin
                            busy <= 1'b0;
                            state <= SIDE_IDLE;
                            result_idx <= 5'd0;
                        end else begin
                            result_idx <= result_idx + 5'd1;
                        end
                    end
                end

                default: begin
                    busy <= 1'b0;
                    state <= SIDE_IDLE;
                end
            endcase
        end
    end
endmodule
