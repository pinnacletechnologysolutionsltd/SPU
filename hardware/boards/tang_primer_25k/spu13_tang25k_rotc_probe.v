// spu13_tang25k_rotc_probe.v -- Tang 25K ROTC 0-5 silicon probe.
//
// Self-checking board proof for the corrected ROTC angle catalog. The probe
// instantiates the TDM rotor directly, checks all six canonical VM/RTL trace
// outputs, then runs repeated period-closure feedback on angles 1-5.
//
// UART at 115200 baud:
//   ROTC:P A:5 E:00  PASS
//   ROTC:F A:<angle> E:<code>  FAIL

module spu13_tang25k_rotc_probe (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx
);
    localparam CLK_FREQ = 50000000;
    localparam CLKS_PER_BIT = 434;  // 115200 baud at 50 MHz
    localparam START_DELAY = CLK_FREQ / 2;
    localparam LINE_PERIOD = CLK_FREQ / 5;

    // Canonical trace vector from software/tests/test_rotc_vm_rtl_trace.py.
    localparam [63:0] TRACE_A = 64'h0000000000000001;
    localparam [63:0] TRACE_B = 64'h0000000200000002;
    localparam [63:0] TRACE_C = 64'h0000000300000003;
    localparam [63:0] TRACE_D = 64'h0000000400000004;

    // Feedback vector from hardware/tests/spu13/spu13_rotc_feedback_tb.v.
    // Packed as {sqrt3_part[31:0], rational_part[31:0]}.
    localparam [63:0] FB_A = 64'h0000000100000001;
    localparam [63:0] FB_B = 64'hFFFFFFFD00000002;
    localparam [63:0] FB_C = 64'h0000000400000005;
    localparam [63:0] FB_D = 64'h00000005FFFFFFFC;

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
    reg        bypass_p5 = 1'b0;
    reg        bypass_p5_inv = 1'b0;
    reg        apply_div3 = 1'b0;
    wire [63:0] A_out, B_out, C_out, D_out;

    spu13_rotor_core_tdm u_rotc (
        .clk(sys_clk), .rst_n(rst_n),
        .start(rotor_start), .done(rotor_done),
        .A_in(A_reg), .B_in(B_reg), .C_in(C_reg), .D_in(D_reg),
        .F(F_reg), .G(G_reg), .H(H_reg),
        .field_sel(2'b00),
        .bypass_p5(bypass_p5),
        .bypass_p5_inv(bypass_p5_inv),
        .bypass_ab_cd(1'b0),
        .bypass_ac_bd(1'b0),
        .bypass_ad_bc(1'b0),
        .recompute_A(1'b0),
        .apply_div3(apply_div3),
        .A_out(A_out), .B_out(B_out), .C_out(C_out), .D_out(D_out)
    );

    function [63:0] coeff_f;
        input [2:0] a;
        begin
            case (a)
                3'd0: coeff_f = 64'h0000000000000001;
                3'd1: coeff_f = 64'h0000000000000002;
                3'd2: coeff_f = 64'd0;
                3'd3: coeff_f = 64'h00000000FFFFFFFF;
                3'd4: coeff_f = 64'h0000000000000002;
                3'd5: coeff_f = 64'd0;
                default: coeff_f = 64'd0;
            endcase
        end
    endfunction

    function [63:0] coeff_g;
        input [2:0] a;
        begin
            case (a)
                3'd0: coeff_g = 64'd0;
                3'd1: coeff_g = 64'h0000000000000002;
                3'd2: coeff_g = 64'h0000000000000001;
                3'd3: coeff_g = 64'h0000000000000002;
                3'd4: coeff_g = 64'h00000000FFFFFFFF;
                3'd5: coeff_g = 64'd0;
                default: coeff_g = 64'd0;
            endcase
        end
    endfunction

    function [63:0] coeff_h;
        input [2:0] a;
        begin
            case (a)
                3'd0: coeff_h = 64'd0;
                3'd1: coeff_h = 64'h00000000FFFFFFFF;
                3'd2: coeff_h = 64'd0;
                3'd3: coeff_h = 64'h0000000000000002;
                3'd4: coeff_h = 64'h0000000000000002;
                3'd5: coeff_h = 64'h0000000000000001;
                default: coeff_h = 64'd0;
            endcase
        end
    endfunction

    function bypass_for;
        input [2:0] a;
        begin bypass_for = (a == 3'd2); end
    endfunction

    function bypass_inv_for;
        input [2:0] a;
        begin bypass_inv_for = (a == 3'd5); end
    endfunction

    function div3_for;
        input [2:0] a;
        begin div3_for = (a == 3'd1) || (a == 3'd3) || (a == 3'd4); end
    endfunction

    function [7:0] period_for;
        input [2:0] a;
        begin
            case (a)
                3'd1: period_for = 8'd6;
                3'd2: period_for = 8'd3;
                3'd3: period_for = 8'd2;
                3'd4: period_for = 8'd6;
                3'd5: period_for = 8'd3;
                default: period_for = 8'd1;
            endcase
        end
    endfunction

    function [7:0] repeats_for;
        input [2:0] a;
        begin
            case (a)
                3'd1: repeats_for = 8'd20;
                3'd2: repeats_for = 8'd50;
                3'd3: repeats_for = 8'd50;
                3'd4: repeats_for = 8'd20;
                3'd5: repeats_for = 8'd50;
                default: repeats_for = 8'd1;
            endcase
        end
    endfunction

    function [63:0] expect_a;
        input [2:0] a;
        begin
            case (a)
                default: expect_a = 64'h0000000000000001;
            endcase
        end
    endfunction

    function [63:0] expect_b;
        input [2:0] a;
        begin
            case (a)
                3'd0: expect_b = 64'h0000000200000002;
                3'd1: expect_b = 64'h0000000300000003;
                3'd2: expect_b = 64'h0000000400000004;
                3'd3: expect_b = 64'h0000000400000004;
                3'd4: expect_b = 64'h0000000200000002;
                3'd5: expect_b = 64'h0000000300000003;
                default: expect_b = 64'd0;
            endcase
        end
    endfunction

    function [63:0] expect_c;
        input [2:0] a;
        begin
            case (a)
                3'd0: expect_c = 64'h0000000300000003;
                3'd1: expect_c = 64'h0000000200000002;
                3'd2: expect_c = 64'h0000000200000002;
                3'd3: expect_c = 64'h0000000300000003;
                3'd4: expect_c = 64'h0000000400000004;
                3'd5: expect_c = 64'h0000000400000004;
                default: expect_c = 64'd0;
            endcase
        end
    endfunction

    function [63:0] expect_d;
        input [2:0] a;
        begin
            case (a)
                3'd0: expect_d = 64'h0000000400000004;
                3'd1: expect_d = 64'h0000000400000004;
                3'd2: expect_d = 64'h0000000300000003;
                3'd3: expect_d = 64'h0000000200000002;
                3'd4: expect_d = 64'h0000000300000003;
                3'd5: expect_d = 64'h0000000200000002;
                default: expect_d = 64'd0;
            endcase
        end
    endfunction

    // Self-test sequencer.
    localparam [4:0] S_RESET         = 5'd0;
    localparam [4:0] S_TRACE_SETUP   = 5'd1;
    localparam [4:0] S_ROTATE_START  = 5'd2;
    localparam [4:0] S_ROTATE_WAIT   = 5'd3;
    localparam [4:0] S_TRACE_CHECK   = 5'd4;
    localparam [4:0] S_CLOSURE_SETUP = 5'd5;
    localparam [4:0] S_CLOSURE_CHECK = 5'd6;
    localparam [4:0] S_PASS          = 5'd7;
    localparam [4:0] S_FAIL          = 5'd8;

    localparam [1:0] PHASE_TRACE   = 2'd0;
    localparam [1:0] PHASE_CLOSURE = 2'd1;

    reg [4:0] test_state = S_RESET;
    reg [1:0] phase = PHASE_TRACE;
    reg [2:0] trace_angle = 3'd0;
    reg [2:0] closure_angle = 3'd1;
    reg [7:0] closure_step = 8'd0;
    reg [7:0] closure_repeat = 8'd0;
    reg [2:0] active_angle = 3'd0;
    reg [2:0] fail_angle = 3'd0;
    reg [7:0] fail_code = 8'd0;
    reg       all_pass = 1'b1;
    reg       trace_done = 1'b0;
    reg       closure_done = 1'b0;

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            test_state <= S_RESET;
            phase <= PHASE_TRACE;
            trace_angle <= 3'd0;
            closure_angle <= 3'd1;
            closure_step <= 8'd0;
            closure_repeat <= 8'd0;
            active_angle <= 3'd0;
            fail_angle <= 3'd0;
            fail_code <= 8'd0;
            all_pass <= 1'b1;
            trace_done <= 1'b0;
            closure_done <= 1'b0;
            rotor_start <= 1'b0;
            A_reg <= 64'd0; B_reg <= 64'd0; C_reg <= 64'd0; D_reg <= 64'd0;
            F_reg <= 64'd0; G_reg <= 64'd0; H_reg <= 64'd0;
            bypass_p5 <= 1'b0;
            bypass_p5_inv <= 1'b0;
            apply_div3 <= 1'b0;
        end else begin
            rotor_start <= 1'b0;

            case (test_state)
                S_RESET: begin
                    if (rst_cnt == 8'hFF) begin
                        trace_angle <= 3'd0;
                        test_state <= S_TRACE_SETUP;
                    end
                end

                S_TRACE_SETUP: begin
                    phase <= PHASE_TRACE;
                    active_angle <= trace_angle;
                    A_reg <= TRACE_A; B_reg <= TRACE_B;
                    C_reg <= TRACE_C; D_reg <= TRACE_D;
                    F_reg <= coeff_f(trace_angle);
                    G_reg <= coeff_g(trace_angle);
                    H_reg <= coeff_h(trace_angle);
                    bypass_p5 <= bypass_for(trace_angle);
                    bypass_p5_inv <= bypass_inv_for(trace_angle);
                    apply_div3 <= div3_for(trace_angle);
                    test_state <= S_ROTATE_START;
                end

                S_CLOSURE_SETUP: begin
                    phase <= PHASE_CLOSURE;
                    active_angle <= closure_angle;
                    closure_step <= 8'd0;
                    A_reg <= FB_A; B_reg <= FB_B;
                    C_reg <= FB_C; D_reg <= FB_D;
                    F_reg <= coeff_f(closure_angle);
                    G_reg <= coeff_g(closure_angle);
                    H_reg <= coeff_h(closure_angle);
                    bypass_p5 <= bypass_for(closure_angle);
                    bypass_p5_inv <= bypass_inv_for(closure_angle);
                    apply_div3 <= div3_for(closure_angle);
                    test_state <= S_ROTATE_START;
                end

                S_ROTATE_START: begin
                    rotor_start <= 1'b1;
                    test_state <= S_ROTATE_WAIT;
                end

                S_ROTATE_WAIT: begin
                    if (rotor_done) begin
                        if (phase == PHASE_TRACE)
                            test_state <= S_TRACE_CHECK;
                        else
                            test_state <= S_CLOSURE_CHECK;
                    end
                end

                S_TRACE_CHECK: begin
                    if (A_out !== expect_a(trace_angle)) begin
                        fail_angle <= trace_angle;
                        fail_code <= 8'hA0 + {5'd0, trace_angle};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (B_out !== expect_b(trace_angle)) begin
                        fail_angle <= trace_angle;
                        fail_code <= 8'hB0 + {5'd0, trace_angle};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (C_out !== expect_c(trace_angle)) begin
                        fail_angle <= trace_angle;
                        fail_code <= 8'hC0 + {5'd0, trace_angle};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (D_out !== expect_d(trace_angle)) begin
                        fail_angle <= trace_angle;
                        fail_code <= 8'hD0 + {5'd0, trace_angle};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (trace_angle == 3'd5) begin
                        trace_done <= 1'b1;
                        closure_angle <= 3'd1;
                        closure_repeat <= 8'd0;
                        test_state <= S_CLOSURE_SETUP;
                    end else begin
                        trace_angle <= trace_angle + 1'b1;
                        test_state <= S_TRACE_SETUP;
                    end
                end

                S_CLOSURE_CHECK: begin
                    A_reg <= A_out;
                    B_reg <= B_out;
                    C_reg <= C_out;
                    D_reg <= D_out;

                    if (closure_step == period_for(closure_angle) - 1'b1) begin
                        if (A_out !== FB_A || B_out !== FB_B ||
                            C_out !== FB_C || D_out !== FB_D) begin
                            fail_angle <= closure_angle;
                            fail_code <= 8'hE0 + {5'd0, closure_angle};
                            all_pass <= 1'b0;
                            test_state <= S_FAIL;
                        end else if (closure_repeat == repeats_for(closure_angle) - 1'b1) begin
                            if (closure_angle == 3'd5) begin
                                closure_done <= 1'b1;
                                test_state <= S_PASS;
                            end else begin
                                closure_angle <= closure_angle + 1'b1;
                                closure_repeat <= 8'd0;
                                test_state <= S_CLOSURE_SETUP;
                            end
                        end else begin
                            closure_repeat <= closure_repeat + 1'b1;
                            closure_step <= 8'd0;
                            test_state <= S_ROTATE_START;
                        end
                    end else begin
                        closure_step <= closure_step + 1'b1;
                        test_state <= S_ROTATE_START;
                    end
                end

                S_PASS: begin
                    active_angle <= 3'd5;
                end

                S_FAIL: begin
                    active_angle <= fail_angle;
                end

                default: begin
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
        reg [2:0] angle_ch;
        begin
            status_ch = (test_state == S_PASS) ? "P" :
                        (test_state == S_FAIL) ? "F" : ".";
            angle_ch = (test_state == S_FAIL) ? fail_angle : active_angle;
            case (idx)
                5'd0:  msg_byte = "R";
                5'd1:  msg_byte = "O";
                5'd2:  msg_byte = "T";
                5'd3:  msg_byte = "C";
                5'd4:  msg_byte = ":";
                5'd5:  msg_byte = status_ch;
                5'd6:  msg_byte = " ";
                5'd7:  msg_byte = "A";
                5'd8:  msg_byte = ":";
                5'd9:  msg_byte = 8'h30 + {5'd0, angle_ch};
                5'd10: msg_byte = " ";
                5'd11: msg_byte = "E";
                5'd12: msg_byte = ":";
                5'd13: msg_byte = hex2ascii(fail_code[7:4]);
                5'd14: msg_byte = hex2ascii(fail_code[3:0]);
                5'd15: msg_byte = 8'h0D;
                5'd16: msg_byte = 8'h0A;
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
                if (msg_idx == 5'd16) begin
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
