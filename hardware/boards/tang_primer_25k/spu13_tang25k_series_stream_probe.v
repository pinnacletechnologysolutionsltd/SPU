// spu13_tang25k_series_stream_probe.v — Tang 25K series-stream silicon probe.
//
// Walks ALL golden vectors from the committed .mem (BRAM-initialized ROM,
// same file the testbench uses), runs each through spu13_series_stream, and
// self-checks roots, err_singular, and the exact resource counts
// (26 shared-mult launches + 1 tower per normal vector; 0 + 1 on singular).
//
// Shared-resource proof: ONE spu13_m31_multiplier serves both the Fp4
// tower and the series stream through a busy-selected mux — the tower and
// the stream never multiply in the same cycle by construction.
//
// ROM discipline: single synchronous read port (gv_q), one sequential
// address pointer walking flag → 36 inputs → 12 expected words per vector,
// so the 393-word ROM maps to BSRAM instead of distributed LUTs.
//
// UART at 115200 (22-char status line, repeats):
//   SSTR:. V=0 M=00 E=00   — running
//   SSTR:P V=8 M=1A E=00   — PASS (8 vectors, last normal used 0x1A=26 mults)
//   SSTR:F V=<n> M=<mm> E=<code>  — FAIL
// Fail codes: B0+v root mismatch, C0+v resource counts, D0+v flag/err.

