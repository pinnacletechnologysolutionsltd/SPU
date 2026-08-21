// fpga_chain_arith.vh — Q2.40 fixed-point helper functions for fpga_chain.v
// (contract_regen_stageB_2026-08-20.md). `include`d verbatim; not a
// standalone compilation unit. Split out of fpga_chain.v for the 150-line
// Lithic cap (AGENTS.md) — pure combinational functions, no state.

// ---- Q2.40 constants ----
localparam [41:0] ONE   = 42'sd1099511627776;   // 1.0 = 2^40
localparam [41:0] C2_3  = 42'sd733007751850;    //  2/3
localparam [41:0] CN1_3 = -42'sd366503875925;   // -1/3

function [4:0] abs_bitlen;
    input [31:0] v;
    reg [31:0] av;
    integer i;
    begin
        av = (v[31] ? (~v + 32'd1) : v);
        abs_bitlen = 5'd1;
        for (i = 31; i >= 0; i = i - 1) begin
            if (av[i]) begin
                abs_bitlen = i + 1;
                i = -1;
            end
        end
    end
endfunction

function [4:0] load_exp;
    input [31:0] a, b, c, d;
    reg [4:0] ba, bb, bc, bd;
    begin
        ba = abs_bitlen(a); bb = abs_bitlen(b);
        bc = abs_bitlen(c); bd = abs_bitlen(d);
        load_exp = 0;
        if (ba > 3 && ba - 3 > load_exp) load_exp = ba - 3;
        if (bb > 3 && bb - 3 > load_exp) load_exp = bb - 3;
        if (bc > 3 && bc - 3 > load_exp) load_exp = bc - 3;
        if (bd > 3 && bd - 3 > load_exp) load_exp = bd - 3;
    end
endfunction

// v (signed 32-bit) -> Q2.40 integer at scale 2^-(2+sh):
// field_int = v * 2^(38 - sh)  (v*2^-2*2^-sh in Q2.40 units)
function [41:0] ashr;
    input [31:0] v;
    input [5:0]  sh;
    reg [63:0] ext;
    reg [41:0] v42;
    begin
        ext = {{32{v[31]}}, v};
        v42 = ext[41:0];
        if (sh <= 38)
            ashr = v42 << (38 - sh);
        else
            ashr = $signed(v42) >>> (sh - 38);
    end
endfunction

// Q2.40 multiply: keep Q2.40 (p >> 40)
function [41:0] mul40;
    input [41:0] x;
    input [41:0] y;
    reg [83:0] p;
    begin
        p = {{42{x[41]}}, x} * {{42{y[41]}}, y};
        mul40 = $signed(p) >>> 40;
    end
endfunction

// (x - y) / 2 in Q2.40
function [41:0] diff_half;
    input [41:0] x;
    input [41:0] y;
    reg [83:0] p;
    begin
        p = {{42{x[41]}}, x} - {{42{y[41]}}, y};
        diff_half = $signed(p) >>> 1;
    end
endfunction

// (F*B + H*C + G*D) / 2 in Q2.40 (ROTC circulant component, pre-cos)
function [41:0] circ_half;
    input [41:0] F; input [41:0] B;
    input [41:0] H; input [41:0] C;
    input [41:0] G; input [41:0] D;
    reg [83:0] p;
    begin
        p = {{42{F[41]}}, F} * {{42{B[41]}}, B}
          + {{42{H[41]}}, H} * {{42{C[41]}}, C}
          + {{42{G[41]}}, G} * {{42{D[41]}}, D};
        circ_half = $signed(p) >>> 41;   // >>40 then /2
    end
endfunction

// re-scale a field from scale m_old to scale m_new (arithmetic shift)
function [41:0] rescale;
    input [41:0] f;
    input [9:0]  m_old;
    input [9:0]  m_new;
    reg [83:0] e;
    begin
        e = {{42{f[41]}}, f};
        if (m_new >= m_old)
            rescale = $signed(e) >>> (m_new - m_old);
        else
            rescale = $signed(e) << (m_old - m_new);
    end
endfunction

// cos(dphi_cfg) in Q2.40 = 1 - t^2/2 + t^4/24, t = dphi*2^-16
function [41:0] cos_const;
    input [7:0] d;
    reg [31:0] d2;
    reg [63:0] d4;
    begin
        d2 = d * d;
        d4 = d2 * d2;
        cos_const = ONE - ({{24{d2[31]}}, d2, 7'b0})
                   + ((d4 * 64'd2731) >> 40);   // t^4/24, t=d*2^-16: d4*2^-24/24
    end
endfunction

// ROTC circulant coefficients (angles 0-5, A invariant)
function [41:0] fgh;
    input [5:0] ang;
    input [1:0] sel;   // 0=F 1=G 2=H
    begin
        case ({ang, sel})
            {6'd0, 2'd0}: fgh = ONE;   {6'd0, 2'd1}: fgh = 0; {6'd0, 2'd2}: fgh = 0;
            {6'd1, 2'd0}: fgh = C2_3;  {6'd1, 2'd1}: fgh = C2_3; {6'd1, 2'd2}: fgh = CN1_3;
            {6'd2, 2'd0}: fgh = 0;     {6'd2, 2'd1}: fgh = ONE; {6'd2, 2'd2}: fgh = 0;
            {6'd3, 2'd0}: fgh = CN1_3; {6'd3, 2'd1}: fgh = C2_3; {6'd3, 2'd2}: fgh = C2_3;
            {6'd4, 2'd0}: fgh = C2_3;  {6'd4, 2'd1}: fgh = CN1_3; {6'd4, 2'd2}: fgh = C2_3;
            {6'd5, 2'd0}: fgh = 0;     {6'd5, 2'd1}: fgh = 0; {6'd5, 2'd2}: fgh = ONE;
            default: fgh = 0;
        endcase
    end
endfunction
