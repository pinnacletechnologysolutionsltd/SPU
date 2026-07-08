// spu13_tang25k_spu4_probe.v — Tang 25K standalone SPU-4 silicon probe.
//
// Loads QROT test program, runs it, verifies ALU output,
// emits status over UART at 115200 baud.
//
// UART protocol (36-char status line, repeats every LINE_PERIOD):
//   SPU4:. A=xxxx B=xxxx C=xxxx D=xxxx\r\n   — still running
//   SPU4:P A=0000 B=0155 C=0155 D=0155\r\n   — PASS
//   SPU4:F A=xxxx B=xxxx C=xxxx D=xxxx\r\n   — FAIL
//
// Rewritten 2026-07-08 after first silicon attempt: the original had a
// multi-driven tx_active/tx_byte/tx_bit (message pump and bit engine in
// separate always blocks — never transmitted), held `run` high forever
// (sequencer restarts the program endlessly, busy never settles), and
// could sample busy-stable-low before execution began.  UART engine now
// mirrors the silicon-proven SOM probe pattern.

module spu13_tang25k_spu4_probe #(
    parameter CLK_FREQ     = 50000000,
    parameter CLKS_PER_BIT = 434,             // 115200 baud at 50 MHz
    parameter START_DELAY  = 50000000 / 2,
    parameter LINE_PERIOD  = 50000000 / 5
) (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx
);

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
        end else begin
            run <= 1'b0;                     // run is a 1-cycle pulse
            if (!prog_done) begin
                pi <= pi + 1;
                case (pi)
                    0: begin prog_addr <= 0; prog_data <= 24'h45_00_00; prog_we <= 1; end
                    1: begin prog_addr <= 1; prog_data <= 24'h01_00_00; prog_we <= 1; end
                    2: begin prog_we <= 0; run <= 1; prog_done <= 1; end
                endcase
            end
        end
    end

    // ── Busy stable-low detector (NBA-safe, armed by first busy) ─────
    // saw_busy prevents sampling "stable low" in the gap between the
    // run pulse and the sequencer actually raising busy.
    reg busy_d1, saw_busy;
    always @(posedge sys_clk) begin
        busy_d1 <= busy;
        if (!rst_n) saw_busy <= 1'b0;
        else if (busy) saw_busy <= 1'b1;
    end
    wire busy_stable_low = saw_busy && !busy && !busy_d1;

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

    // ── UART + status line (single-owner engine, SOM-probe pattern) ──
    // One always block owns all tx_* registers.  A 36-char status line
    // repeats every LINE_PERIOD; verdict char is '.' until the test FSM
    // concludes, then 'P' or 'F'.
    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits = 4'd0;
    reg [15:0] baud_cnt = 16'd0;
    reg        tx_busy = 1'b0;
    reg [7:0]  tx_byte = 8'd0;
    reg        tx_go = 1'b0;
    reg [27:0] line_timer = 28'd0;
    reg [27:0] start_cnt = 28'd0;
    reg        start_ready = 1'b0;
    reg [5:0]  msg_idx = 6'd0;
    reg        line_active = 1'b0;

    assign uart_tx = tx_shift[0];

    function [7:0] h;
        input [3:0] n;
        begin h = (n < 10) ? ("0" + n) : ("A" + n - 10); end
    endfunction

    function [7:0] msg_byte;
        input [5:0] idx;
        reg [7:0] status_ch;
        begin
            status_ch = (test_state == S_PASS) ? "P" :
                        (test_state == S_FAIL) ? "F" : ".";
            case (idx)
                6'd0:  msg_byte = "S";
                6'd1:  msg_byte = "P";
                6'd2:  msg_byte = "U";
                6'd3:  msg_byte = "4";
                6'd4:  msg_byte = ":";
                6'd5:  msg_byte = status_ch;
                6'd6:  msg_byte = " ";
                6'd7:  msg_byte = "A";
                6'd8:  msg_byte = "=";
                6'd9:  msg_byte = h(A_out[15:12]);
                6'd10: msg_byte = h(A_out[11:8]);
                6'd11: msg_byte = h(A_out[7:4]);
                6'd12: msg_byte = h(A_out[3:0]);
                6'd13: msg_byte = " ";
                6'd14: msg_byte = "B";
                6'd15: msg_byte = "=";
                6'd16: msg_byte = h(B_out[15:12]);
                6'd17: msg_byte = h(B_out[11:8]);
                6'd18: msg_byte = h(B_out[7:4]);
                6'd19: msg_byte = h(B_out[3:0]);
                6'd20: msg_byte = " ";
                6'd21: msg_byte = "C";
                6'd22: msg_byte = "=";
                6'd23: msg_byte = h(C_out[15:12]);
                6'd24: msg_byte = h(C_out[11:8]);
                6'd25: msg_byte = h(C_out[7:4]);
                6'd26: msg_byte = h(C_out[3:0]);
                6'd27: msg_byte = " ";
                6'd28: msg_byte = "D";
                6'd29: msg_byte = "=";
                6'd30: msg_byte = h(D_out[15:12]);
                6'd31: msg_byte = h(D_out[11:8]);
                6'd32: msg_byte = h(D_out[7:4]);
                6'd33: msg_byte = h(D_out[3:0]);
                6'd34: msg_byte = 8'h0D;
                6'd35: msg_byte = 8'h0A;
                default: msg_byte = 8'h20;
            endcase
        end
    endfunction

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            tx_shift <= 10'h3FF; tx_bits <= 4'd0; baud_cnt <= 16'd0;
            tx_busy <= 1'b0; tx_byte <= 8'd0; tx_go <= 1'b0;
            line_timer <= 28'd0; start_cnt <= 28'd0; start_ready <= 1'b0;
            msg_idx <= 6'd0; line_active <= 1'b0;
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
                if (msg_idx == 6'd35) begin
                    msg_idx <= 6'd0;
                    line_active <= 1'b0;
                end else begin
                    msg_idx <= msg_idx + 1'b1;
                end
            end else if (line_timer < LINE_PERIOD - 1) begin
                line_timer <= line_timer + 1'b1;
            end else begin
                line_timer <= 28'd0;
                msg_idx <= 6'd0;
                line_active <= 1'b1;
            end
        end
    end

    // ── LEDs ─────────────────────────────────────────────────────────
    reg [24:0] blink;
    always @(posedge sys_clk) blink <= blink + 1;
    assign led[0] = ~blink[24];
    assign led[1] = ~(test_state == S_PASS);
    assign led[2] = ~(test_state == S_FAIL);

endmodule
