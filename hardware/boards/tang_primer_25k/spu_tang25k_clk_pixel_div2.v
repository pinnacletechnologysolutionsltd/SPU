// spu_tang25k_clk_pixel_div2.v — 50 MHz -> 25 MHz pixel clock, exact
// divide-by-2, for spu_gpu_top.v's VGA path on Tang Primer 25K.
//
// Deliberately NOT a PLLA-based clock: GW5A-25A's real multi-output PLL
// primitive (PLLA, see pll_gowin_stub.v) has never been instantiated
// anywhere in this repo, and its blackbox stub has no internal behavior
// to simulate against -- there is no way to verify a chosen ODIV/FBDIV/
// IDIV parameter set here without real datasheet cross-reference this
// session doesn't have. 50/25 is an exact integer divide-by-2, which a
// plain toggle flip-flop does correctly and verifiably with zero risk
// of a wrong PLL config -- the right tool for THIS specific ratio.
//
// This does NOT solve HDMI's clk_tmds (250 MHz, a genuine 10x multiply
// from clk_pixel, not an integer divide of sys_clk) -- that still needs
// a real PLLA config, deliberately left for separate, careful work
// rather than guessed at here. See
// spu_strategy/contract_gpu_video_output_2026-08-25.md.
//
// CC0 1.0 Universal.

module spu_tang25k_clk_pixel_div2 (
    input  wire clk_50,
    input  wire rst_n,
    output reg  clk_pixel
);

    initial clk_pixel = 1'b0;

    always @(posedge clk_50 or negedge rst_n) begin
        if (!rst_n) clk_pixel <= 1'b0;
        else clk_pixel <= ~clk_pixel;
    end

endmodule
