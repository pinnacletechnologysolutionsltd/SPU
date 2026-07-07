// spu13_tang25k_spu4_probe.v — Tang 25K standalone SPU-4 silicon probe.
//
// Loads QROT test program, runs it, verifies ALU output,
// emits status over UART at 115200 baud.
//
// UART protocol:
//   SPU4:START\r\n           — sent on boot
//   SPU4:P B=0155 C=0155 D=0155 \r\n  — PASS
//   SPU4:F A=XXXX B=XXXX C=XXXX D=XXXX \r\n  — FAIL

module spu13_tang25k_spu4_probe (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx
);
    localparam CLK_FREQ = 50000000;
    localparam CLKS_PER_BIT = 434;

    // ── Reset ────────────────────────────────────────────────────────
    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) begin
        if (!rst_n) rst_cnt <= rst_cnt + 1;
    end

    // ── SPU-4 standalone ─────────────────────────────────────────────
    reg         prog_we;
    reg [5:0]   prog_addr;
    reg [23:0]  prog_data;
    reg         run;
    wire        busy;
    wire [15:0] A_out, B_out, C_out, D_out;
    wire [7:0]  debug;

    spu4_standalone_top #(.MEM_DEPTH(64), .ADDR_W(6)) u_spu4 (
        .clk(sys_clk), .rst_n(rst_n),
        .prog_we(prog_we), .prog_addr(prog_addr), .prog_data(prog_data),
        .run(run), .busy(busy), .done(),
        .sentinel_mode(1'b0), .piranha_pulse(1'b0),
        .A_in(16'h0), .B_in(16'h0100), .C_in(16'h0100), .D_in(16'h0100),
        .F(16'h0050), .G(16'h00B5), .H(16'h0050),
        .A_out(A_out), .B_out(B_out), .C_out(C_out), .D_out(D_out),
        .henosis_pulse(), .uart_tx(), .debug_status(debug)
    );

    // ── Program sequencer: QROT + HALT ──────────────────────────────
    reg prog_done;
    reg [5:0] pi;
    always @(posedge sys_clk) begin
        if (!rst_n) begin
            prog_we <= 0; prog_addr <= 0; prog_data <= 0;
            run <= 0; prog_done <= 0; pi <= 0;
        end else if (!prog_done) begin
            pi <= pi + 1;
            case (pi)
                0: begin prog_addr <= 0; prog_data <= 24'h45_00_00; prog_we <= 1; end
                1: begin prog_addr <= 1; prog_data <= 24'h01_00_00; prog_we <= 1; end
                2: begin prog_we <= 0; prog_done <= 1; run <= 1; end
                default: run <= 0;
            endcase
        end
    end

    // ── Busy stable-low detector (NBA-safe) ─────────────────────────
    reg busy_d1;
    always @(posedge sys_clk) busy_d1 <= busy;
    wire busy_stable_low = !busy && !busy_d1;  // busy low for 2+ cycles

    // ── Test FSM ─────────────────────────────────────────────────────
    localparam S_RESET = 4'd0, S_WAIT = 4'd1, S_CHECK = 4'd2;
    localparam S_PASS = 4'd3, S_FAIL = 4'd4;

    reg [3:0] test_state = S_RESET;
    reg [31:0] timeout;

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            test_state <= S_RESET; timeout <= 0;
        end else begin
            case (test_state)
                S_RESET: if (prog_done) test_state <= S_WAIT;
                S_WAIT: begin
                    if (busy_stable_low) test_state <= S_CHECK;
                    else if (timeout > 10000000) test_state <= S_FAIL;  // 200ms
                    else timeout <= timeout + 1;
                end
                S_CHECK: begin
                    if (B_out == 16'h0155 && C_out == 16'h0155 && D_out == 16'h0155)
                        test_state <= S_PASS;
                    else
                        test_state <= S_FAIL;
                end
            endcase
        end
    end

    // ── UART (bit-banged 115200 baud) ────────────────────────────────
    reg [15:0] uart_baud;
    wire uart_tick = (uart_baud == CLKS_PER_BIT - 1);
    reg tx_active;
    reg [7:0] tx_byte;
    reg [3:0] tx_bit;
    reg [31:0] tx_shift;

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            uart_baud <= 0; tx_active <= 0; tx_bit <= 0; tx_shift <= 32'hFFFFFFFF;
        end else begin
            if (uart_tick) uart_baud <= 0; else uart_baud <= uart_baud + 1;
            if (!tx_active) begin
                tx_shift[0] <= 1'b1;
            end else if (uart_tick) begin
                if (tx_bit == 0) begin tx_shift[0] <= 1'b0; tx_bit <= 1; end
                else if (tx_bit <= 8) begin
                    tx_shift[0] <= tx_byte[0];
                    tx_byte <= {1'b0, tx_byte[7:1]};
                    tx_bit <= tx_bit + 1;
                end else if (tx_bit == 9) begin tx_shift[0] <= 1'b1; tx_bit <= 10; end
                else tx_active <= 0;
            end
        end
    end
    assign uart_tx = tx_shift[0];

    // ── Message system ───────────────────────────────────────────────
    reg [5:0] msg_idx;
    reg [7:0] msg_buf [0:47];
    wire msg_idle = (msg_idx == 0 && !tx_active);

    function [7:0] h;
        input [3:0] n;
        begin h = (n < 10) ? ("0" + n) : ("A" + n - 10); end
    endfunction

    // Boot message flag: sent once shortly after reset
    reg boot_msg_sent;
    always @(posedge sys_clk) begin
        if (!rst_n) boot_msg_sent <= 0;
        else if (msg_idle && !boot_msg_sent) boot_msg_sent <= 1;
    end

    always @(posedge sys_clk) begin
        if (!rst_n) msg_idx <= 0;
        else if (msg_idle) begin
            if (!boot_msg_sent) begin
                // Send boot message
                msg_buf[0] <= "S"; msg_buf[1] <= "P"; msg_buf[2] <= "U";
                msg_buf[3] <= "4"; msg_buf[4] <= ":"; msg_buf[5] <= "S";
                msg_buf[6] <= "T"; msg_buf[7] <= "A"; msg_buf[8] <= "R";
                msg_buf[9] <= "T"; msg_buf[10] <= 8'h0D; msg_buf[11] <= 8'h0A;
                msg_idx <= 12;
            end else if (test_state == S_PASS) begin
                msg_buf[0] <= "S"; msg_buf[1] <= "P"; msg_buf[2] <= "U";
                msg_buf[3] <= "4"; msg_buf[4] <= ":"; msg_buf[5] <= "P";
                msg_buf[6] <= " "; msg_buf[7] <= "B"; msg_buf[8] <= "=";
                msg_buf[9] <= h(B_out[15:12]); msg_buf[10] <= h(B_out[11:8]);
                msg_buf[11] <= h(B_out[7:4]);  msg_buf[12] <= h(B_out[3:0]);
                msg_buf[13] <= " "; msg_buf[14] <= "C"; msg_buf[15] <= "=";
                msg_buf[16] <= h(C_out[15:12]); msg_buf[17] <= h(C_out[11:8]);
                msg_buf[18] <= h(C_out[7:4]);  msg_buf[19] <= h(C_out[3:0]);
                msg_buf[20] <= " "; msg_buf[21] <= "D"; msg_buf[22] <= "=";
                msg_buf[23] <= h(D_out[15:12]); msg_buf[24] <= h(D_out[11:8]);
                msg_buf[25] <= h(D_out[7:4]);  msg_buf[26] <= h(D_out[3:0]);
                msg_buf[27] <= " "; msg_buf[28] <= "P"; msg_buf[29] <= "A";
                msg_buf[30] <= "S"; msg_buf[31] <= "S";
                msg_buf[32] <= 8'h0D; msg_buf[33] <= 8'h0A;
                msg_idx <= 34;
            end else if (test_state == S_FAIL) begin
                msg_buf[0] <= "S"; msg_buf[1] <= "P"; msg_buf[2] <= "U";
                msg_buf[3] <= "4"; msg_buf[4] <= ":"; msg_buf[5] <= "F";
                msg_buf[6] <= " "; msg_buf[7] <= "A"; msg_buf[8] <= "=";
                msg_buf[9] <= h(A_out[15:12]); msg_buf[10] <= h(A_out[11:8]);
                msg_buf[11] <= h(A_out[7:4]);  msg_buf[12] <= h(A_out[3:0]);
                msg_buf[13] <= " "; msg_buf[14] <= "B"; msg_buf[15] <= "=";
                msg_buf[16] <= h(B_out[15:12]); msg_buf[17] <= h(B_out[11:8]);
                msg_buf[18] <= h(B_out[7:4]);  msg_buf[19] <= h(B_out[3:0]);
                msg_buf[20] <= " "; msg_buf[21] <= "C"; msg_buf[22] <= "=";
                msg_buf[23] <= h(C_out[15:12]); msg_buf[24] <= h(C_out[11:8]);
                msg_buf[25] <= h(C_out[7:4]);  msg_buf[26] <= h(C_out[3:0]);
                msg_buf[27] <= " "; msg_buf[28] <= "D"; msg_buf[29] <= "=";
                msg_buf[30] <= h(D_out[15:12]); msg_buf[31] <= h(D_out[11:8]);
                msg_buf[32] <= h(D_out[7:4]);  msg_buf[33] <= h(D_out[3:0]);
                msg_buf[35] <= "F"; msg_buf[36] <= "A";
                msg_buf[37] <= "I"; msg_buf[38] <= "L";
                msg_buf[39] <= 8'h0D; msg_buf[40] <= 8'h0A;
                msg_idx <= 41;
            end
        end else if (!tx_active && msg_idx > 0) begin
            tx_active <= 1; tx_byte <= msg_buf[0]; tx_bit <= 0;
            msg_idx <= msg_idx - 1;
            for (integer i = 0; i < 47; i = i + 1) msg_buf[i] <= msg_buf[i+1];
        end
    end

    // ── LEDs ─────────────────────────────────────────────────────────
    reg [24:0] blink;
    always @(posedge sys_clk) blink <= blink + 1;
    assign led[0] = ~blink[24];
    assign led[1] = ~(test_state == S_PASS);
    assign led[2] = ~(test_state == S_FAIL);

endmodule
