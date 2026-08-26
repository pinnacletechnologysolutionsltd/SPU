// spu13_tang25k_gpu_framebuffer_readout_probe.v — digital framebuffer
// readout: the real depth-v2 + depth-compare pipeline (same modules
// spu_gpu_top.v uses, minus the VGA/HDMI HAL -- no video PMOD/PLL
// available on this board, see
// spu_strategy/contract_gpu_video_output_2026-08-25.md), two fixed,
// deliberately overlapping triangles, streamed pixel-by-pixel over
// UART so a host can reconstruct and display the real rendered image
// -- the "point a camera at the screen" proof, minus the screen: the
// picture comes from real silicon, read out digitally instead of
// driven onto analog/TMDS video pins this board doesn't expose.
//
// UART (217 clocks/bit @ 25 MHz = 115200 baud) is far slower than one
// new pixel per clock, and a 640x480 framebuffer (~460KB) doesn't fit
// in this device's BRAM -- so this scans one pixel at a time, throttled
// to UART completion, using explicit step_x/step_y pulses (same manual-
// stepping convention as this session's testbenches), not free-running
// spu_video_timing.
//
// Wire format, repeating forever (host re-syncs on "SPU1" if it misses
// the start): 4-byte marker "SPU1", then 640*480 pixels row-major, each
// as 2 bytes: {4'b0, pixel_r}, {pixel_g, pixel_b} (R4G4B4).

