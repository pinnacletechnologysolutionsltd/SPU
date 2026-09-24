// spu_a7_gpu_vga_top.v — Wukong Artix-7 spin: the real rasterizer on the
// proven VGA display path. Two static overlapping triangles resolved by
// per-pixel depth, no host link.
//
// Why this exists. hardware_evidence.md §3.8 established the VGA path in
// silicon (640x480@60, 0.006% timing error, colour bars on a monitor) using
// spu_video_pattern. This spin swaps the test pattern for spu_gpu_top's
// actual coverage rasterizer and changes nothing else about the display
// path: same clocking, same reset conditioning, same hal_vga, same
// three-resistor DAC on J10, same spu_a7_vga_fix.xdc mapping.
//
// The triangle is hardcoded. There is deliberately no host interface here:
// if the shape appears, the rasterizer works on silicon; if it does not, the
// fault is in the GPU and not in a link that would otherwise have to be
// debugged at the same time.
//
// spu_gpu_top is built with ENABLE_HDMI=0 -- openXC7's placer hangs on
// differential output (upstream issue #66) -- and DEVICE="A7".
//
// CC0 1.0 Universal.

module spu_a7_gpu_vga_top #(
    parameter PREPARED_SCENE = 0,
    parameter COST_STIMULUS  = 0,
    parameter FOUR_PRIMITIVE_SCENE = 0,
    parameter T1H_SCALAR_SCENE = 0,
    parameter T1H_SCALAR_DIAG = 0,
    parameter T1I_UV_SCENE = 0,
    parameter T1I_UV_DIAG = 0,
    parameter T1I_UV_REG_DIAG = 0,
    parameter T1I_DEPTH_DIAG = 0,
    parameter GPU_POST_WINNER_REG = 0
) (
    input  wire        sys_clk,      // M21, 50 MHz
    input  wire        rst_n,        // H7, active low, board PULLUP
`ifdef GPU_T1D_UART
    input  wire        uart_rx,      // F3, onboard CH340 TXD
`endif
    output wire        vga_r,        // 1 bit per channel through 3 resistors
    output wire        vga_g,
    output wire        vga_b,
    output wire        vga_hsync,
    output wire        vga_vsync
`ifdef GPU_T1D_DIAG
    , output wire      diag_tx
`endif
);

    // ── Reset conditioning ───────────────────────────────────────────────
    // Identical to spu_a7_vga_top. rst_n (H7) has no external pull-down;
    // feeding it straight into async resets left this board dead for three
    // weeks (hardware_evidence.md §3.2m). Debounce before use.
    reg [15:0] db_cnt   = 16'd0;
    reg        rst_n_db = 1'b0;
    always @(posedge sys_clk) begin
        if (rst_n == rst_n_db)      db_cnt <= 16'd0;
        else if (&db_cnt) begin     rst_n_db <= rst_n; db_cnt <= 16'd0; end
        else                        db_cnt <= db_cnt + 16'd1;
    end

    // ── Pixel clock: 50 MHz / 2 = 25 MHz, exactly. No MMCM. ──────────────
    reg clk_div = 1'b0;
    always @(posedge sys_clk) clk_div <= ~clk_div;

    wire clk_pixel;
    BUFG u_bufg_pix (.I(clk_div), .O(clk_pixel));

    reg [2:0] pix_rst_sync = 3'b000;
    always @(posedge clk_pixel) pix_rst_sync <= {pix_rst_sync[1:0], rst_n_db};
    wire pix_rst_n = pix_rst_sync[2];

    // Synthesis-cost stimulus only. Canonical and physical builds leave
    // COST_STIMULUS=0, so this state and the prepared-scene path disappear.
    wire [7:0] scene_rx_byte;
    wire       scene_rx_valid;
    wire       uart_frame_err;
    generate
