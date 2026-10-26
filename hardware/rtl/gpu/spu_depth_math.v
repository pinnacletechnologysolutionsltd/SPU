// spu_depth_math.v — depth-v2 setup arithmetic: dot products, denominator,
// reciprocal (via spu_reciprocal_core.v, its own subordinate
// micro-sequencer, not a second master -- see
// spu_strategy/contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md
// §8), final scale. Unit-agnostic: operates on whichever job's inputs
// are presented; spu_depth_dispatch.v owns per-unit latching and the
// setup0/setup1 pending queue.
//
// D = c0+c1+c2 needs no multiply (F_i(0,0)=c_i, F0+F1+F2 is constant).
// The shared multiplier is magnitude-only (unsigned): every sign is
// extracted here and reapplied after the multiply, never carried
// through spu_shared_mult35.v itself.
//
// No floating point, no division. CC0 1.0 Universal.

module spu_depth_math (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire signed [15:0] a0, b0, a1, b1, a2, b2,
    input  wire signed [31:0] c0, c1, c2,
    input  wire [15:0] z0, z1, z2,
    output reg  signed [55:0] A_z, B_z, C_z,
    output reg  [6:0]  frac_bits,
    output reg          done
);

    function [15:0] abs16;
        input signed [15:0] v;
        reg signed [16:0] ext;
        begin
            ext = {v[15], v};
            abs16 = v[15] ? (-ext) : ext;
        end
    endfunction
    function [31:0] abs32;
        input signed [31:0] v;
        reg signed [32:0] ext;
        begin
            ext = {v[31], v};
            abs32 = v[31] ? (-ext) : ext;
        end
    endfunction
    function [33:0] abs34;
        input signed [33:0] v;
        reg signed [34:0] ext;
        begin
            ext = {v[33], v};
            abs34 = v[33] ? (-ext) : ext;
        end
    endfunction
    function [39:0] abs40;
        input signed [39:0] v;
        reg signed [40:0] ext;
        begin
            ext = {v[39], v};
            abs40 = v[39] ? (-ext) : ext;
        end
    endfunction

    wire [15:0] a0m = abs16(a0), b0m = abs16(b0);
    wire [15:0] a1m = abs16(a1), b1m = abs16(b1);
    wire [15:0] a2m = abs16(a2), b2m = abs16(b2);
    wire [31:0] c0m = abs32(c0), c1m = abs32(c1), c2m = abs32(c2);

    // D = c0+c1+c2, 34-bit signed -- 32-bit inputs, 2 guard bits for a
    // 3-way sum, never overflows.
    wire signed [33:0] D = {{2{c0[31]}}, c0} + {{2{c1[31]}}, c1} + {{2{c2[31]}}, c2};
    wire d_sign = D[33];
    wire [33:0] d_abs = abs34(D);

    localparam [3:0]
        S_IDLE = 4'd0, S_SA0 = 4'd1, S_SA1 = 4'd2, S_SA2 = 4'd3,
        S_SB0 = 4'd4, S_SB1 = 4'd5, S_SB2 = 4'd6,
        S_SC0 = 4'd7, S_SC1 = 4'd8, S_SC2 = 4'd9,
        S_RECIP_START = 4'd10, S_RECIP_WAIT = 4'd11,
        S_SCALE_A = 4'd12, S_SCALE_B = 4'd13, S_SCALE_C = 4'd14,
        S_DONE = 4'd15;
    reg [3:0] state;

    // 40-bit signed: covers the provable |Sc| < 2**38 bound for REAL
    // 640x480 screen-derived c_i (|c_i| <= 2*639*479 < 2**20; see
    // spu_shared_mult35.v's width-history comment for why this is the
    // right bound, not c_i's full 32-bit port range) with margin. Sa/Sb
    // (from 16-bit a_i/b_i) need far less; one uniform width for all
    // three is simpler and the extra bits are cheap.
    reg signed [39:0] Sa, Sb, Sc;
    reg [15:0] recip_y;
    reg [6:0]  recip_exp;

    wire recip_start = (state == S_RECIP_START);
    wire recip_done, recip_busy_w;
    wire [15:0] recip_y_out;
    wire [6:0]  recip_exp_out;
    wire [39:0] recip_mult_a;
    wire [16:0] recip_mult_b;
    wire [56:0] shared_p;

    spu_reciprocal_core u_recip (
        .clk(clk), .rst_n(rst_n), .start(recip_start), .d_in(d_abs),
        .y_out(recip_y_out), .exp_out(recip_exp_out), .done(recip_done),
        .degenerate(), .mult_a(recip_mult_a), .mult_b(recip_mult_b),
        .mult_p(shared_p), .busy(recip_busy_w)
    );

    wire [39:0] Sa_abs = abs40(Sa);
    wire [39:0] Sb_abs = abs40(Sb);
    wire [39:0] Sc_abs = abs40(Sc);

    reg [39:0] own_a;
    reg [16:0] own_b;
    always @(*) begin
        case (state)
            S_SA0: begin own_a = {24'd0, a0m}; own_b = {1'd0, z0}; end
            S_SA1: begin own_a = {24'd0, a1m}; own_b = {1'd0, z1}; end
            S_SA2: begin own_a = {24'd0, a2m}; own_b = {1'd0, z2}; end
            S_SB0: begin own_a = {24'd0, b0m}; own_b = {1'd0, z0}; end
            S_SB1: begin own_a = {24'd0, b1m}; own_b = {1'd0, z1}; end
            S_SB2: begin own_a = {24'd0, b2m}; own_b = {1'd0, z2}; end
            S_SC0: begin own_a = {8'd0, c0m}; own_b = {1'd0, z0}; end
            S_SC1: begin own_a = {8'd0, c1m}; own_b = {1'd0, z1}; end
            S_SC2: begin own_a = {8'd0, c2m}; own_b = {1'd0, z2}; end
            // Full magnitude, no truncating slice -- the earlier bug
            // (hardcoded [32:0], 33 bits) silently dropped Sc's bit 33
            // whenever |Sc| exceeded 2**33, caught by this module's own
            // parity test against triangles with real (not adversarial)
            // c_i values.
            S_SCALE_A: begin own_a = Sa_abs; own_b = {1'd0, recip_y}; end
            S_SCALE_B: begin own_a = Sb_abs; own_b = {1'd0, recip_y}; end
            S_SCALE_C: begin own_a = Sc_abs; own_b = {1'd0, recip_y}; end
            default: begin own_a = 40'd0; own_b = 17'd0; end
        endcase
    end

    wire [39:0] shared_a = recip_busy_w ? recip_mult_a : own_a;
    wire [16:0] shared_b = recip_busy_w ? recip_mult_b : own_b;
    spu_shared_mult35 u_mult (.a(shared_a), .b(shared_b), .p(shared_p));

    // term must hold the widest dot-product product without truncation:
    // |c_i*z_i| < 2**36 for real screen-derived c_i (see
    // spu_shared_mult35.v's width comment) -- a 40-bit signed wire
    // covers that with margin, matching Sa/Sb/Sc's own width so the
    // accumulation additions below need no further extension.
    wire signed [39:0] term = $signed({3'b0, shared_p[36:0]});

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state)
                S_IDLE: if (start) state <= S_SA0;
                S_SA0: begin Sa <= a0[15] ? -term : term; state <= S_SA1; end
                S_SA1: begin Sa <= a1[15] ? (Sa - term) : (Sa + term); state <= S_SA2; end
                S_SA2: begin Sa <= a2[15] ? (Sa - term) : (Sa + term); state <= S_SB0; end
                S_SB0: begin Sb <= b0[15] ? -term : term; state <= S_SB1; end
                S_SB1: begin Sb <= b1[15] ? (Sb - term) : (Sb + term); state <= S_SB2; end
                S_SB2: begin Sb <= b2[15] ? (Sb - term) : (Sb + term); state <= S_SC0; end
                S_SC0: begin Sc <= c0[31] ? -term : term; state <= S_SC1; end
                S_SC1: begin Sc <= c1[31] ? (Sc - term) : (Sc + term); state <= S_SC2; end
                S_SC2: begin Sc <= c2[31] ? (Sc - term) : (Sc + term); state <= S_RECIP_START; end
                S_RECIP_START: state <= S_RECIP_WAIT;
                S_RECIP_WAIT: if (recip_done) begin
                    recip_y <= recip_y_out;
                    recip_exp <= recip_exp_out;
                    state <= S_SCALE_A;
                end
                S_SCALE_A: begin
                    A_z <= (Sa[39] ^ d_sign) ? -$signed({16'd0, shared_p}) : $signed({16'd0, shared_p});
                    state <= S_SCALE_B;
                end
                S_SCALE_B: begin
                    B_z <= (Sb[39] ^ d_sign) ? -$signed({16'd0, shared_p}) : $signed({16'd0, shared_p});
                    state <= S_SCALE_C;
                end
                S_SCALE_C: begin
                    C_z <= (Sc[39] ^ d_sign) ? -$signed({16'd0, shared_p}) : $signed({16'd0, shared_p});
                    state <= S_DONE;
                end
                S_DONE: begin
                    frac_bits <= recip_exp;
                    done <= 1'b1;
                    state <= S_IDLE;
                end
                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
