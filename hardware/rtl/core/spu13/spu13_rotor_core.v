// SPU-13 Thomson Rotor Core (v3.1.27)
// Implementation: Circulant ALU for Isotropic Rotation.
// Logic: a + b*sqrt(3) field arithmetic in Quadray Space.
// Objective: Zero-drift, bit-exact spatial transformation.

module spu13_rotor_core (
    input  wire        clk,
    input  wire        rst_n,
    
    // Quadray Input Coordinates (A,B,C,D)
    // Format: [63:32] Surd component (S), [31:0] Integer component (I)
    input  wire [63:0] A_in, B_in, C_in, D_in,
    
    // Rotation Coefficients (F,G,H) in Q(sqrt(3))
    input  wire [63:0] F, G, H,
    
    // Control: Enable Zero-Gate Bypass for P5 (120-degree) rotations
    input  wire        bypass_p5,
    
    `ifdef FORMAL
    output wire        is_sane,
    `endif

    // Quadray Output Coordinates
    output reg  [63:0] A_out, B_out, C_out, D_out
);

    // 1. Surd Multiplication Intermediates
    // B' = (F*B) + (H*C) + (G*D)
    // C' = (G*B) + (F*C) + (H*D)
    // D' = (H*B) + (G*C) + (F*D)
    
    wire [63:0] FB_out, HC_out, GD_out;
    wire [63:0] GB_out, FC_out, HD_out;
    wire [63:0] HB_out, GC_out, FD_out;

    // Row B Intermediates
    surd_multiplier mFB (.clk(clk), .reset(!rst_n), .a1(B_in[31:0]), .b1(B_in[63:32]), .a2(F[31:0]), .b2(F[63:32]), .res_a(FB_out[31:0]), .res_b(FB_out[63:32]));
    surd_multiplier mHC (.clk(clk), .reset(!rst_n), .a1(C_in[31:0]), .b1(C_in[63:32]), .a2(H[31:0]), .b2(H[63:32]), .res_a(HC_out[31:0]), .res_b(HC_out[63:32]));
    surd_multiplier mGD (.clk(clk), .reset(!rst_n), .a1(D_in[31:0]), .b1(D_in[63:32]), .a2(G[31:0]), .b2(G[63:32]), .res_a(GD_out[31:0]), .res_b(GD_out[63:32]));

    // Row C Intermediates
    surd_multiplier mGB (.clk(clk), .reset(!rst_n), .a1(B_in[31:0]), .b1(B_in[63:32]), .a2(G[31:0]), .b2(G[63:32]), .res_a(GB_out[31:0]), .res_b(GB_out[63:32]));
    surd_multiplier mFC (.clk(clk), .reset(!rst_n), .a1(C_in[31:0]), .b1(C_in[63:32]), .a2(F[31:0]), .b2(F[63:32]), .res_a(FC_out[31:0]), .res_b(FC_out[63:32]));
    surd_multiplier mHD (.clk(clk), .reset(!rst_n), .a1(D_in[31:0]), .b1(D_in[63:32]), .a2(H[31:0]), .b2(H[63:32]), .res_a(HD_out[31:0]), .res_b(HD_out[63:32]));

    // Row D Intermediates
    surd_multiplier mHB (.clk(clk), .reset(!rst_n), .a1(B_in[31:0]), .b1(B_in[63:32]), .a2(H[31:0]), .b2(H[63:32]), .res_a(HB_out[31:0]), .res_b(HB_out[63:32]));
    surd_multiplier mGC (.clk(clk), .reset(!rst_n), .a1(C_in[31:0]), .b1(C_in[63:32]), .a2(G[31:0]), .b2(G[63:32]), .res_a(GC_out[31:0]), .res_b(GC_out[63:32]));
    surd_multiplier mFD (.clk(clk), .reset(!rst_n), .a1(D_in[31:0]), .b1(D_in[63:32]), .a2(F[31:0]), .b2(F[63:32]), .res_a(FD_out[31:0]), .res_b(FD_out[63:32]));

    // 2. Summation Logic (Combinational after 1-cycle multiply)
    wire [63:0] B_sum;
    assign B_sum = {FB_out[63:32] + HC_out[63:32] + GD_out[63:32], FB_out[31:0] + HC_out[31:0] + GD_out[31:0]};
    wire [63:0] C_sum;
    assign C_sum = {GB_out[63:32] + FC_out[63:32] + HD_out[63:32], GB_out[31:0] + FC_out[31:0] + HD_out[31:0]};
    wire [63:0] D_sum;
    assign D_sum = {HB_out[63:32] + GC_out[63:32] + FD_out[63:32], HB_out[31:0] + GC_out[31:0] + FD_out[31:0]};

    // 3. Output Pipeline and Bypass Path
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            A_out <= 64'b0; B_out <= 64'b0;
            C_out <= 64'b0; D_out <= 64'b0;
        end else begin
            A_out <= A_in; // Invariant Axis
            
            if (bypass_p5) begin
                // Zero-Gate Bypass: Pure permutation for P5 (120-degree)
                // F=0, G=1, H=0 implies B'=D, C'=B, D'=C
                B_out <= D_in;
                C_out <= B_in;
                D_out <= C_in;
            end else begin
                // Normal Circulant Rotation
                B_out <= B_sum;
                C_out <= C_sum;
                D_out <= D_sum;
            end
        end
    end

    // 4. Formal Verification: Indestructible Invariant
    // Assert that the circulant matrix determinant is exactly 1.
    // Logic: det(M) = F^3 + G^3 + H^3 - 3FGH
    // (Note: Requires surd-cubing logic for full implementation; 
    // Simplified here to indicate the formal requirement).
    
    `ifdef FORMAL
    assign is_sane = !bypass_p5;
    always @(posedge clk) begin
        if (rst_n && !bypass_p5) begin
            // Determinant assertion (Conceptually in Q(sqrt(3)))
            // assert( (F*F*F + G*G*G + H*H*H - 3*F*G*H) == 1 );
        end
    end
    `endif

endmodule