module spu13_tang25k_gpu_framebuffer_readout_probe #(
    parameter CLKS_PER_BIT = 217  // 115200 baud at 25 MHz (this probe's
                                    // internal clk, divided from the
                                    // 50 MHz sys_clk -- see below);
                                    // overridden much smaller in
                                    // simulation only, so a protocol/
                                    // timing check doesn't need to wait
                                    // out real UART bit periods (a full
                                    // 640x480 frame at real 115200 baud
                                    // would need billions of cycles)
    ,parameter SETTLE_EXTRA_CYCLES = 1  // diagnostic-only, see the settle_cnt
                                          // comment below; 1 == today's
                                          // behavior unchanged, overridden
                                          // only for the 2026-08-26 real-
                                          // hardware settle-margin experiment
)(
    input  wire       sys_clk,     // 50 MHz crystal
    output wire [2:0] led,
    output wire       uart_tx
);
    localparam CLK_FREQ = 25000000;

    // Runs at 25 MHz, not the raw 50 MHz sys_clk (real bug found on real
    // hardware, not caught by iverilog simulation, since that's a
    // zero-delay model with no way to expose a real timing violation):
    // this design's own measured Fmax was 44.49 MHz -- BELOW the 50 MHz
    // it was actually being clocked at, despite nextpnr reporting "PASS"
    // against a loose 12 MHz artificial timing constraint used
    // throughout this session's probes for closure checking, never
    // checked against the real operating frequency for a design this
    // size. Symptom: pixels correct in simulation but wrong on real
    // silicon at specific positions (setup/hold violations are data-
    // and path-dependent, not uniform corruption) -- e.g. (50,50)
    // consistently wrong on hardware, consistently right in simulation.
    // This probe's actual throughput is entirely UART-bound (434 cycles/
    // bit) regardless of core clock speed, so there's no cost to running
    // it at 25 MHz instead -- reuses the already-verified
    // spu_tang25k_clk_pixel_div2.v divider (built for VGA, equally
    // valid here) for real timing margin instead of chasing the actual
    // critical path.
    wire clk;
    spu_tang25k_clk_pixel_div2 u_clkdiv (.clk_50(sys_clk), .rst_n(1'b1), .clk_pixel(clk));

    // rst_n is registered (not a raw combinational rst_cnt==8'hFF
    // compare) so the net fanned out to every downstream module's
    // async CLEAR is a clean FF output with a fixed, small clk-to-Q
    // delay -- a real build found 2 hold/removal violations on this
    // path when rst_n was a bare comparator output routed through
    // synthesis-restructured mux logic (see git log for this file):
    // the comparator's extra combinational delay relative to the
    // derived `clk` net's skew was enough to blow a ~0.06ns margin.
    reg [7:0] rst_cnt = 0;
    reg       rst_n_r = 1'b0;
    always @(posedge clk) begin
        if (rst_cnt != 8'hFF) rst_cnt <= rst_cnt + 1;  // freezes at 0xFF,
                                                          // does not wrap --
                                                          // S_RESET below
                                                          // depends on
                                                          // rst_cnt==8'hFF
                                                          // staying true
                                                          // forever after
                                                          // reset
        rst_n_r <= (rst_cnt == 8'hFF);
    end
    wire rst_n = rst_n_r;

    // ── Fixed test triangles: vivid, visually distinguishable colors ──
    // (contract_gpu_depth_dispatch/compare's usual test fixture used
    // near-black colors for oracle contrast checks; this probe uses
    // bright red/green so a human looking at the reconstructed image
    // can see the depth compositing directly, not just the oracle.)
    localparam signed [15:0] A0_0=-16'sd240, B0_0=-16'sd200;
    localparam signed [31:0] C0_0=32'sd108000;
    localparam signed [15:0] A1_0=16'sd250, B1_0=-16'sd150;
    localparam signed [31:0] C1_0=-32'sd5000;
    localparam signed [15:0] A2_0=-16'sd10, B2_0=16'sd350;
    localparam signed [31:0] C2_0=-32'sd17000;
    localparam [15:0] Z0_0=16'd50000, Z1_0=16'd50000, Z2_0=16'd50000;
    localparam [3:0] TRI_R0=4'd15, TRI_G0=4'd0, TRI_B0=4'd0;  // red, far

    // Correction: this probe's original values were hand-derived and
    // wrong (a real bug, not caught by simulation until this test was
    // extended to check the full frame -- the earlier 3-row check never
    // reached triangle1's actual geometry). Corrected to the exact
    // values from software/lib/gpu_depth_v2_oracle.py's triangle_edges()
    // for V0_1=(150,100), V1_1=(450,150), V2_1=(300,400) -- generated,
    // not hand-derived, per this project's own discipline against
    // exactly this class of error.
    localparam signed [15:0] A0_1=-16'sd250, B0_1=-16'sd150;
    localparam signed [31:0] C0_1=32'sd135000;
    localparam signed [15:0] A1_1=16'sd300, B1_1=-16'sd150;
    localparam signed [31:0] C1_1=-32'sd30000;
    localparam signed [15:0] A2_1=-16'sd50, B2_1=16'sd300;
    localparam signed [31:0] C2_1=-32'sd22500;
    localparam [15:0] Z0_1=16'd10000, Z1_1=16'd10000, Z2_1=16'd10000;
    localparam [3:0] TRI_R1=4'd0, TRI_G1=4'd15, TRI_B1=4'd0;  // green, near

    // ── Coverage + depth-v2 + depth-compare (same modules spu_gpu_top.v
    // uses, wired directly -- no HAL, no clk_pixel/clk_tmds needed) ────
    reg setup0 = 0, setup1 = 0;
    reg step_x = 0, step_y = 0;

    wire cov0, cov1;
    wire [3:0] r0, g0, b0, r1, g1, b1;
    wire [3:0] fixed_r, fixed_g, fixed_b;  // unused

    spu_dual_raster u_rast (.clk(clk), .rst_n(rst_n),
        .setup0(setup0),
        .a0_0(A0_0), .b0_0(B0_0), .c0_0(C0_0),
        .a1_0(A1_0), .b1_0(B1_0), .c1_0(C1_0),
        .a2_0(A2_0), .b2_0(B2_0), .c2_0(C2_0),
        .tri_r0(TRI_R0), .tri_g0(TRI_G0), .tri_b0(TRI_B0),
        .setup1(setup1),
        .a0_1(A0_1), .b0_1(B0_1), .c0_1(C0_1),
        .a1_1(A1_1), .b1_1(B1_1), .c1_1(C1_1),
        .a2_1(A2_1), .b2_1(B2_1), .c2_1(C2_1),
        .tri_r1(TRI_R1), .tri_g1(TRI_G1), .tri_b1(TRI_B1),
        .step_x(step_x), .step_y(step_y), .x_span(16'sd640),
        .pixel_r(fixed_r), .pixel_g(fixed_g), .pixel_b(fixed_b),
        .cov0_out(cov0), .cov1_out(cov1),
        .r0_out(r0), .g0_out(g0), .b0_out(b0),
        .r1_out(r1), .g1_out(g1), .b1_out(b1));

    wire signed [55:0] A_z0, B_z0, C_z0, A_z1, B_z1, C_z1;
    wire [6:0] frac_bits0, frac_bits1;
    wire ready0, ready1;

    spu_depth_dispatch u_dispatch (.clk(clk), .rst_n(rst_n),
        .depth_setup0(setup0), .depth_setup1(setup1),
        .a0_0(A0_0), .b0_0(B0_0), .a1_0(A1_0), .b1_0(B1_0), .a2_0(A2_0), .b2_0(B2_0),
        .c0_0(C0_0), .c1_0(C1_0), .c2_0(C2_0), .z0_0(Z0_0), .z1_0(Z1_0), .z2_0(Z2_0),
        .a0_1(A0_1), .b0_1(B0_1), .a1_1(A1_1), .b1_1(B1_1), .a2_1(A2_1), .b2_1(B2_1),
        .c0_1(C0_1), .c1_1(C1_1), .c2_1(C2_1), .z0_1(Z0_1), .z1_1(Z1_1), .z2_1(Z2_1),
        .A_z0(A_z0), .B_z0(B_z0), .C_z0(C_z0), .frac_bits0(frac_bits0), .ready0(ready0),
        .A_z1(A_z1), .B_z1(B_z1), .C_z1(C_z1), .frac_bits1(frac_bits1), .ready1(ready1));

    reg attr_setup0 = 0, attr_setup1 = 0;
    wire signed [55:0] depth0, depth1;
    spu_attr_stepper u_attr0 (.clk(clk), .rst_n(rst_n), .setup(attr_setup0),
        .a_coef(A_z0), .b_coef(B_z0), .c_coef(C_z0),
        .step_x(step_x), .step_y(step_y), .frac_bits(frac_bits0), .value_out(depth0));
    spu_attr_stepper u_attr1 (.clk(clk), .rst_n(rst_n), .setup(attr_setup1),
        .a_coef(A_z1), .b_coef(B_z1), .c_coef(C_z1),
        .step_x(step_x), .step_y(step_y), .frac_bits(frac_bits1), .value_out(depth1));

    wire [3:0] pixel_r, pixel_g, pixel_b;
    spu_depth_compare u_compare (
        .cov0(cov0), .cov1(cov1), .depth0(depth0), .depth1(depth1),
        .r0(r0), .g0(g0), .b0(b0), .r1(r1), .g1(g1), .b1(b1),
        .pixel_r(pixel_r), .pixel_g(pixel_g), .pixel_b(pixel_b));

    // ── UART TX core: start/byte/busy handshake ─────────────────────
    reg [9:0] tx_shift = 10'h3FF;
    reg [3:0] tx_bits = 0;
    reg [15:0] baud_cnt = 0;
    reg tx_busy = 0;
    reg [7:0] tx_byte_in = 0;
    reg tx_start = 0;
    assign uart_tx = tx_shift[0];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_shift <= 10'h3FF; tx_bits <= 0; baud_cnt <= 0; tx_busy <= 0;
        end else if (tx_busy) begin
            if (baud_cnt < CLKS_PER_BIT - 1) baud_cnt <= baud_cnt + 1;
            else begin
                baud_cnt <= 0;
                tx_shift <= {1'b1, tx_shift[9:1]};
                if (tx_bits == 1) begin tx_busy <= 0; tx_bits <= 0; end
                else tx_bits <= tx_bits - 1;
            end
        end else if (tx_start) begin
            tx_shift <= {1'b1, tx_byte_in, 1'b0};
            tx_bits <= 10; tx_busy <= 1; baud_cnt <= 0;
        end
    end

    // ── Scan/transmit sequencer ──────────────────────────────────────
    localparam [4:0]
        S_RESET=0, S_SETUP=1, S_WAIT_READY=2, S_ATTR_SETUP=3,
        S_MARKER_SEND=4, S_MARKER_WAIT=5,
        S_ROW_STEP=6, S_COL_STEP=7, S_SETTLE=8,
        S_SEND0=9, S_WAIT0=10, S_SEND1=11, S_WAIT1=12, S_NEXT=13;
    reg [4:0] state = S_RESET;
    reg [2:0] marker_idx = 0;
    reg [9:0] px = 0, py = 0;
    reg seen_ready0 = 0, seen_ready1 = 0;

    // SETTLE_EXTRA_CYCLES (module parameter above), default 1 == exactly
    // today's behavior (one settle cycle). 2026-08-26: real hardware
    // disagrees with the oracle right at TRI0's first coverage transition
    // ((50,50) onward) despite sim being bit-exact over the same rows and
    // nextpnr reporting a comfortable Fmax margin -- a shift-search on the
    // raw byte stream ruled out a UART framing bug (flat 70190 mismatches
    // at every tested offset). This parameter exists ONLY to test whether
    // more real settle time changes that result -- a real hardware
    // experiment, not a permanent fix. If overriding it >1 changes the
    // mismatch pattern, it's a settle-margin issue invisible to zero-delay
    // sim and to nextpnr's STA; if not, timing is ruled out entirely.
    reg [3:0] settle_cnt = 0;

    wire [7:0] marker_byte = (marker_idx==0) ? "S" : (marker_idx==1) ? "P" :
                              (marker_idx==2) ? "U" : "1";

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_RESET; setup0 <= 0; setup1 <= 0;
            attr_setup0 <= 0; attr_setup1 <= 0;
            step_x <= 0; step_y <= 0; tx_start <= 0;
            px <= 0; py <= 0; marker_idx <= 0;
            seen_ready0 <= 0; seen_ready1 <= 0; settle_cnt <= 0;
        end else begin
            setup0 <= 0; setup1 <= 0; attr_setup0 <= 0; attr_setup1 <= 0;
            step_x <= 0; step_y <= 0; tx_start <= 0; settle_cnt <= 0;
            if (ready0) seen_ready0 <= 1'b1;
            if (ready1) seen_ready1 <= 1'b1;

            case (state)
                S_RESET: if (rst_cnt == 8'hFF) begin
                    setup0 <= 1; setup1 <= 1;
                    state <= S_SETUP;
                end
                S_SETUP: state <= S_WAIT_READY;
                S_WAIT_READY: if (seen_ready0 && seen_ready1) begin
                    attr_setup0 <= 1; attr_setup1 <= 1;
                    state <= S_ATTR_SETUP;
                end
                S_ATTR_SETUP: begin
                    px <= 0; py <= 0; marker_idx <= 0;
                    state <= S_MARKER_SEND;
                end
                S_MARKER_SEND: begin
                    tx_byte_in <= marker_byte;
                    tx_start <= 1;
                    state <= S_MARKER_WAIT;
                end
                S_MARKER_WAIT: if (!tx_busy && !tx_start) begin
                    if (marker_idx == 3) state <= S_SETTLE;
                    else begin
                        marker_idx <= marker_idx + 1;
                        state <= S_MARKER_SEND;
                    end
                end
                S_ROW_STEP: begin
                    step_y <= 1;
                    state <= S_SETTLE;
                end
                S_COL_STEP: begin
                    step_x <= 1;
                    state <= S_SETTLE;
                end
                S_SETTLE: begin
                    // SETTLE_EXTRA_CYCLES==1 (default): identical to the
                    // original single-cycle settle. >1 is the diagnostic
                    // experiment described above.
                    if (settle_cnt == SETTLE_EXTRA_CYCLES - 1) state <= S_SEND0;
                    else settle_cnt <= settle_cnt + 1;
                end
                S_SEND0: begin
                    tx_byte_in <= {4'b0, pixel_r};
                    tx_start <= 1;
                    state <= S_WAIT0;
                end
                S_WAIT0: if (!tx_busy && !tx_start) state <= S_SEND1;
                S_SEND1: begin
                    tx_byte_in <= {pixel_g, pixel_b};
                    tx_start <= 1;
                    state <= S_WAIT1;
                end
                S_WAIT1: if (!tx_busy && !tx_start) state <= S_NEXT;
                S_NEXT: begin
                    if (px == 10'd639) begin
                        px <= 0;
                        if (py == 10'd479) begin
                            // Loop: re-send the whole frame. MUST re-pulse
                            // attr_setup0/1 here (same as the very first
                            // pass, via S_ATTR_SETUP) -- the per-pixel
                            // depth accumulators in spu_attr_stepper.v
                            // don't know about "frame boundaries" on their
                            // own; without reseeding them to the origin,
                            // every frame after the first would keep
                            // accumulating from wherever the previous
                            // frame's scan ended, computing depth at the
                            // wrong virtual position for the entire frame.
                            // Real bug, caught on real hardware after the
                            // simulation test (which only checked 3 rows
                            // of the FIRST frame) missed it.
                            attr_setup0 <= 1; attr_setup1 <= 1;
                            state <= S_ATTR_SETUP;
                        end else begin
                            py <= py + 1;
                            state <= S_ROW_STEP;
                        end
                    end else begin
                        px <= px + 1;
                        state <= S_COL_STEP;
                    end
                end
                default: state <= S_RESET;
            endcase
        end
    end

    reg [2:0] led_reg = 3'b0;
    always @(posedge clk) led_reg <= led_reg ^ {pixel_r[3], pixel_g[3], pixel_b[3]};
    assign led = led_reg;

endmodule
