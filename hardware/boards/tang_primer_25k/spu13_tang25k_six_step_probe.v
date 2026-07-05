// spu13_tang25k_six_step_probe.v -- Tang 25K six-step robotics probe.
//
// Self-checking board proof for the period-6 rational robotics orbit used by
// software/tests/test_rotc_six_step_rtl_trace.py. The probe applies corrected
// ROTC angle 1 forward, applies angle 4 as the inverse recovery check, and
// verifies exact closure on the sixth commanded pose.
//
// UART at 115200 baud:
//   KIN:P P:5 E:00  PASS
//   KIN:F P:<phase> E:<code>  FAIL

module spu13_tang25k_six_step_probe (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx
);
    localparam CLK_FREQ = 50000000;
    localparam CLKS_PER_BIT = 434;  // 115200 baud at 50 MHz
    localparam START_DELAY = CLK_FREQ / 2;
    localparam LINE_PERIOD = CLK_FREQ / 5;

    // Root vector and commanded phase vectors from build/rotc_six_step_expected.vh.
    // Packed as {sqrt3_part[31:0], rational_part[31:0]}.
    localparam [63:0] ROOT_A = 64'h0000000000000001;
    localparam [63:0] ROOT_B = 64'h0000000200000002;
    localparam [63:0] ROOT_C = 64'h0000000300000003;
    localparam [63:0] ROOT_D = 64'h0000000400000004;

    // Reset.
    reg [7:0] rst_cnt = 8'd0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) begin
        if (!rst_n) rst_cnt <= rst_cnt + 1'b1;
    end

    // Rotor instance.
    reg        rotor_start = 1'b0;
    wire       rotor_done;
    reg [63:0] A_reg = 64'd0;
    reg [63:0] B_reg = 64'd0;
    reg [63:0] C_reg = 64'd0;
    reg [63:0] D_reg = 64'd0;
    reg [63:0] F_reg = 64'd0;
    reg [63:0] G_reg = 64'd0;
    reg [63:0] H_reg = 64'd0;
    reg        apply_div3 = 1'b0;
    wire [63:0] A_out, B_out, C_out, D_out;

    spu13_rotor_core_tdm u_rotc (
        .clk(sys_clk), .rst_n(rst_n),
        .start(rotor_start), .done(rotor_done),
        .A_in(A_reg), .B_in(B_reg), .C_in(C_reg), .D_in(D_reg),
        .F(F_reg), .G(G_reg), .H(H_reg),
        .field_sel(2'b00),
        .bypass_p5(1'b0),
        .bypass_p5_inv(1'b0),
        .apply_div3(apply_div3),
        .A_out(A_out), .B_out(B_out), .C_out(C_out), .D_out(D_out)
    );

    function [63:0] expect_a;
        input [2:0] p;
        begin
            case (p)
                default: expect_a = 64'h0000000000000001;
            endcase
        end
    endfunction

    function [63:0] expect_b;
        input [2:0] p;
        begin
            case (p)
                3'd0: expect_b = 64'h0000000300000003;
                3'd1: expect_b = 64'h0000000400000004;
                3'd2: expect_b = 64'h0000000400000004;
                3'd3: expect_b = 64'h0000000300000003;
                3'd4: expect_b = 64'h0000000200000002;
                3'd5: expect_b = 64'h0000000200000002;
                default: expect_b = 64'd0;
            endcase
        end
    endfunction

    function [63:0] expect_c;
        input [2:0] p;
        begin
            case (p)
                3'd0: expect_c = 64'h0000000200000002;
                3'd1: expect_c = 64'h0000000200000002;
                3'd2: expect_c = 64'h0000000300000003;
                3'd3: expect_c = 64'h0000000400000004;
                3'd4: expect_c = 64'h0000000400000004;
                3'd5: expect_c = 64'h0000000300000003;
                default: expect_c = 64'd0;
            endcase
        end
    endfunction

    function [63:0] expect_d;
        input [2:0] p;
        begin
            case (p)
                3'd0: expect_d = 64'h0000000400000004;
                3'd1: expect_d = 64'h0000000300000003;
                3'd2: expect_d = 64'h0000000200000002;
                3'd3: expect_d = 64'h0000000200000002;
                3'd4: expect_d = 64'h0000000300000003;
                3'd5: expect_d = 64'h0000000400000004;
                default: expect_d = 64'd0;
            endcase
        end
    endfunction

    function is_root;
        input [63:0] a;
        input [63:0] b;
        input [63:0] c;
        input [63:0] d;
        begin
            is_root = (a == ROOT_A) && (b == ROOT_B) &&
                      (c == ROOT_C) && (d == ROOT_D);
        end
    endfunction

    // Self-test sequencer.
    localparam [4:0] S_RESET       = 5'd0;
    localparam [4:0] S_FWD_SETUP   = 5'd1;
    localparam [4:0] S_ROT_START   = 5'd2;
    localparam [4:0] S_ROT_WAIT    = 5'd3;
    localparam [4:0] S_FWD_CHECK   = 5'd4;
    localparam [4:0] S_INV_SETUP   = 5'd5;
    localparam [4:0] S_INV_CHECK   = 5'd6;
    localparam [4:0] S_ADVANCE     = 5'd7;
    localparam [4:0] S_PASS        = 5'd8;
    localparam [4:0] S_FAIL        = 5'd9;

    localparam [0:0] OP_FWD = 1'b0;
    localparam [0:0] OP_INV = 1'b1;

    reg [4:0] test_state = S_RESET;
    reg       op = OP_FWD;
    reg [2:0] kin_phase = 3'd0;
    reg [2:0] active_phase = 3'd0;
    reg [2:0] fail_phase = 3'd0;
    reg [7:0] fail_code = 8'd0;
    reg       all_pass = 1'b1;
    reg       closure_done = 1'b0;

    reg [63:0] cur_a = ROOT_A;
    reg [63:0] cur_b = ROOT_B;
    reg [63:0] cur_c = ROOT_C;
    reg [63:0] cur_d = ROOT_D;
    reg [63:0] cmd_a = 64'd0;
    reg [63:0] cmd_b = 64'd0;
    reg [63:0] cmd_c = 64'd0;
    reg [63:0] cmd_d = 64'd0;

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            test_state <= S_RESET;
            op <= OP_FWD;
            kin_phase <= 3'd0;
            active_phase <= 3'd0;
            fail_phase <= 3'd0;
            fail_code <= 8'd0;
            all_pass <= 1'b1;
            closure_done <= 1'b0;
            rotor_start <= 1'b0;
            A_reg <= 64'd0; B_reg <= 64'd0; C_reg <= 64'd0; D_reg <= 64'd0;
            F_reg <= 64'd0; G_reg <= 64'd0; H_reg <= 64'd0;
            apply_div3 <= 1'b0;
            cur_a <= ROOT_A; cur_b <= ROOT_B; cur_c <= ROOT_C; cur_d <= ROOT_D;
            cmd_a <= 64'd0; cmd_b <= 64'd0; cmd_c <= 64'd0; cmd_d <= 64'd0;
        end else begin
            rotor_start <= 1'b0;

            case (test_state)
                S_RESET: begin
                    if (rst_cnt == 8'hFF) begin
                        kin_phase <= 3'd0;
                        active_phase <= 3'd0;
                        cur_a <= ROOT_A; cur_b <= ROOT_B;
                        cur_c <= ROOT_C; cur_d <= ROOT_D;
                        test_state <= S_FWD_SETUP;
                    end
                end

                S_FWD_SETUP: begin
                    op <= OP_FWD;
                    active_phase <= kin_phase;
                    A_reg <= cur_a; B_reg <= cur_b;
                    C_reg <= cur_c; D_reg <= cur_d;
                    F_reg <= 64'h0000000000000002;
                    G_reg <= 64'h0000000000000002;
                    H_reg <= 64'h00000000FFFFFFFF;
                    apply_div3 <= 1'b1;
                    test_state <= S_ROT_START;
                end

                S_INV_SETUP: begin
                    op <= OP_INV;
                    A_reg <= cmd_a; B_reg <= cmd_b;
                    C_reg <= cmd_c; D_reg <= cmd_d;
                    F_reg <= 64'h0000000000000002;
                    G_reg <= 64'h00000000FFFFFFFF;
                    H_reg <= 64'h0000000000000002;
                    apply_div3 <= 1'b1;
                    test_state <= S_ROT_START;
                end

                S_ROT_START: begin
                    rotor_start <= 1'b1;
                    test_state <= S_ROT_WAIT;
                end

                S_ROT_WAIT: begin
                    if (rotor_done) begin
                        test_state <= (op == OP_FWD) ? S_FWD_CHECK : S_INV_CHECK;
                    end
                end

                S_FWD_CHECK: begin
                    cmd_a <= A_out;
                    cmd_b <= B_out;
                    cmd_c <= C_out;
                    cmd_d <= D_out;

                    if (A_out !== expect_a(kin_phase)) begin
                        fail_phase <= kin_phase;
                        fail_code <= 8'hA0 + {5'd0, kin_phase};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (B_out !== expect_b(kin_phase)) begin
                        fail_phase <= kin_phase;
                        fail_code <= 8'hB0 + {5'd0, kin_phase};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (C_out !== expect_c(kin_phase)) begin
                        fail_phase <= kin_phase;
                        fail_code <= 8'hC0 + {5'd0, kin_phase};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (D_out !== expect_d(kin_phase)) begin
                        fail_phase <= kin_phase;
                        fail_code <= 8'hD0 + {5'd0, kin_phase};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (kin_phase != 3'd5 &&
                                 is_root(A_out, B_out, C_out, D_out)) begin
                        fail_phase <= kin_phase;
                        fail_code <= 8'hF0 + {5'd0, kin_phase};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (kin_phase == 3'd5 &&
                                 !is_root(A_out, B_out, C_out, D_out)) begin
                        fail_phase <= kin_phase;
                        fail_code <= 8'hF0 + {5'd0, kin_phase};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else begin
                        test_state <= S_INV_SETUP;
                    end
                end

                S_INV_CHECK: begin
                    if (A_out !== cur_a || B_out !== cur_b ||
                        C_out !== cur_c || D_out !== cur_d) begin
                        fail_phase <= kin_phase;
                        fail_code <= 8'hE0 + {5'd0, kin_phase};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else begin
                        test_state <= S_ADVANCE;
                    end
                end

                S_ADVANCE: begin
                    cur_a <= cmd_a;
                    cur_b <= cmd_b;
                    cur_c <= cmd_c;
                    cur_d <= cmd_d;

                    if (kin_phase == 3'd5) begin
                        closure_done <= 1'b1;
                        test_state <= S_PASS;
                    end else begin
                        kin_phase <= kin_phase + 1'b1;
                        test_state <= S_FWD_SETUP;
                    end
                end

                S_PASS: begin
                    active_phase <= 3'd5;
                end

                S_FAIL: begin
                    active_phase <= fail_phase;
                end

                default: begin
                    fail_phase <= kin_phase;
                    fail_code <= 8'hFF;
                    all_pass <= 1'b0;
                    test_state <= S_FAIL;
                end
            endcase
        end
    end

    // LEDs: active-low PASS/FAIL plus heartbeat.
    reg [25:0] blink_cnt = 26'd0;
    always @(posedge sys_clk) blink_cnt <= blink_cnt + 1'b1;

    assign led[0] = ~blink_cnt[24];
    assign led[1] = ~(test_state == S_PASS);
    assign led[2] = ~(test_state == S_FAIL);

    // UART telemetry.
    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits = 4'd0;
    reg [15:0] baud_cnt = 16'd0;
    reg        tx_busy = 1'b0;
    reg [7:0]  tx_byte = 8'd0;
    reg        tx_go = 1'b0;
    reg [27:0] line_timer = 28'd0;
    reg [27:0] start_cnt = 28'd0;
    reg        start_ready = 1'b0;
    reg [4:0]  msg_idx = 5'd0;
    reg        line_active = 1'b0;

    assign uart_tx = tx_shift[0];

    function [7:0] hex2ascii;
        input [3:0] h;
        begin
            hex2ascii = (h < 10) ? (8'h30 + h) : (8'h37 + h);
        end
    endfunction

    function [7:0] msg_byte;
        input [4:0] idx;
        reg [7:0] status_ch;
        reg [2:0] phase_ch;
        begin
            status_ch = (test_state == S_PASS) ? "P" :
                        (test_state == S_FAIL) ? "F" : ".";
            phase_ch = (test_state == S_FAIL) ? fail_phase : active_phase;
            case (idx)
                5'd0:  msg_byte = "K";
                5'd1:  msg_byte = "I";
                5'd2:  msg_byte = "N";
                5'd3:  msg_byte = ":";
                5'd4:  msg_byte = status_ch;
                5'd5:  msg_byte = " ";
                5'd6:  msg_byte = "P";
                5'd7:  msg_byte = ":";
                5'd8:  msg_byte = 8'h30 + {5'd0, phase_ch};
                5'd9:  msg_byte = " ";
                5'd10: msg_byte = "E";
                5'd11: msg_byte = ":";
                5'd12: msg_byte = hex2ascii(fail_code[7:4]);
                5'd13: msg_byte = hex2ascii(fail_code[3:0]);
                5'd14: msg_byte = 8'h0D;
                5'd15: msg_byte = 8'h0A;
                default: msg_byte = 8'h20;
            endcase
        end
    endfunction

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            tx_shift <= 10'h3FF;
            tx_bits <= 4'd0;
            baud_cnt <= 16'd0;
            tx_busy <= 1'b0;
            tx_byte <= 8'd0;
            tx_go <= 1'b0;
            line_timer <= 28'd0;
            start_cnt <= 28'd0;
            start_ready <= 1'b0;
            msg_idx <= 5'd0;
            line_active <= 1'b0;
        end else begin
            if (tx_busy) begin
                if (baud_cnt < CLKS_PER_BIT - 1) begin
                    baud_cnt <= baud_cnt + 1'b1;
                end else begin
                    baud_cnt <= 16'd0;
                    tx_shift <= {1'b1, tx_shift[9:1]};
                    if (tx_bits == 1) begin
                        tx_busy <= 1'b0;
                        tx_bits <= 4'd0;
                    end else begin
                        tx_bits <= tx_bits - 1'b1;
                    end
                end
            end else if (tx_go) begin
                tx_go <= 1'b0;
                tx_shift <= {1'b1, tx_byte, 1'b0};
                tx_bits <= 4'd10;
                tx_busy <= 1'b1;
                baud_cnt <= 16'd0;
            end else if (!start_ready) begin
                if (start_cnt < START_DELAY - 1)
                    start_cnt <= start_cnt + 1'b1;
                else
                    start_ready <= 1'b1;
            end else if (line_active) begin
                tx_byte <= msg_byte(msg_idx);
                tx_go <= 1'b1;
                if (msg_idx == 5'd15) begin
                    msg_idx <= 5'd0;
                    line_active <= 1'b0;
                end else begin
                    msg_idx <= msg_idx + 1'b1;
                end
            end else if (line_timer < LINE_PERIOD - 1) begin
                line_timer <= line_timer + 1'b1;
            end else begin
                line_timer <= 28'd0;
                msg_idx <= 5'd0;
                line_active <= 1'b1;
            end
        end
    end

endmodule