module spu13_tang25k_series_stream_probe #(
    parameter CLK_FREQ     = 50000000,
    parameter CLKS_PER_BIT = 434,
    parameter START_DELAY  = 50000000 / 2,
    parameter LINE_PERIOD  = 50000000 / 5
) (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx
);

    // ── Reset ────────────────────────────────────────────────────────
    reg [7:0] rst_cnt = 8'd0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) begin
        if (!rst_n) rst_cnt <= rst_cnt + 1'b1;
    end

    // ── Golden vector ROM (committed .mem, shared with the tb) ───────
    reg [31:0] gv [0:392];
    initial $readmemh("hardware/tests/spu13/spu13_series_stream_golden.mem", gv);

    reg [8:0]  raddr;
    reg [31:0] gv_q;
    always @(posedge sys_clk) gv_q <= gv[raddr];

    // ── Vector staging: 36 input words; expected compared streaming ──
    // Loaded as a shift register (constant indices → plain FFs, not
    // distributed RAM — PnR ran out of RAM16SDP4 BELs on the array form).
    // After 36 shifts, the FIRST word (c0_o0_z0) sits in vin[35].
    reg [31:0] vin [0:35];
    reg        vflag;
    integer    k;

    // ── DUT wiring ────────────────────────────────────────────────────
    reg  dut_start;
    wire [31:0] x_o0_z0, x_o0_z1, x_o0_z2, x_o0_z3;
    wire [31:0] x_o1_z0, x_o1_z1, x_o1_z2, x_o1_z3;
    wire [31:0] x_o2_z0, x_o2_z1, x_o2_z2, x_o2_z3;
    wire dut_done, dut_err, dut_busy;

    wire        inv_start_w;
    wire [31:0] inv_z0, inv_z1, inv_z2, inv_z3;
    wire [31:0] inv_r0, inv_r1, inv_r2, inv_r3;
    wire        inv_done_w, inv_flags_v, inv_busy_w;

    wire        t_start;
    wire [31:0] t_a0, t_a1, t_a2, t_a3, t_b0, t_b1, t_b2, t_b3;
    wire        j_start;
    wire [31:0] j_a0, j_a1, j_a2, j_a3, j_b0, j_b1, j_b2, j_b3;
    wire [31:0] m_r0, m_r1, m_r2, m_r3;
    wire        m_done, m_busy;

    // ── Shared-mult mux: tower owns the multiplier while inverting ───
    wire sel_tower = inv_start_w | inv_busy_w;
    wire        m_start = sel_tower ? t_start : j_start;
    wire [31:0] m_a0 = sel_tower ? t_a0 : j_a0;
    wire [31:0] m_a1 = sel_tower ? t_a1 : j_a1;
    wire [31:0] m_a2 = sel_tower ? t_a2 : j_a2;
    wire [31:0] m_a3 = sel_tower ? t_a3 : j_a3;
    wire [31:0] m_b0 = sel_tower ? t_b0 : j_b0;
    wire [31:0] m_b1 = sel_tower ? t_b1 : j_b1;
    wire [31:0] m_b2 = sel_tower ? t_b2 : j_b2;
    wire [31:0] m_b3 = sel_tower ? t_b3 : j_b3;

    spu13_series_stream u_dut (
        .clk(sys_clk), .rst_n(rst_n), .start(dut_start),
        // shift-register load: word k of the .mem lands in vin[35-k]
        .c0_o0_z0(vin[35]), .c0_o0_z1(vin[34]), .c0_o0_z2(vin[33]), .c0_o0_z3(vin[32]),
        .c0_o1_z0(vin[31]), .c0_o1_z1(vin[30]), .c0_o1_z2(vin[29]), .c0_o1_z3(vin[28]),
        .c0_o2_z0(vin[27]), .c0_o2_z1(vin[26]), .c0_o2_z2(vin[25]), .c0_o2_z3(vin[24]),
        .c1_o0_z0(vin[23]), .c1_o0_z1(vin[22]), .c1_o0_z2(vin[21]), .c1_o0_z3(vin[20]),
        .c1_o1_z0(vin[19]), .c1_o1_z1(vin[18]), .c1_o1_z2(vin[17]), .c1_o1_z3(vin[16]),
        .c1_o2_z0(vin[15]), .c1_o2_z1(vin[14]), .c1_o2_z2(vin[13]), .c1_o2_z3(vin[12]),
        .c2_o0_z0(vin[11]), .c2_o0_z1(vin[10]), .c2_o0_z2(vin[9]),  .c2_o0_z3(vin[8]),
        .c2_o1_z0(vin[7]),  .c2_o1_z1(vin[6]),  .c2_o1_z2(vin[5]),  .c2_o1_z3(vin[4]),
        .c2_o2_z0(vin[3]),  .c2_o2_z1(vin[2]),  .c2_o2_z2(vin[1]),  .c2_o2_z3(vin[0]),
        .x_o0_z0(x_o0_z0), .x_o0_z1(x_o0_z1), .x_o0_z2(x_o0_z2), .x_o0_z3(x_o0_z3),
        .x_o1_z0(x_o1_z0), .x_o1_z1(x_o1_z1), .x_o1_z2(x_o1_z2), .x_o1_z3(x_o1_z3),
        .x_o2_z0(x_o2_z0), .x_o2_z1(x_o2_z1), .x_o2_z2(x_o2_z2), .x_o2_z3(x_o2_z3),
        .done(dut_done), .err_singular(dut_err), .busy(dut_busy),
        .inv_start(inv_start_w),
        .inv_z0(inv_z0), .inv_z1(inv_z1), .inv_z2(inv_z2), .inv_z3(inv_z3),
        .inv_r0(inv_r0), .inv_r1(inv_r1), .inv_r2(inv_r2), .inv_r3(inv_r3),
        .inv_done(inv_done_w), .inv_flags_v(inv_flags_v),
        .mult_start(j_start),
        .mult_a0(j_a0), .mult_a1(j_a1), .mult_a2(j_a2), .mult_a3(j_a3),
        .mult_b0(j_b0), .mult_b1(j_b1), .mult_b2(j_b2), .mult_b3(j_b3),
        .mult_r0(m_r0), .mult_r1(m_r1), .mult_r2(m_r2), .mult_r3(m_r3),
        .mult_done(m_done)
    );

    spu13_fp4_inverter u_inverter (
        .clk(sys_clk), .rst_n(rst_n), .start(inv_start_w),
        .z0(inv_z0), .z1(inv_z1), .z2(inv_z2), .z3(inv_z3),
        .inv0(inv_r0), .inv1(inv_r1), .inv2(inv_r2), .inv3(inv_r3),
        .done(inv_done_w), .busy(inv_busy_w), .flags_v(inv_flags_v),
        .mult_start(t_start),
        .mult_a0(t_a0), .mult_a1(t_a1), .mult_a2(t_a2), .mult_a3(t_a3),
        .mult_b0(t_b0), .mult_b1(t_b1), .mult_b2(t_b2), .mult_b3(t_b3),
        .mult_r0(m_r0), .mult_r1(m_r1), .mult_r2(m_r2), .mult_r3(m_r3),
        .mult_done(m_done), .mult_busy(m_busy)
    );

    spu13_m31_multiplier u_mult (
        .clk(sys_clk), .rst_n(rst_n), .start(m_start),
        .a0(m_a0), .a1(m_a1), .a2(m_a2), .a3(m_a3),
        .b0(m_b0), .b1(m_b1), .b2(m_b2), .b3(m_b3),
        .r0(m_r0), .r1(m_r1), .r2(m_r2), .r3(m_r3),
        .done(m_done), .busy(m_busy), .rns_error()
    );

    // ── Resource counters (per vector, reset by dut_start) ───────────
    reg [7:0] jcnt, icnt;
    always @(posedge sys_clk) begin
        if (!rst_n) begin jcnt <= 8'd0; icnt <= 8'd0; end
        else if (dut_start) begin jcnt <= 8'd0; icnt <= 8'd0; end
        else begin
            if (j_start && !sel_tower) jcnt <= jcnt + 1'b1;
            if (inv_start_w)           icnt <= icnt + 1'b1;
        end
    end

    // ── Expected-root word mux for streaming compare ─────────────────
    function [31:0] x_word;
        input [3:0] k;
        begin
            case (k)
                4'd0:  x_word = x_o0_z0;  4'd1:  x_word = x_o0_z1;
                4'd2:  x_word = x_o0_z2;  4'd3:  x_word = x_o0_z3;
                4'd4:  x_word = x_o1_z0;  4'd5:  x_word = x_o1_z1;
                4'd6:  x_word = x_o1_z2;  4'd7:  x_word = x_o1_z3;
                4'd8:  x_word = x_o2_z0;  4'd9:  x_word = x_o2_z1;
                4'd10: x_word = x_o2_z2;  default: x_word = x_o2_z3;
            endcase
        end
    endfunction

    // ── Test FSM: two-phase ROM walk (ph0 fetch settles, ph1 consume) ─
    localparam S_HDR   = 3'd0;
    localparam S_RD    = 3'd1;
    localparam S_RUN   = 3'd2;
    localparam S_WAIT  = 3'd3;
    localparam S_CMP   = 3'd4;
    localparam S_CHECK = 3'd5;
    localparam S_PASS  = 3'd6;
    localparam S_FAIL  = 3'd7;

    reg [2:0] test_state = S_HDR;
    reg       ph;
    reg [3:0] n_vec, v, pass_cnt, kcmp;
    reg [5:0] widx;
    reg [7:0] fail_code, m_last;
    reg       cmp_bad, err_lat;

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            test_state <= S_HDR; ph <= 1'b0;
            v <= 4'd0; pass_cnt <= 4'd0; n_vec <= 4'd0; kcmp <= 4'd0;
            raddr <= 9'd0; widx <= 6'd0;
            fail_code <= 8'd0; m_last <= 8'd0;
            dut_start <= 1'b0; vflag <= 1'b0; cmp_bad <= 1'b0;
        end else begin
            dut_start <= 1'b0;
            ph <= ~ph;

            case (test_state)
                S_HDR: if (ph) begin
                    n_vec <= gv_q[3:0];
                    raddr <= raddr + 1'b1;     // → first vector's flag
                    widx <= 6'd0;
                    test_state <= S_RD;
                end

                S_RD: if (ph) begin
                    if (widx == 6'd0) vflag <= gv_q[0];
                    else begin
                        for (k = 35; k > 0; k = k - 1) vin[k] <= vin[k-1];
                        vin[0] <= gv_q;
                    end
                    raddr <= raddr + 1'b1;
                    if (widx == 6'd36) begin
                        widx <= 6'd0;
                        test_state <= S_RUN;   // raddr now at expected[0]
                    end else begin
                        widx <= widx + 1'b1;
                    end
                end

                S_RUN: begin
                    dut_start <= 1'b1;
                    cmp_bad <= 1'b0;
                    kcmp <= 4'd0;
                    test_state <= S_WAIT;
                end

                S_WAIT: if (dut_done) begin
                    err_lat <= dut_err;       // capture at done, belt-and-braces
                    ph <= 1'b0;               // realign fetch phase
                    test_state <= S_CMP;
                end

                S_CMP: if (ph) begin
                    // walk the 12 expected words; compare only on normal
                    // vectors (singular expected words are placeholders)
                    if (!vflag && gv_q !== x_word(kcmp)) cmp_bad <= 1'b1;
                    raddr <= raddr + 1'b1;
                    if (kcmp == 4'd11) test_state <= S_CHECK;
                    else kcmp <= kcmp + 1'b1;
                end

                S_CHECK: begin
                    if (vflag ? (err_lat !== 1'b1) : (err_lat !== 1'b0)) begin
                        fail_code <= 8'hD0 + {4'd0, v};
                        test_state <= S_FAIL;
                    end else if (!vflag && cmp_bad) begin
                        fail_code <= 8'hB0 + {4'd0, v};
                        test_state <= S_FAIL;
                    end else if (vflag ? (jcnt != 8'd0 || icnt != 8'd1)
                                       : (jcnt != 8'd26 || icnt != 8'd1)) begin
                        fail_code <= 8'hC0 + {4'd0, v};
                        test_state <= S_FAIL;
                    end else begin
                        if (!vflag) m_last <= jcnt;
                        pass_cnt <= pass_cnt + 1'b1;
                        if (v == n_vec - 1) test_state <= S_PASS;
                        else begin
                            v <= v + 1'b1;
                            widx <= 6'd0;
                            test_state <= S_RD;   // raddr at next flag word
                        end
                    end
                end

                S_PASS: test_state <= S_PASS;
                S_FAIL: test_state <= S_FAIL;
                default: test_state <= S_FAIL;
            endcase
        end
    end

    // ── LEDs ─────────────────────────────────────────────────────────
    reg [24:0] blink = 25'd0;
    always @(posedge sys_clk) blink <= blink + 1'b1;
    assign led[0] = ~blink[24];
    assign led[1] = ~(test_state == S_PASS);
    assign led[2] = ~(test_state == S_FAIL);

    // ── UART status line (SOM-probe pattern, single owner) ───────────
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

    function [7:0] h;
        input [3:0] n;
        begin h = (n < 10) ? ("0" + n) : ("A" + n - 10); end
    endfunction

    function [7:0] msg_byte;
        input [4:0] idx;
        reg [7:0] status_ch;
        begin
            status_ch = (test_state == S_PASS) ? "P" :
                        (test_state == S_FAIL) ? "F" : ".";
            case (idx)
                5'd0:  msg_byte = "S";
                5'd1:  msg_byte = "S";
                5'd2:  msg_byte = "T";
                5'd3:  msg_byte = "R";
                5'd4:  msg_byte = ":";
                5'd5:  msg_byte = status_ch;
                5'd6:  msg_byte = " ";
                5'd7:  msg_byte = "V";
                5'd8:  msg_byte = "=";
                5'd9:  msg_byte = h(pass_cnt);
                5'd10: msg_byte = " ";
                5'd11: msg_byte = "M";
                5'd12: msg_byte = "=";
                5'd13: msg_byte = h(m_last[7:4]);
                5'd14: msg_byte = h(m_last[3:0]);
                5'd15: msg_byte = " ";
                5'd16: msg_byte = "E";
                5'd17: msg_byte = "=";
                5'd18: msg_byte = h(fail_code[7:4]);
                5'd19: msg_byte = h(fail_code[3:0]);
                5'd20: msg_byte = 8'h0D;
                5'd21: msg_byte = 8'h0A;
                default: msg_byte = 8'h20;
            endcase
        end
    endfunction

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            tx_shift <= 10'h3FF; tx_bits <= 4'd0; baud_cnt <= 16'd0;
            tx_busy <= 1'b0; tx_byte <= 8'd0; tx_go <= 1'b0;
            line_timer <= 28'd0; start_cnt <= 28'd0; start_ready <= 1'b0;
            msg_idx <= 5'd0; line_active <= 1'b0;
        end else begin
            if (tx_busy) begin
                if (baud_cnt < CLKS_PER_BIT - 1) begin
                    baud_cnt <= baud_cnt + 1'b1;
                end else begin
                    baud_cnt <= 16'd0;
                    tx_shift <= {1'b1, tx_shift[9:1]};
                    if (tx_bits == 1) begin
                        tx_busy <= 1'b0; tx_bits <= 4'd0;
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
                if (start_cnt < START_DELAY - 1) start_cnt <= start_cnt + 1'b1;
                else start_ready <= 1'b1;
            end else if (line_active) begin
                tx_byte <= msg_byte(msg_idx);
                tx_go <= 1'b1;
                if (msg_idx == 5'd21) begin
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
