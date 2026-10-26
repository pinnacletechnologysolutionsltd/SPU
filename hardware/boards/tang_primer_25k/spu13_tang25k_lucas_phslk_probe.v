// spu13_tang25k_lucas_phslk_probe.v -- Lucas PHSLK standalone probe.
//
// Exercises the Lucas MAC PHSLK opcode on Tang 25K.  This is intentionally
// separate from the PSCALE/PCHIRAL fast-path probe so each timing claim has a
// clean artifact.

module spu13_tang25k_lucas_phslk_probe (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx
);
    localparam L_P = 521;
    localparam L_P_BITS = 10;
    localparam CLK_FREQ = 50000000;
    localparam CLKS_PER_BIT = 434;  // 115200 baud at 50 MHz

    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) if (!rst_n) rst_cnt <= rst_cnt + 1'b1;

    reg         mac_start = 0;
    reg  [2:0]  mac_opcode = 3'd4;
    reg  [9:0]  mac_a = 0, mac_b = 0, mac_c = 0, mac_d = 0;
    reg  [9:0]  mac_n2_a = 0, mac_n2_b = 0, mac_d2_a = 0, mac_d2_b = 0;
    wire        mac_busy, mac_done, mac_error;
    wire [9:0]  mac_res_a, mac_res_b;
    wire        mac_phslk_coherent, mac_phslk_zero_divisor;

    spu13_lucas_mac #(
        .L_P(L_P),
        .L_P_BITS(L_P_BITS),
        .FAST_ONLY(1)
    ) u_mac (
        .clk(sys_clk), .rst_n(rst_n),
        .start(mac_start), .opcode(mac_opcode),
        .op_a(mac_a), .op_b(mac_b),
        .op_c(mac_c), .op_d(mac_d),
        .phslk_n2_a(mac_n2_a), .phslk_n2_b(mac_n2_b),
        .phslk_d2_a(mac_d2_a), .phslk_d2_b(mac_d2_b),
        .busy(mac_busy), .done(mac_done),
        .result_a(mac_res_a), .result_b(mac_res_b),
        .phslk_coherent(mac_phslk_coherent),
        .phslk_zero_divisor(mac_phslk_zero_divisor),
        .error(mac_error),
        .norm_violation()
    );

    localparam [2:0] S_RESET = 0;
    localparam [2:0] S_LOAD  = 1;
    localparam [2:0] S_WAIT  = 2;
    localparam [2:0] S_PASS  = 3;
    localparam [2:0] S_FAIL  = 4;
    localparam [2:0] S_DYNAMIC = 5;
    localparam [2:0] S_DYNAMIC_WAIT = 6;

    reg [2:0] test_state = S_RESET;
    reg [1:0] test_idx = 0;
    reg       all_pass = 1'b1;
    reg       functional_done = 1'b0;
    reg [7:0] result_shift = 8'hA5;
    reg [15:0] lfsr = 16'hACE1;

    wire exp_coherent = (test_idx == 2'd0);
    wire exp_zero_divisor = (test_idx == 2'd2);
    wire result_ok = !mac_error &&
                     (mac_phslk_coherent == exp_coherent) &&
                     (mac_phslk_zero_divisor == exp_zero_divisor) &&
                     (mac_res_a == {9'd0, exp_coherent}) &&
                     (mac_res_b == {9'd0, exp_zero_divisor});

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            test_state <= S_RESET;
            test_idx <= 0;
            all_pass <= 1'b1;
            functional_done <= 1'b0;
            result_shift <= 8'hA5;
            lfsr <= 16'hACE1;
            mac_start <= 1'b0;
            mac_opcode <= 3'd4;
            mac_a <= 0; mac_b <= 0; mac_c <= 0; mac_d <= 0;
            mac_n2_a <= 0; mac_n2_b <= 0; mac_d2_a <= 0; mac_d2_b <= 0;
        end else begin
            mac_start <= 1'b0;
            case (test_state)
                S_RESET: begin
                    test_state <= S_LOAD;
                end

                S_LOAD: begin
                    mac_opcode <= 3'd4;
                    case (test_idx)
                        2'd0: begin
                            // (3+5phi)/(2+7phi) == (6+10phi)/(4+14phi)
                            mac_a <= 10'd3; mac_b <= 10'd5;
                            mac_c <= 10'd2; mac_d <= 10'd7;
                            mac_n2_a <= 10'd6; mac_n2_b <= 10'd10;
                            mac_d2_a <= 10'd4; mac_d2_b <= 10'd14;
                        end
                        2'd1: begin
                            // Perturb n2 to force mismatch.
                            mac_a <= 10'd3; mac_b <= 10'd5;
                            mac_c <= 10'd2; mac_d <= 10'd7;
                            mac_n2_a <= 10'd6; mac_n2_b <= 10'd11;
                            mac_d2_a <= 10'd4; mac_d2_b <= 10'd14;
                        end
                        default: begin
                            // d1=(1+100phi) has norm zero mod 521.
                            mac_a <= 10'd3; mac_b <= 10'd5;
                            mac_c <= 10'd1; mac_d <= 10'd100;
                            mac_n2_a <= 10'd6; mac_n2_b <= 10'd10;
                            mac_d2_a <= 10'd4; mac_d2_b <= 10'd14;
                        end
                    endcase
                    mac_start <= 1'b1;
                    test_state <= S_WAIT;
                end

                S_WAIT: begin
                    if (mac_done || mac_error) begin
                        result_shift <= {result_shift[6:0],
                                         result_shift[7] ^ mac_phslk_coherent ^
                                         mac_phslk_zero_divisor ^ mac_error};
                        if (!result_ok) begin
                            all_pass <= 1'b0;
                            test_state <= S_FAIL;
                        end else if (test_idx == 2'd2) begin
                            functional_done <= 1'b1;
                            test_state <= S_PASS;
                        end else begin
                            test_idx <= test_idx + 1'b1;
                            test_state <= S_LOAD;
                        end
                    end
                end

                S_PASS: begin
                    test_state <= S_DYNAMIC;
                end

                S_DYNAMIC: begin
                    mac_opcode <= 3'd4;
                    mac_a <= {1'b0, lfsr[8:0]};
                    mac_b <= {1'b0, lfsr[9:1]};
                    mac_c <= {1'b0, lfsr[10:2]};
                    mac_d <= {1'b0, lfsr[11:3]};
                    mac_n2_a <= {1'b0, lfsr[12:4]};
                    mac_n2_b <= {1'b0, lfsr[13:5]};
                    mac_d2_a <= {1'b0, lfsr[14:6]};
                    mac_d2_b <= {1'b0, lfsr[15:7]};
                    mac_start <= 1'b1;
                    test_state <= S_DYNAMIC_WAIT;
                end

                S_DYNAMIC_WAIT: begin
                    if (mac_done || mac_error) begin
                        result_shift <= result_shift ^ mac_res_a[7:0] ^
                                        {6'd0, mac_phslk_zero_divisor,
                                         mac_phslk_coherent} ^
                                        {7'd0, mac_error};
                        lfsr <= {lfsr[14:0],
                                 lfsr[15] ^ lfsr[13] ^ lfsr[12] ^ lfsr[10]};
                        test_state <= S_DYNAMIC;
                    end
                end

                S_FAIL: ;
                default: test_state <= S_FAIL;
            endcase
        end
    end

    reg [25:0] blink_cnt = 0;
    always @(posedge sys_clk) blink_cnt <= blink_cnt + 1'b1;

    assign led[0] = ~(blink_cnt[24] ^ result_shift[0]);
    assign led[1] = ~(functional_done && all_pass);
    assign led[2] = ~(test_state == S_FAIL);

    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits = 0;
    reg [15:0] baud_cnt = 0;
    reg        tx_busy = 0;
    reg [7:0]  tx_byte = 0;
    reg        tx_go = 0;
    reg [27:0] line_timer = 0;
    reg        start_ready = 0;
    reg [27:0] start_cnt = 0;
    reg [3:0]  msg_idx = 0;
    reg        line_active = 0;

    assign uart_tx = tx_shift[0];

    function [7:0] msg_byte;
        input [3:0] idx;
        begin
            case (idx)
                4'd0: msg_byte = "P";
                4'd1: msg_byte = "H";
                4'd2: msg_byte = "S";
                4'd3: msg_byte = "L";
                4'd4: msg_byte = "K";
                4'd5: msg_byte = ":";
                4'd6: msg_byte = (functional_done && all_pass) ? "P" :
                                  (test_state == S_FAIL) ? "F" : ".";
                4'd7: msg_byte = 8'h0D;
                4'd8: msg_byte = 8'h0A;
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
                if (baud_cnt < CLKS_PER_BIT - 1) baud_cnt <= baud_cnt + 1'b1;
                else begin
                    baud_cnt <= 0;
                    tx_shift <= {1'b1, tx_shift[9:1]};
                    if (tx_bits == 1) begin tx_busy <= 0; tx_bits <= 0; end
                    else tx_bits <= tx_bits - 1'b1;
                end
            end else if (tx_go) begin
                tx_go <= 0;
                tx_shift <= {1'b1, tx_byte, 1'b0};
                tx_bits <= 10; tx_busy <= 1'b1;
                baud_cnt <= 0;
            end else if (!start_ready) begin
                if (start_cnt < CLK_FREQ/2 - 1) start_cnt <= start_cnt + 1'b1;
                else start_ready <= 1'b1;
            end else if (line_active) begin
                tx_byte <= msg_byte(msg_idx);
                tx_go <= 1'b1;
                if (msg_idx == 4'd8) begin
                    msg_idx <= 0;
                    line_active <= 1'b0;
                end else begin
                    msg_idx <= msg_idx + 1'b1;
                end
            end else if (line_timer < CLK_FREQ/5 - 1) begin
                line_timer <= line_timer + 1'b1;
            end else begin
                line_timer <= 0;
                msg_idx <= 0;
                line_active <= 1'b1;
            end
        end
    end

endmodule
