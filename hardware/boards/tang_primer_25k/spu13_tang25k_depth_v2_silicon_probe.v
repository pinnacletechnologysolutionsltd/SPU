// spu13_tang25k_depth_v2_silicon_probe.v — depth-v2 silicon proof
//
// First real-hardware verification of the depth-v2 pipeline
// (spu_depth_dispatch -> spu_depth_math -> spu_reciprocal_core ->
// spu_shared_mult35 -> spu_attr_stepper), everything prior to this was
// testbench-verified + synthesizable, never flashed. Fixed test
// triangle "small, screen-corner" from software/lib/gpu_depth_v2_oracle.py's
// TEST_CASES (v0=(10,10) z0=0, v1=(600,30) z1=65535, v2=(300,460)
// z2=32768) -- reusing an already-oracle-checked fixture rather than a
// new one, so the expected values below are the exact numbers
// test_gpu_depth_math_rtl_parity.py already verified in simulation, not
// freshly computed for this probe.
//
// Sequence: pulse depth_setup0 once -> wait for ready0 (exercises the
// full setup arithmetic: dot products, reciprocal, final scale) ->
// seed spu_attr_stepper at (0,0) -> step 200 rows then 300 columns to
// reach pixel (300,200), a point verified inside this triangle -> the
// accumulated value there is compared against the oracle's exact
// expected depth. Self-checks A_z/B_z/C_z/frac_bits AND the final
// per-pixel value against hardcoded expected constants, reports P/F +
// the raw computed depth in hex over UART, same convention as
// spu13_tang25k_lucas_mac_probe.v.
//
// No video PMOD, no functional dependency on it -- this is a digital
// UART proof, not a display demo.

