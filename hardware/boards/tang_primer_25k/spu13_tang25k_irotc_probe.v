// spu13_tang25k_irotc_probe.v — IROTC Engine Tang 25K Probe
// Uses proven Lucas MAC probe UART pattern. Self-checking FSM drives the
// term-serial IROTC engine through golden vectors + fault matrix.

module spu13_tang25k_irotc_probe #(
    // Parameter (not localparam) so the testbench can shrink the boot
    // and line-gap waits and decode the real UART line in simulation;
    // hardware builds use the default (0.5 s settle at 50 MHz).
    parameter CLK_FREQ = 50000000
) (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx
);
    localparam W = 32;
    localparam CLKS_PER_BIT = 434;

    localparam [1:0] TAG_UNTAGGED = 2'd0;
    localparam [1:0] TAG_FRESH    = 2'd1;
    localparam [1:0] TAG_MAIN     = 2'd2;
    localparam [1:0] TAG_CONJ     = 2'd3;

    // ── Reset ───────────────────────────────────────────────────────
    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) if (!rst_n) rst_cnt <= rst_cnt + 1;

    // ── IROTC Engine ────────────────────────────────────────────────
    reg                 eng_start = 0;
    reg  [6:0]          eng_sel;
    reg  [1:0]          eng_src_tag;
    reg  signed [W-1:0] eng_in_b_a, eng_in_b_b;
    reg  signed [W-1:0] eng_in_c_a, eng_in_c_b;
    reg  signed [W-1:0] eng_in_d_a, eng_in_d_b;
    wire                eng_busy, eng_done, eng_fault;
    wire [1:0]          eng_fault_code, eng_out_tag;
    wire signed [W-1:0] eng_out_a_a, eng_out_a_b;
    wire signed [W-1:0] eng_out_b_a, eng_out_b_b;
    wire signed [W-1:0] eng_out_c_a, eng_out_c_b;
    wire signed [W-1:0] eng_out_d_a, eng_out_d_b;

    spu13_irotc_engine #(.W(W)) u_engine (
        .clk(sys_clk), .rst_n(rst_n),
        .start(eng_start), .sel(eng_sel), .src_tag(eng_src_tag),
        .in_b_a(eng_in_b_a), .in_b_b(eng_in_b_b),
        .in_c_a(eng_in_c_a), .in_c_b(eng_in_c_b),
        .in_d_a(eng_in_d_a), .in_d_b(eng_in_d_b),
        .busy(eng_busy), .done(eng_done), .fault(eng_fault),
        .fault_code(eng_fault_code), .out_tag(eng_out_tag),
        .out_a_a(eng_out_a_a), .out_a_b(eng_out_a_b),
        .out_b_a(eng_out_b_a), .out_b_b(eng_out_b_b),
        .out_c_a(eng_out_c_a), .out_c_b(eng_out_c_b),
        .out_d_a(eng_out_d_a), .out_d_b(eng_out_d_b)
    );

    // ── Golden values (oracle-verified, 2026-07-10) ────────────────
    wire signed [W-1:0] G16_B_A = 12, G16_B_B = 10;
    wire signed [W-1:0] G16_C_A = -4, G16_C_B = 8;
    wire signed [W-1:0] G16_D_A = 10, G16_D_B = 0;
    wire signed [W-1:0] G16_EXP_BA = -18, G16_EXP_BB = -18;
    wire signed [W-1:0] G16_EXP_CA = -4,  G16_EXP_CB = 8;

    wire signed [W-1:0] G36_B_A = -8, G36_B_B = -16;
    wire signed [W-1:0] G36_C_A = 6,  G36_C_B = 0;
    wire signed [W-1:0] G36_D_A = -8, G36_D_B = 10;
    wire signed [W-1:0] G36_EXP_BA = 0,   G36_EXP_BB = -12;
    wire signed [W-1:0] G36_EXP_CA = -4,  G36_EXP_CB = 10;

    // ── Test sequencer ─────────────────────────────────────────────
    localparam [3:0] S_RESET  = 4'd0;
    localparam [3:0] S_P3     = 4'd1;   // idx 16 main (period-3)
    localparam [3:0] S_P5     = 4'd2;   // idx 36 main (period-5)
    localparam [3:0] S_FAULT_BADIDX   = 4'd3;
    localparam [3:0] S_FAULT_UNTAGGED = 4'd4;
    localparam [3:0] S_FAULT_CATMIX   = 4'd5;
    localparam [3:0] S_PASS   = 4'd14;
    localparam [3:0] S_FAIL   = 4'd15;

    reg [3:0]  test_state = S_RESET;
    reg [1:0]  test_sub = 0;
    reg [7:0]  err_code = 0;
    reg [15:0] watchdog = 0;  // timeout if engine stuck
    reg signed [W-1:0] exp_ba, exp_bb, exp_ca, exp_cb;
    reg [1:0]  exp_tag;

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            test_state <= S_RESET;
            test_sub <= 0; err_code <= 0; watchdog <= 0;
            eng_start <= 0;
        end else begin
            // Pulse eng_start for exactly 1 cycle
            eng_start <= 0;
            if (!eng_busy) begin
            watchdog <= 0;
            case (test_state)
                S_RESET: begin
                    if (rst_cnt == 8'hFF) test_state <= S_P3;
                end
                S_P3: begin  // idx 16: 120deg period-3
                    if (test_sub == 0) begin
                        eng_sel <= 7'd16; eng_src_tag <= TAG_FRESH;
                        eng_in_b_a <= G16_B_A; eng_in_b_b <= G16_B_B;
                        eng_in_c_a <= G16_C_A; eng_in_c_b <= G16_C_B;
                        eng_in_d_a <= G16_D_A; eng_in_d_b <= G16_D_B;
                        exp_ba <= G16_EXP_BA; exp_bb <= G16_EXP_BB;
                        exp_ca <= G16_EXP_CA; exp_cb <= G16_EXP_CB;
                        exp_tag <= TAG_MAIN;
                        eng_start <= 1; test_sub <= 1;
                    end else if (eng_done) begin
                        if (eng_out_b_a == exp_ba && eng_out_b_b == exp_bb &&
                            eng_out_c_a == exp_ca && eng_out_c_b == exp_cb &&
                            eng_out_tag == exp_tag && !eng_fault)
                            test_state <= S_P5;
                        else begin test_state <= S_FAIL; err_code <= 1; end
                        test_sub <= 0;
                    end else if (eng_fault) begin
                        test_state <= S_FAIL; err_code <= 2; test_sub <= 0;
                    end
                end
                S_P5: begin  // idx 36: 72deg period-5
                    if (test_sub == 0) begin
                        eng_sel <= 7'd36; eng_src_tag <= TAG_FRESH;
                        eng_in_b_a <= G36_B_A; eng_in_b_b <= G36_B_B;
                        eng_in_c_a <= G36_C_A; eng_in_c_b <= G36_C_B;
                        eng_in_d_a <= G36_D_A; eng_in_d_b <= G36_D_B;
                        exp_ba <= G36_EXP_BA; exp_bb <= G36_EXP_BB;
                        exp_ca <= G36_EXP_CA; exp_cb <= G36_EXP_CB;
                        exp_tag <= TAG_MAIN;
                        eng_start <= 1; test_sub <= 1;
                    end else if (eng_done) begin
                        if (eng_out_b_a == exp_ba && eng_out_b_b == exp_bb &&
                            eng_out_c_a == exp_ca && eng_out_c_b == exp_cb &&
                            eng_out_tag == exp_tag && !eng_fault)
                            test_state <= S_FAULT_BADIDX;
                        else begin test_state <= S_FAIL; err_code <= 3; end
                        test_sub <= 0;
                    end else if (eng_fault) begin
                        test_state <= S_FAIL; err_code <= 4; test_sub <= 0;
                    end
                end
                S_FAULT_BADIDX: begin  // idx 60 -> BADIDX
                    if (test_sub == 0) begin
                        eng_sel <= 7'd60; eng_src_tag <= TAG_FRESH;
                        eng_in_b_a <= 2; eng_in_b_b <= 0;
                        eng_in_c_a <= 4; eng_in_c_b <= 0;
                        eng_in_d_a <= -6; eng_in_d_b <= 0;
                        eng_start <= 1; test_sub <= 1;
                    end else if (eng_fault && eng_fault_code == 2'd1) begin
                        test_state <= S_FAULT_UNTAGGED; test_sub <= 0;
                    end else if (eng_done) begin
                        test_state <= S_FAIL; err_code <= 5; test_sub <= 0;
                    end
                end
                S_FAULT_UNTAGGED: begin
                    if (test_sub == 0) begin
                        eng_sel <= 7'd0; eng_src_tag <= TAG_UNTAGGED;
                        eng_in_b_a <= 2; eng_in_b_b <= 0;
                        eng_in_c_a <= 4; eng_in_c_b <= 0;
                        eng_in_d_a <= -6; eng_in_d_b <= 0;
                        eng_start <= 1; test_sub <= 1;
                    end else if (eng_fault && eng_fault_code == 2'd2) begin
                        test_state <= S_FAULT_CATMIX; test_sub <= 0;
                    end else if (eng_done) begin
                        test_state <= S_FAIL; err_code <= 6; test_sub <= 0;
                    end
                end
                S_FAULT_CATMIX: begin  // MAIN src, conj sel -> CATMIX
                    if (test_sub == 0) begin
                        eng_sel <= 7'h40; eng_src_tag <= TAG_MAIN;
                        eng_in_b_a <= G16_B_A; eng_in_b_b <= G16_B_B;
                        eng_in_c_a <= G16_C_A; eng_in_c_b <= G16_C_B;
                        eng_in_d_a <= G16_D_A; eng_in_d_b <= G16_D_B;
                        eng_start <= 1; test_sub <= 1;
                    end else if (eng_fault && eng_fault_code == 2'd3) begin
                        test_state <= S_PASS; test_sub <= 0;
                    end else if (eng_done) begin
                        test_state <= S_FAIL; err_code <= 7; test_sub <= 0;
                    end
                end
                S_PASS: ;
                S_FAIL: ;
            endcase
            end else begin
                // Watchdog: if engine stays busy too long, force FAIL
                if (watchdog < 16'hFFFF) watchdog <= watchdog + 1;
                else begin test_state <= S_FAIL; err_code <= 8'hFF; end
            end
        end
    end

    // ── LEDs ───────────────────────────────────────────────────────
    // Diagnostic: LED[0]=heartbeat, LED[1]=engine busy, LED[2]=FSM running
    reg [25:0] blink_cnt = 0;
    always @(posedge sys_clk) blink_cnt <= blink_cnt + 1;
    assign led[0] = ~blink_cnt[24];
    assign led[1] = ~eng_busy;                              // OFF when engine busy
    assign led[2] = ~(test_state == S_PASS ||
                      test_state == S_FAIL);                // ON while testing

    // ── UART (Lucas probe pattern, verbatim) ───────────────────────
    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits = 0;
    reg [15:0] baud_cnt = 0;
    reg        tx_busy = 0;
    reg        tx_go = 0;
    reg [7:0]  tx_byte = 0;
    reg [27:0] start_cnt = 0;
    reg        start_ready = 0;
    reg [3:0]  msg_idx = 0;
    reg        line_active = 0;
    reg [27:0] line_timer = 0;
    reg        line_sent = 0;

    assign uart_tx = tx_shift[0];

    function [7:0] hex2ascii;
        input [3:0] h;
        begin hex2ascii = (h < 10) ? (8'h30 + h) : (8'h37 + h); end
    endfunction

    function [7:0] msg_byte;
        input [3:0] idx;
        begin
            case (idx)
                4'd0:  msg_byte = "I";
                4'd1:  msg_byte = "R";
                4'd2:  msg_byte = "O";
                4'd3:  msg_byte = "T";
                4'd4:  msg_byte = "C";
                4'd5:  msg_byte = ":";
                4'd6:  msg_byte = (test_state == S_PASS) ? "P" :
                                  (test_state == S_FAIL) ? "F" : ".";
                4'd7:  msg_byte = " ";
                4'd8:  msg_byte = "E";
                4'd9:  msg_byte = "=";
                4'd10: msg_byte = hex2ascii(err_code[7:4]);
                4'd11: msg_byte = hex2ascii(err_code[3:0]);
                4'd12: msg_byte = 8'h0D;
                4'd13: msg_byte = 8'h0A;
                default: msg_byte = 8'h20;
            endcase
        end
    endfunction

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            tx_shift <= 10'h3FF; tx_bits <= 0; baud_cnt <= 0;
            tx_busy <= 0; tx_go <= 0; start_ready <= 0;
            start_cnt <= 0; line_timer <= 0; msg_idx <= 0; line_active <= 0;
            line_sent <= 0;
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
                if (msg_idx == 4'd13) begin
                    msg_idx <= 0; line_active <= 0;
                end else begin
                    msg_idx <= msg_idx + 1'b1;
                end
            end else if (line_timer < CLK_FREQ/5 - 1) begin
                line_timer <= line_timer + 1;
            end else if (!line_sent &&
                       (test_state == S_PASS || test_state == S_FAIL)) begin
                line_active <= 1; msg_idx <= 0; line_timer <= 0;
                line_sent <= 1;
            end
        end
    end
endmodule
