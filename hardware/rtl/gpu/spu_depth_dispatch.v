// spu_depth_dispatch.v — owns the depth_setup0/depth_setup1 pending
// queue and per-unit input latching, then drives spu_depth_math.v (unit-
// agnostic) with whichever job is dispatched. One shared depth-setup
// sequencer serves both spu_dual_raster.v triangle units, not two
// duplicated ones -- see
// spu_strategy/contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md
// §8/§9.
//
// Correctness note this module exists to fix: depth_setupN's a/b/c/z
// inputs MUST be latched at the moment the pulse fires, not read again
// whenever a deferred (pending) dispatch actually happens -- otherwise
// a host that starts loading a new triangle for the same unit while its
// depth request is still queued would silently corrupt the pending
// job. This was a real gap in the original prose sketch, found during
// implementation, not in the sketch itself.
//
// Host contract: do not re-pulse depth_setupN for the same unit while
// its previous request is still outstanding (pendingN set, or a job
// for that unit in flight) -- a second pulse before the first is
// latched would overwrite the latch registers before they're read.
// Deliberately a 1-deep queue, not a FIFO: the current one-triangle-
// at-a-time host usage pattern doesn't call for more (AGENTS.md §2.2).
//
// CC0 1.0 Universal.

module spu_depth_dispatch (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        depth_setup0,
    input  wire        depth_setup1,
    input  wire signed [15:0] a0_0, b0_0, a1_0, b1_0, a2_0, b2_0,
    input  wire signed [31:0] c0_0, c1_0, c2_0,
    input  wire [15:0] z0_0, z1_0, z2_0,
    input  wire signed [15:0] a0_1, b0_1, a1_1, b1_1, a2_1, b2_1,
    input  wire signed [31:0] c0_1, c1_1, c2_1,
    input  wire [15:0] z0_1, z1_1, z2_1,
    output reg  signed [55:0] A_z0, B_z0, C_z0,
    output reg  [6:0]  frac_bits0,
    output reg          ready0,
    output reg  signed [55:0] A_z1, B_z1, C_z1,
    output reg  [6:0]  frac_bits1,
    output reg          ready1
);

    reg pending0, pending1, active_unit;

    reg signed [15:0] a0_0_l, b0_0_l, a1_0_l, b1_0_l, a2_0_l, b2_0_l;
    reg signed [31:0] c0_0_l, c1_0_l, c2_0_l;
    reg [15:0] z0_0_l, z1_0_l, z2_0_l;
    reg signed [15:0] a0_1_l, b0_1_l, a1_1_l, b1_1_l, a2_1_l, b2_1_l;
    reg signed [31:0] c0_1_l, c1_1_l, c2_1_l;
    reg [15:0] z0_1_l, z1_1_l, z2_1_l;

    localparam S_IDLE = 1'd0, S_RUN = 1'd1;
    reg state;

    wire signed [15:0] a0 = active_unit ? a0_1_l : a0_0_l;
    wire signed [15:0] b0 = active_unit ? b0_1_l : b0_0_l;
    wire signed [15:0] a1 = active_unit ? a1_1_l : a1_0_l;
    wire signed [15:0] b1 = active_unit ? b1_1_l : b1_0_l;
    wire signed [15:0] a2 = active_unit ? a2_1_l : a2_0_l;
    wire signed [15:0] b2 = active_unit ? b2_1_l : b2_0_l;
    wire signed [31:0] c0 = active_unit ? c0_1_l : c0_0_l;
    wire signed [31:0] c1 = active_unit ? c1_1_l : c1_0_l;
    wire signed [31:0] c2 = active_unit ? c2_1_l : c2_0_l;
    wire [15:0] z0 = active_unit ? z0_1_l : z0_0_l;
    wire [15:0] z1 = active_unit ? z1_1_l : z1_0_l;
    wire [15:0] z2 = active_unit ? z2_1_l : z2_0_l;

    wire signed [55:0] A_z_m, B_z_m, C_z_m;
    wire [6:0] frac_bits_m;
    wire math_done;
    reg math_start_r;

    spu_depth_math u_math (
        .clk(clk), .rst_n(rst_n), .start(math_start_r),
        .a0(a0), .b0(b0), .a1(a1), .b1(b1), .a2(a2), .b2(b2),
        .c0(c0), .c1(c1), .c2(c2), .z0(z0), .z1(z1), .z2(z2),
        .A_z(A_z_m), .B_z(B_z_m), .C_z(C_z_m), .frac_bits(frac_bits_m),
        .done(math_done)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pending0 <= 1'b0;
            pending1 <= 1'b0;
            state <= S_IDLE;
            math_start_r <= 1'b0;
            ready0 <= 1'b0;
            ready1 <= 1'b0;
        end else begin
            ready0 <= 1'b0;
            ready1 <= 1'b0;
            math_start_r <= 1'b0;

            // Latch inputs unconditionally at the pulse, regardless of
            // whether dispatch happens this cycle or is deferred.
            if (depth_setup0) begin
                a0_0_l <= a0_0; b0_0_l <= b0_0; a1_0_l <= a1_0; b1_0_l <= b1_0;
                a2_0_l <= a2_0; b2_0_l <= b2_0;
                c0_0_l <= c0_0; c1_0_l <= c1_0; c2_0_l <= c2_0;
                z0_0_l <= z0_0; z1_0_l <= z1_0; z2_0_l <= z2_0;
                pending0 <= 1'b1;
            end
            if (depth_setup1) begin
                a0_1_l <= a0_1; b0_1_l <= b0_1; a1_1_l <= a1_1; b1_1_l <= b1_1;
                a2_1_l <= a2_1; b2_1_l <= b2_1;
                c0_1_l <= c0_1; c1_1_l <= c1_1; c2_1_l <= c2_1;
                z0_1_l <= z0_1; z1_1_l <= z1_1; z2_1_l <= z2_1;
                pending1 <= 1'b1;
            end

            case (state)
                S_IDLE: begin
                    if (pending0) begin
                        pending0 <= 1'b0;
                        active_unit <= 1'b0;
                        math_start_r <= 1'b1;
                        state <= S_RUN;
                    end else if (pending1) begin
                        pending1 <= 1'b0;
                        active_unit <= 1'b1;
                        math_start_r <= 1'b1;
                        state <= S_RUN;
                    end
                end
                S_RUN: if (math_done) begin
                    if (active_unit) begin
                        A_z1 <= A_z_m; B_z1 <= B_z_m; C_z1 <= C_z_m;
                        frac_bits1 <= frac_bits_m;
                        ready1 <= 1'b1;
                    end else begin
                        A_z0 <= A_z_m; B_z0 <= B_z_m; C_z0 <= C_z_m;
                        frac_bits0 <= frac_bits_m;
                        ready0 <= 1'b1;
                    end
                    state <= S_IDLE;
                end
            endcase
        end
    end

endmodule