module spu13_tang25k_depth_v2_silicon_probe (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx
);
    localparam CLK_FREQ = 50000000;
    localparam CLKS_PER_BIT = 434;  // 115200 baud at 50 MHz

    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) if (!rst_n) rst_cnt <= rst_cnt + 1;

    // ── Fixed test triangle + expected results (from the oracle) ────
    localparam signed [15:0] A0 = -16'sd430, B0 = -16'sd300;
    localparam signed [31:0] C0 = 32'sd267000;
    localparam signed [15:0] A1 = 16'sd450,  B1 = -16'sd290;
    localparam signed [31:0] C1 = -32'sd1600;
    localparam signed [15:0] A2 = -16'sd20,  B2 = 16'sd590;
    localparam signed [31:0] C2 = -32'sd5700;
    localparam [15:0] Z0 = 16'd0, Z1 = 16'd65535, Z2 = 16'd32768;

    localparam signed [55:0] EXP_A_Z = 56'sd953759359640;
    localparam signed [55:0] EXP_B_Z = 56'sd10847935720;
    localparam signed [55:0] EXP_C_Z = -56'sd9646072953600;
    localparam [6:0] EXP_FRAC = 7'd33;
    localparam signed [55:0] EXP_DEPTH = 56'sd32439;  // at pixel (300,200)
    localparam [9:0] TARGET_X = 10'd300, TARGET_Y = 10'd200;

    // ── Depth-v2 pipeline under test (unit0 only; unit1 tied off) ───
    reg depth_setup0 = 0;
    wire signed [55:0] A_z0, B_z0, C_z0, A_z1, B_z1, C_z1;
    wire [6:0] frac_bits0, frac_bits1;
    wire ready0, ready1;

    spu_depth_dispatch u_dispatch (
        .clk(sys_clk), .rst_n(rst_n),
        .depth_setup0(depth_setup0), .depth_setup1(1'b0),
        .a0_0(A0), .b0_0(B0), .a1_0(A1), .b1_0(B1), .a2_0(A2), .b2_0(B2),
        .c0_0(C0), .c1_0(C1), .c2_0(C2), .z0_0(Z0), .z1_0(Z1), .z2_0(Z2),
        .a0_1(16'sd0), .b0_1(16'sd0), .a1_1(16'sd0), .b1_1(16'sd0),
        .a2_1(16'sd0), .b2_1(16'sd0),
        .c0_1(32'sd0), .c1_1(32'sd0), .c2_1(32'sd0),
        .z0_1(16'd0), .z1_1(16'd0), .z2_1(16'd0),
        .A_z0(A_z0), .B_z0(B_z0), .C_z0(C_z0), .frac_bits0(frac_bits0), .ready0(ready0),
        .A_z1(A_z1), .B_z1(B_z1), .C_z1(C_z1), .frac_bits1(frac_bits1), .ready1(ready1)
    );

    reg attr_setup = 0, attr_step_x = 0, attr_step_y = 0;
    wire signed [55:0] depth_out;
    spu_attr_stepper u_attr (
        .clk(sys_clk), .rst_n(rst_n), .setup(attr_setup),
        .a_coef(A_z0), .b_coef(B_z0), .c_coef(C_z0),
        .step_x(attr_step_x), .step_y(attr_step_y), .frac_bits(frac_bits0),
        .value_out(depth_out)
    );

    // ── Test sequencer ───────────────────────────────────────────────
    localparam [3:0]
        S_RESET = 0, S_SETUP = 1, S_WAIT_READY = 2, S_SEED = 3,
        S_STEP_Y = 4, S_STEP_X = 5, S_CHECK = 6, S_PASS = 7, S_FAIL = 8;
    reg [3:0] test_state = S_RESET;
    reg [9:0] step_cnt = 0;

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            test_state <= S_RESET;
            step_cnt <= 0;
            depth_setup0 <= 0;
            attr_setup <= 0;
            attr_step_x <= 0;
            attr_step_y <= 0;
        end else begin
            depth_setup0 <= 0;
            attr_setup <= 0;
            attr_step_x <= 0;
            attr_step_y <= 0;
            case (test_state)
                S_RESET: if (rst_cnt == 8'hFF) begin
                    depth_setup0 <= 1;
                    test_state <= S_SETUP;
                end
                S_SETUP: test_state <= S_WAIT_READY;
                S_WAIT_READY: if (ready0) begin
                    attr_setup <= 1;
                    test_state <= S_SEED;
                end
                S_SEED: begin
                    step_cnt <= 0;
                    test_state <= S_STEP_Y;
                end
                S_STEP_Y: begin
                    if (step_cnt == TARGET_Y) begin
                        step_cnt <= 0;
                        test_state <= S_STEP_X;
                    end else begin
                        attr_step_y <= 1;
                        step_cnt <= step_cnt + 1;
                    end
                end
                S_STEP_X: begin
                    if (step_cnt == TARGET_X) begin
                        test_state <= S_CHECK;
                    end else begin
                        attr_step_x <= 1;
                        step_cnt <= step_cnt + 1;
                    end
                end
                S_CHECK: begin
                    if (A_z0 == EXP_A_Z && B_z0 == EXP_B_Z && C_z0 == EXP_C_Z &&
                        frac_bits0 == EXP_FRAC && depth_out == EXP_DEPTH)
                        test_state <= S_PASS;
                    else
                        test_state <= S_FAIL;
                end
                S_PASS: ;  // hold
                S_FAIL: ;  // hold
            endcase
        end
    end

    // ── LEDs ─────────────────────────────────────────────────────────
    reg [25:0] blink_cnt = 0;
    always @(posedge sys_clk) blink_cnt <= blink_cnt + 1;
    assign led[0] = ~blink_cnt[24];              // heartbeat
    assign led[1] = ~(test_state == S_PASS);      // off = PASS
    assign led[2] = ~(test_state == S_FAIL);      // off = FAIL

    // ── UART telemetry: "DEPTH2:<P/F> D=<8 hex>\r\n" ─────────────────
    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits = 0;
    reg [15:0] baud_cnt = 0;
    reg        tx_busy = 0;
    reg [7:0]  tx_byte = 0;
    reg        tx_go = 0;
    reg [27:0] line_timer = 0;
    reg        start_ready = 0;
    reg [27:0] start_cnt = 0;
    reg [4:0]  msg_idx = 0;
    reg        line_active = 0;

    assign uart_tx = tx_shift[0];

    function [7:0] hex2ascii;
        input [3:0] h;
        begin hex2ascii = (h < 10) ? (8'h30 + h) : (8'h37 + h); end
    endfunction

    wire [31:0] depth_lo32 = depth_out[31:0];

    function [7:0] msg_byte;
        input [4:0] idx;
        begin
            case (idx)
                5'd0:  msg_byte = "D";
                5'd1:  msg_byte = "E";
                5'd2:  msg_byte = "P";
                5'd3:  msg_byte = "T";
                5'd4:  msg_byte = "H";
                5'd5:  msg_byte = "2";
                5'd6:  msg_byte = ":";
                5'd7:  msg_byte = (test_state == S_PASS) ? "P" :
                                   (test_state == S_FAIL) ? "F" : ".";
                5'd8:  msg_byte = " ";
                5'd9:  msg_byte = "D";
                5'd10: msg_byte = "=";
                5'd11: msg_byte = hex2ascii(depth_lo32[31:28]);
                5'd12: msg_byte = hex2ascii(depth_lo32[27:24]);
                5'd13: msg_byte = hex2ascii(depth_lo32[23:20]);
                5'd14: msg_byte = hex2ascii(depth_lo32[19:16]);
                5'd15: msg_byte = hex2ascii(depth_lo32[15:12]);
                5'd16: msg_byte = hex2ascii(depth_lo32[11:8]);
                5'd17: msg_byte = hex2ascii(depth_lo32[7:4]);
                5'd18: msg_byte = hex2ascii(depth_lo32[3:0]);
                5'd19: msg_byte = 8'h0D;
                5'd20: msg_byte = 8'h0A;
                default: msg_byte = 8'h20;
            endcase
        end
    endfunction

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            tx_shift <= 10'h3FF; tx_bits <= 0; baud_cnt <= 0;
            tx_busy <= 0; tx_go <= 0; start_ready <= 0;
            start_cnt <= 0; line_timer <= 0; msg_idx <= 0; line_active <= 0;
        end else begin
            if (tx_busy) begin
                if (baud_cnt < CLKS_PER_BIT - 1) baud_cnt <= baud_cnt + 1;
                else begin
                    baud_cnt <= 0;
                    tx_shift <= {1'b1, tx_shift[9:1]};
                    if (tx_bits == 1) begin tx_busy <= 0; tx_bits <= 0; end
                    else tx_bits <= tx_bits - 1;
                end
            end else if (tx_go) begin
                tx_go <= 0;
                tx_shift <= {1'b1, tx_byte, 1'b0};
                tx_bits <= 10; tx_busy <= 1;
                baud_cnt <= 0;
            end else if (!start_ready) begin
                if (start_cnt < CLK_FREQ/2 - 1) start_cnt <= start_cnt + 1;
                else start_ready <= 1;
            end else if (line_active) begin
                tx_byte <= msg_byte(msg_idx);
                tx_go <= 1;
                if (msg_idx == 5'd20) begin
                    msg_idx <= 0;
                    line_active <= 0;
                end else begin
                    msg_idx <= msg_idx + 1'b1;
                end
            end else if (line_timer < CLK_FREQ/5 - 1) begin
                line_timer <= line_timer + 1;
            end else begin
                line_timer <= 0;
                msg_idx <= 0;
                line_active <= 1;
            end
        end
    end

endmodule
