// spu_a7_j10_ident_top.v — J10 pin-identification positive control.
//
// Drives all eight J10 IO pins with square waves whose frequencies differ by
// a factor of two. A single logic capture therefore identifies WHICH J10 pin
// each analyzer channel is touching, and simultaneously proves the bank-35
// output path is alive -- so a silent probe can be blamed on wiring rather
// than guessed at.
//
// Per docs: never trust a "no signal" reading from a real design until a
// known-toggling bitstream has been seen on the same probe point.
// CC0 1.0 Universal.

module spu_a7_j10_ident_top (
    input  wire       sys_clk,     // M21, 50 MHz
    input  wire       rst_n,       // H7, active low
    output wire [7:0] j10          // the eight J10 IO pins
);
    // Debounced reset: the raw H7 pad must never drive logic directly
    // (hardware_evidence.md 3.2m).
    reg [15:0] db   = 16'd0;
    reg        rstd = 1'b0;
    always @(posedge sys_clk) begin
        if (rst_n == rstd)   db <= 16'd0;
        else if (&db) begin  rstd <= rst_n; db <= 16'd0; end
        else                 db <= db + 16'd1;
    end

    reg [24:0] cnt = 25'd0;
    always @(posedge sys_clk) begin
        if (!rstd) cnt <= 25'd0;
        else       cnt <= cnt + 25'd1;
    end

    // 50 MHz / 2^(n+1). Bits 9..16 give 48.8 kHz down to 381 Hz -- every one
    // comfortably resolved at a 1 MHz sample rate, and each is 2x its
    // neighbour so they cannot be confused.
    assign j10[0] = cnt[9];    // 48.8 kHz
    assign j10[1] = cnt[10];   // 24.4 kHz
    assign j10[2] = cnt[11];   // 12.2 kHz
    assign j10[3] = cnt[12];   //  6.1 kHz
    assign j10[4] = cnt[13];   //  3.05 kHz
    assign j10[5] = cnt[14];   //  1.53 kHz
    assign j10[6] = cnt[15];   //   763 Hz
    assign j10[7] = cnt[16];   //   381 Hz
endmodule