`ifdef GPU_T1D_UART
        if (1'b1) begin : t1d_uart_input
            wire [7:0] uart_data;
            wire       uart_valid;
            spu_uart_rx #(.CLK_HZ(25_000_000), .BAUD(115200)) u_uart (
                .clk(clk_pixel), .rst_n(pix_rst_n), .rx(uart_rx),
                .data(uart_data), .valid(uart_valid),
                .frame_err(uart_frame_err));
            assign scene_rx_byte  = uart_data;
            assign scene_rx_valid = uart_valid;
        end
`else
        if (1'b1) begin : no_uart_input
            assign uart_frame_err = 1'b0;
        end
        if (COST_STIMULUS) begin : cost_stimulus
            (* keep *) reg [8:0] lfsr = 9'h001;
            always @(posedge clk_pixel) begin
                if (!pix_rst_n)
                    lfsr <= 9'h001;
                else
                    lfsr <= {lfsr[7:0], lfsr[8] ^ lfsr[4]};
            end
            assign scene_rx_byte  = lfsr[7:0];
            assign scene_rx_valid = lfsr[8];
        end else begin : no_cost_stimulus
            assign scene_rx_byte  = 8'h00;
            assign scene_rx_valid = 1'b0;
        end
`endif
    endgenerate

    // ── Frame-start pulse for triangle setup ─────────────────────────────
    // REQUIRED, not an optimisation. spu_gpu_top derives step_y from the
    // horizontal wrap alone, so step_y fires on all 525 lines of the frame
    // while only 480 are active. The edge accumulators are anchored to (0,0)
    // by `setup` and never re-anchored, so a triangle set up once drifts by
    // 525*B per frame -- measured, see spu_gpu_top_frame_anchor_tb.v -- and
    // leaves the screen almost immediately.
    //
    // As of 2026-09-05 spu_gpu_top does this re-anchoring itself, so this
    // pulse is redundant. It is kept because it is also what arms the unit,
    // and pulsing setup at (0,0) is exactly what the internal fix does; the
    // two coincide rather than conflict.
    //
    // This second spu_video_timing instance exists only to see (x,y): it is
    // a pure counter on the same clock and reset as the one inside
    // spu_gpu_top, so the two stay in lockstep by construction. Cheaper than
    // widening spu_gpu_top's port list for a bring-up spin.
    wire [9:0] tx, ty;
    wire t_hsync, t_vsync, t_active;
    spu_video_timing u_tick (
        .clk(clk_pixel), .rst_n(pix_rst_n),
        .x(tx), .y(ty), .hsync(t_hsync), .vsync(t_vsync), .active(t_active));

    // setup coincides with (0,0). In spu_edge_stepper `setup` takes priority
    // over step_y, so f loads C -- the value for (0,0) -- on exactly the
    // cycle the counters read (0,0).
    wire frame_start = (tx == 10'd0) && (ty == 10'd0);

    // ── The scene: two overlapping triangles, resolved by depth ──────────
    // Edge function for V_i -> V_j, inside when >= 0:
    //     A = yj - yi        B = -(xj - xi)        C = -(A*xi + B*yi)
    // For both triangles every edge evaluates to +257600 at its opposite
    // vertex, so the winding is consistent and all three half-planes agree
    // on the interior. That common value is D, and sum_i E_i(x,y) == D
    // identically, which is what makes E_i the barycentric weight the depth
    // interpolator uses.
    //
    // Both triangles share the top edge y=0 from x=40 to x=600 and differ
    // only in where their apex falls, so they overlap in a large region
    // that INCLUDES SCANLINE 0. That is deliberate: the depth-anchor defect
    // fixed on 2026-09-06 was row-0-only, so a scene that does not reach
    // row 0 could not show that class of fault on a monitor.
    //
    //   tri0 (red)   V0 (600,0)  V1 (40,0)  V2 (120,460)   apex bottom-left
    //   tri1 (green) V0 (600,0)  V1 (40,0)  V2 (520,460)   apex bottom-right
    localparam signed [15:0] T0_E0_A = 16'sd0,    T0_E0_B = 16'sd560;
    localparam signed [31:0] T0_E0_C = 32'sd0;          // V0 -> V1
    localparam signed [15:0] T0_E1_A = 16'sd460,  T0_E1_B = -16'sd80;
    localparam signed [31:0] T0_E1_C = -32'sd18400;     // V1 -> V2
    localparam signed [15:0] T0_E2_A = -16'sd460, T0_E2_B = -16'sd480;
    localparam signed [31:0] T0_E2_C = 32'sd276000;     // V2 -> V0

    localparam signed [15:0] T1_E0_A = 16'sd0,    T1_E0_B = 16'sd560;
    localparam signed [31:0] T1_E0_C = 32'sd0;          // V0 -> V1
    localparam signed [15:0] T1_E1_A = 16'sd460,  T1_E1_B = -16'sd480;
    localparam signed [31:0] T1_E1_C = -32'sd18400;     // V1 -> V2
    localparam signed [15:0] T1_E2_A = -16'sd460, T1_E2_B = -16'sd80;
    localparam signed [31:0] T1_E2_C = 32'sd276000;     // V2 -> V0

    // ── Depth ────────────────────────────────────────────────────────────
    // z(x,y) = sum_i z_i * E_i(x,y) / D. At V0 only E1 is non-zero, at V1
    // only E2, at V2 only E0 -- so the port z0 is the depth AT V2, z1 at V0,
    // and z2 at V1. That permutation is easy to get wrong; it was derived
    // from the edge functions above and then confirmed by rendering a full
    // 640x480 frame and comparing every pixel against an independent oracle.
    //
    // tri0 is NEAR on the left and FAR on the right; tri1 the reverse. Both
    // interpolate 400..3600 across the top edge, so in the overlap they cross
    // exactly where the two are equidistant:
    //
    //     400 + (x-40)*(3200/560) = 3600 - (x-40)*(3200/560)  =>  x = 320
    //
    // THE PREDICTION, and the whole point of this spin: a colour boundary at
    // x = 320, the exact horizontal centre of the screen, running straight
    // down from the top edge to where the two triangles separate at y ~= 268.
    // It is vertical because both depth planes have the same y gradient, so
    // their difference has no y term. Below y ~= 268 the triangles no longer
    // overlap and the picture is simply red on the left, green on the right.
    //
    // Nothing in the geometry puts an edge at x=320. A boundary anywhere else
    // is a depth fault, not a coverage fault -- which is what makes this a
    // test of the depth path rather than of the rasterizer.
    localparam [15:0] T0_Z0 = 16'd700,  T0_Z1 = 16'd3600, T0_Z2 = 16'd400;
    localparam [15:0] T1_Z0 = 16'd700,  T1_Z1 = 16'd400,  T1_Z2 = 16'd3600;

    // ── GPU ──────────────────────────────────────────────────────────────
    wire [3:0] gr, gg, gb;
    wire g_hsync, g_vsync;
`ifdef GPU_T1D_DIAG
    wire       diag_start_accepted;
    wire       diag_payload_accepted;
    wire [6:0] diag_payload_count;
    wire       diag_receiving;
    wire       diag_active_bank;
    wire       diag_commit_pending;
    wire       diag_activate_scene;
    wire       diag_frame_start;
    wire       diag_ready0, diag_ready1, diag_generation_matches;
`endif

    spu_gpu_top #(
        .DEVICE("A7"), .ENABLE_HDMI(0),
        .PREPARED_SCENE(PREPARED_SCENE),
        .FOUR_PRIMITIVE_SCENE(FOUR_PRIMITIVE_SCENE),
        .T1H_SCALAR_SCENE(T1H_SCALAR_SCENE),
        .T1H_SCALAR_DIAG(T1H_SCALAR_DIAG),
        .T1I_UV_SCENE(T1I_UV_SCENE),
        .T1I_UV_DIAG(T1I_UV_DIAG),
        .T1I_UV_REG_DIAG(T1I_UV_REG_DIAG),
        .T1I_DEPTH_DIAG(T1I_DEPTH_DIAG),
        .GPU_POST_WINNER_REG(GPU_POST_WINNER_REG)
    ) u_gpu (
        .clk_pixel(clk_pixel),
        .clk_tmds (clk_pixel),   // unused with ENABLE_HDMI=0
        .rst_n    (pix_rst_n),

        .tri0_setup(frame_start),
        .tri0_a0(T0_E0_A), .tri0_b0(T0_E0_B), .tri0_c0(T0_E0_C),
        .tri0_a1(T0_E1_A), .tri0_b1(T0_E1_B), .tri0_c1(T0_E1_C),
        .tri0_a2(T0_E2_A), .tri0_b2(T0_E2_B), .tri0_c2(T0_E2_C),
        .tri0_r(4'hF), .tri0_g(4'h0), .tri0_b(4'h0),   // red
        .tri0_z0(T0_Z0), .tri0_z1(T0_Z1), .tri0_z2(T0_Z2),

        .tri1_setup(frame_start),
        .tri1_a0(T1_E0_A), .tri1_b0(T1_E0_B), .tri1_c0(T1_E0_C),
        .tri1_a1(T1_E1_A), .tri1_b1(T1_E1_B), .tri1_c1(T1_E1_C),
        .tri1_a2(T1_E2_A), .tri1_b2(T1_E2_B), .tri1_c2(T1_E2_C),
        .tri1_r(4'h0), .tri1_g(4'hF), .tri1_b(4'h0),   // green
        .tri1_z0(T1_Z0), .tri1_z1(T1_Z1), .tri1_z2(T1_Z2),

        .scene_rx_byte(scene_rx_byte),
        .scene_rx_valid(scene_rx_valid),

        .vga_r(gr), .vga_g(gg), .vga_b(gb),
        .vga_hsync(g_hsync), .vga_vsync(g_vsync)
`ifdef GPU_T1D_DIAG
        , .diag_start_accepted(diag_start_accepted),
        .diag_payload_accepted(diag_payload_accepted),
        .diag_payload_count(diag_payload_count),
        .diag_receiving(diag_receiving),
        .diag_active_bank(diag_active_bank),
        .diag_commit_pending(diag_commit_pending),
        .diag_activate_scene(diag_activate_scene),
        .diag_frame_start(diag_frame_start),
        .diag_ready0(diag_ready0), .diag_ready1(diag_ready1),
        .diag_generation_matches(diag_generation_matches)
`endif
        ,

        .tmds_clk_p(), .tmds_clk_n(), .tmds_d_p(), .tmds_d_n());

    // ── Output ───────────────────────────────────────────────────────────
    // spu_gpu_top already delays sync to match its colour pipeline and
    // already blanks through hal_vga, so only the MSB of each channel is
    // brought out, exactly as in the proven §3.8 spin.
    assign vga_r     = gr[3];
    assign vga_g     = gg[3];
    assign vga_b     = gb[3];
    assign vga_hsync = g_hsync;
    assign vga_vsync = g_vsync;

`ifdef GPU_T1D_DIAG
    wire [127:0] diag_record_data;
    wire         diag_record_valid;
    wire         diag_record_ready;

    spu_t1d_diag_record u_diag_record (
        .clk(clk_pixel), .rst_n(pix_rst_n),
        .ready_state(pix_rst_n),
        .start_accepted(diag_start_accepted),
        .payload_accepted(diag_payload_accepted),
        .payload_byte(scene_rx_byte),
        .frame_start(diag_frame_start),
        .frame_error(uart_frame_err),
        .loader_commit_pending(diag_commit_pending),
        .scene_activate(diag_activate_scene),
        .active_bank(diag_active_bank),
        .record_ready(diag_record_ready),
        .record_valid(diag_record_valid),
        .record_data(diag_record_data));

    spu_t1d_diag_uart_tx u_diag_uart_tx (
        .clk(clk_pixel), .rst_n(pix_rst_n),
        .record_data(diag_record_data),
        .record_valid(diag_record_valid),
        .record_ready(diag_record_ready),
        .tx(diag_tx));
`endif

endmodule
