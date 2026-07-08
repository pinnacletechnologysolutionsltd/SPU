`timescale 1ns / 1ps

// spu13_series_stream.v — Hyper-Catalan series root over J₂ = A31[ε]/(ε³)
//
// Static-ROM evaluator.  26 base products sequenced by a global counter.
// No runtime window arithmetic, no while-loops.
//
// Sign convention: c₁ is negated at input (paper's 0 = c₀ − c₁x + …).
// Product schedule in doc/SERIES_STREAM_CONTROLLER.md §4.

module spu13_series_stream (
    input  wire         clk, rst_n, start,
    input  wire [31:0]  c0_o0_z0, c0_o0_z1, c0_o0_z2, c0_o0_z3,
    input  wire [31:0]  c0_o1_z0, c0_o1_z1, c0_o1_z2, c0_o1_z3,
    input  wire [31:0]  c0_o2_z0, c0_o2_z1, c0_o2_z2, c0_o2_z3,
    input  wire [31:0]  c1_o0_z0, c1_o0_z1, c1_o0_z2, c1_o0_z3,
    input  wire [31:0]  c1_o1_z0, c1_o1_z1, c1_o1_z2, c1_o1_z3,
    input  wire [31:0]  c1_o2_z0, c1_o2_z1, c1_o2_z2, c1_o2_z3,
    input  wire [31:0]  c2_o0_z0, c2_o0_z1, c2_o0_z2, c2_o0_z3,
    input  wire [31:0]  c2_o1_z0, c2_o1_z1, c2_o1_z2, c2_o1_z3,
    input  wire [31:0]  c2_o2_z0, c2_o2_z1, c2_o2_z2, c2_o2_z3,
    output reg  [31:0]  x_o0_z0, x_o0_z1, x_o0_z2, x_o0_z3,
    output reg  [31:0]  x_o1_z0, x_o1_z1, x_o1_z2, x_o1_z3,
    output reg  [31:0]  x_o2_z0, x_o2_z1, x_o2_z2, x_o2_z3,
    output reg          done, err_singular,
    output wire         busy,
    output reg          inv_start,
    output reg  [31:0]  inv_z0, inv_z1, inv_z2, inv_z3,
    input  wire [31:0]  inv_r0, inv_r1, inv_r2, inv_r3,
    input  wire         inv_done, inv_flags_v,
    output reg          mult_start,
    output reg  [31:0]  mult_a0, mult_a1, mult_a2, mult_a3,
    output reg  [31:0]  mult_b0, mult_b1, mult_b2, mult_b3,
    input  wire [31:0]  mult_r0, mult_r1, mult_r2, mult_r3,
    input  wire         mult_done
);
    localparam P = 32'h7FFFFFFF;
    localparam N_PRODS = 26, LAST_PROD = 5'd25;
    localparam ST_IDLE=3'd0, ST_INV=3'd1, ST_PROD_L=3'd2, ST_PROD_W=3'd3,
               ST_DISP=3'd4, ST_FINAL=3'd5;
    reg [2:0] state;
    reg [4:0] pctr;
    reg [31:0] rf [0:15][0:3], partial [0:3], acc [0:2][0:3];
    reg [31:0] bypass [0:3];
    reg [3:0]  bypass_idx; reg bypass_valid;
    reg [3:0] srcA[0:N_PRODS-1], srcB[0:N_PRODS-1], dest[0:N_PRODS-1];
    reg [1:0] ops[0:N_PRODS-1];
    reg [3:0] spec[0:N_PRODS-1];
    integer i, comp;

    function [31:0] add; input [31:0] x,y; reg [32:0] s;
        begin s={1'b0,x}+{1'b0,y}; add=(s>=P)?(s-P):s[31:0]; end endfunction
    function [31:0] sub; input [31:0] x,y;
        begin sub=(x>=y)?(x-y):(x+P-y); end endfunction
    function [31:0] neg; input [31:0] x;
        begin neg=(x==0)?0:(P-x); end endfunction

    // Done-coupled busy (scoreboard discipline): high from start
    // acceptance until the cycle done pulses.
    assign busy = (state != ST_IDLE);

    initial begin
        // 0-5: jet_inv scalars → rf[5..10]
        srcA[0]=2; srcB[0]=2; ops[0]=1; dest[0]=5; spec[0]=0;
        srcA[1]=5; srcB[1]=2; ops[1]=1; dest[1]=6; spec[1]=0;
        srcA[2]=12; srcB[2]=5; ops[2]=1; dest[2]=7; spec[2]=0;
        srcA[3]=12; srcB[3]=12; ops[3]=1; dest[3]=8; spec[3]=0;
        srcA[4]=8; srcB[4]=6; ops[4]=1; dest[4]=9; spec[4]=0;
        srcA[5]=13; srcB[5]=5; ops[5]=1; dest[5]=10; spec[5]=4'b0001;
        // 6-11: ci² (dense)
        srcA[6]=2; srcB[6]=2; ops[6]=1; dest[6]=5; spec[6]=0;
        srcA[7]=2; srcB[7]=3; ops[7]=0; dest[7]=0; spec[7]=0;
        srcA[8]=3; srcB[8]=2; ops[8]=1; dest[8]=6; spec[8]=0;
        srcA[9]=2; srcB[9]=4; ops[9]=0; dest[9]=0; spec[9]=0;
        srcA[10]=3; srcB[10]=3; ops[10]=0; dest[10]=0; spec[10]=0;
        srcA[11]=4; srcB[11]=2; ops[11]=1; dest[11]=7; spec[11]=0;
        // 12-17: ci³ (dense)
        srcA[12]=5; srcB[12]=2; ops[12]=1; dest[12]=8; spec[12]=0;
        srcA[13]=5; srcB[13]=3; ops[13]=0; dest[13]=0; spec[13]=0;
        srcA[14]=6; srcB[14]=2; ops[14]=1; dest[14]=9; spec[14]=0;
        srcA[15]=5; srcB[15]=4; ops[15]=0; dest[15]=0; spec[15]=0;
        srcA[16]=6; srcB[16]=3; ops[16]=0; dest[16]=0; spec[16]=0;
        srcA[17]=7; srcB[17]=2; ops[17]=1; dest[17]=10; spec[17]=0;
        // 18: c0²
        srcA[18]=12; srcB[18]=12; ops[18]=1; dest[18]=14; spec[18]=0;
        // 19: C_m staging for term0's eps^2 leg only — 1×c0[2] → rf[6].
        // (The eps^1 leg reads c0[1] straight from rf[12] at product 20;
        // a 1×c0[1] staging product would never be read.)
        srcA[19]=1; srcB[19]=13; ops[19]=1; dest[19]=6; spec[19]=0;
        // 20-22: term0×ci  (c0[1] from rf[12])
        srcA[20]=12; srcB[20]=2; ops[20]=1; dest[20]=5; spec[20]=0;
        srcA[21]=12; srcB[21]=3; ops[21]=0; dest[21]=0; spec[21]=0;
        srcA[22]=6; srcB[22]=2; ops[22]=1; dest[22]=6; spec[22]=4'b0100;
        // 23-25: term1
        srcA[23]=1; srcB[23]=14; ops[23]=1; dest[23]=7; spec[23]=0;
        srcA[24]=7; srcB[24]=8; ops[24]=1; dest[24]=7; spec[24]=0;
        srcA[25]=7; srcB[25]=15; ops[25]=1; dest[25]=7; spec[25]=4'b1000;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state<=ST_IDLE; pctr<=0; done<=0; err_singular<=0; inv_start<=0; mult_start<=0;
            bypass_valid=0; bypass_idx=0;
            for(i=0;i<16;i=i+1) for(comp=0;comp<4;comp=comp+1) rf[i][comp]<=0;
            for(comp=0;comp<4;comp=comp+1) begin partial[comp]<=0; bypass[comp]<=0; end
            for(i=0;i<3;i=i+1) for(comp=0;comp<4;comp=comp+1) acc[i][comp]<=0;
            x_o0_z0<=0;x_o0_z1<=0;x_o0_z2<=0;x_o0_z3<=0;
            x_o1_z0<=0;x_o1_z1<=0;x_o1_z2<=0;x_o1_z3<=0;
            x_o2_z0<=0;x_o2_z1<=0;x_o2_z2<=0;x_o2_z3<=0;
        end else case(state)
            ST_IDLE: begin done<=0; err_singular<=0;
                if(start) begin
                    rf[1][0]<=32'd1;
                    rf[11][0]<=c0_o0_z0;rf[11][1]<=c0_o0_z1;rf[11][2]<=c0_o0_z2;rf[11][3]<=c0_o0_z3;
                    rf[12][0]<=c0_o1_z0;rf[12][1]<=c0_o1_z1;rf[12][2]<=c0_o1_z2;rf[12][3]<=c0_o1_z3;
                    rf[13][0]<=c0_o2_z0;rf[13][1]<=c0_o2_z1;rf[13][2]<=c0_o2_z2;rf[13][3]<=c0_o2_z3;
                    rf[15][0]<=c2_o0_z0;rf[15][1]<=c2_o0_z1;rf[15][2]<=c2_o0_z2;rf[15][3]<=c2_o0_z3;
                    for(i=0;i<3;i=i+1) for(comp=0;comp<4;comp=comp+1) acc[i][comp]<=0;
                    inv_z0<=neg(c1_o0_z0);inv_z1<=neg(c1_o0_z1);inv_z2<=neg(c1_o0_z2);inv_z3<=neg(c1_o0_z3);
                    inv_start<=1'b1; state<=ST_INV;
                end
            end
            ST_INV: begin inv_start<=0;
                if(inv_done) begin
                    if(inv_flags_v) begin err_singular<=1; state<=ST_IDLE; done<=1; end
                    else begin
                        rf[2][0]<=inv_r0;rf[2][1]<=inv_r1;rf[2][2]<=inv_r2;rf[2][3]<=inv_r3;
                        rf[12][0]<=neg(c1_o1_z0);rf[12][1]<=neg(c1_o1_z1);rf[12][2]<=neg(c1_o1_z2);rf[12][3]<=neg(c1_o1_z3);
                        rf[13][0]<=neg(c1_o2_z0);rf[13][1]<=neg(c1_o2_z1);rf[13][2]<=neg(c1_o2_z2);rf[13][3]<=neg(c1_o2_z3);
                        pctr<=0; for(comp=0;comp<4;comp=comp+1) partial[comp]<=0;
                        mult_a0<=inv_r0;mult_a1<=inv_r1;mult_a2<=inv_r2;mult_a3<=inv_r3;
                        mult_b0<=inv_r0;mult_b1<=inv_r1;mult_b2<=inv_r2;mult_b3<=inv_r3;
                        mult_start<=1'b1; state<=ST_PROD_L;
                    end
                end
            end
            ST_PROD_L: begin mult_start<=0; state<=ST_PROD_W; end
            ST_PROD_W: if(mult_done) begin
                partial[0]<=add(partial[0],mult_r0);partial[1]<=add(partial[1],mult_r1);
                partial[2]<=add(partial[2],mult_r2);partial[3]<=add(partial[3],mult_r3);
                state<=ST_DISP;
            end
            ST_DISP: begin
                if(spec[pctr][0]) begin
                    rf[3][0]<=neg(rf[7][0]);rf[3][1]<=neg(rf[7][1]);rf[3][2]<=neg(rf[7][2]);rf[3][3]<=neg(rf[7][3]);
                    rf[4][0]<=sub(rf[9][0],partial[0]);rf[4][1]<=sub(rf[9][1],partial[1]);
                    rf[4][2]<=sub(rf[9][2],partial[2]);rf[4][3]<=sub(rf[9][3],partial[3]);
                    rf[12][0]<=c0_o1_z0;rf[12][1]<=c0_o1_z1;rf[12][2]<=c0_o1_z2;rf[12][3]<=c0_o1_z3;
                    rf[13][0]<=c0_o2_z0;rf[13][1]<=c0_o2_z1;rf[13][2]<=c0_o2_z2;rf[13][3]<=c0_o2_z3;
                end
                if(spec[pctr][2]) begin
                    acc[1][0]<=add(acc[1][0],rf[5][0]);acc[1][1]<=add(acc[1][1],rf[5][1]);
                    acc[1][2]<=add(acc[1][2],rf[5][2]);acc[1][3]<=add(acc[1][3],rf[5][3]);
                    acc[2][0]<=add(acc[2][0],partial[0]);acc[2][1]<=add(acc[2][1],partial[1]);
                    acc[2][2]<=add(acc[2][2],partial[2]);acc[2][3]<=add(acc[2][3],partial[3]);
                end
                if(spec[pctr][3]) begin
                    acc[2][0]<=add(acc[2][0],partial[0]);acc[2][1]<=add(acc[2][1],partial[1]);
                    acc[2][2]<=add(acc[2][2],partial[2]);acc[2][3]<=add(acc[2][3],partial[3]);
                    state<=ST_FINAL;
                end
                if(ops[pctr]==2'd1) begin
                    rf[dest[pctr]][0]<=partial[0];rf[dest[pctr]][1]<=partial[1];
                    rf[dest[pctr]][2]<=partial[2];rf[dest[pctr]][3]<=partial[3];
                    bypass[0]=partial[0];bypass[1]=partial[1];bypass[2]=partial[2];bypass[3]=partial[3];
                    bypass_idx=dest[pctr]; bypass_valid=1;
                    for(comp=0;comp<4;comp=comp+1) partial[comp]<=0;
                end else bypass_valid=0;
                if(state==ST_DISP && pctr<LAST_PROD) begin
                    pctr<=pctr+5'd1;
                    if(bypass_valid && bypass_idx==srcA[pctr+1]) begin
                        mult_a0=bypass[0];mult_a1=bypass[1];mult_a2=bypass[2];mult_a3=bypass[3];
                    end else begin
                        mult_a0=rf[srcA[pctr+1]][0];mult_a1=rf[srcA[pctr+1]][1];
                        mult_a2=rf[srcA[pctr+1]][2];mult_a3=rf[srcA[pctr+1]][3];
                    end
                    if(bypass_valid && bypass_idx==srcB[pctr+1]) begin
                        mult_b0=bypass[0];mult_b1=bypass[1];mult_b2=bypass[2];mult_b3=bypass[3];
                    end else begin
                        mult_b0=rf[srcB[pctr+1]][0];mult_b1=rf[srcB[pctr+1]][1];
                        mult_b2=rf[srcB[pctr+1]][2];mult_b3=rf[srcB[pctr+1]][3];
                    end
                    mult_start<=1'b1; state<=ST_PROD_L;
                end
            end
            ST_FINAL: begin
                x_o0_z0<=acc[0][0];x_o0_z1<=acc[0][1];x_o0_z2<=acc[0][2];x_o0_z3<=acc[0][3];
                x_o1_z0<=acc[1][0];x_o1_z1<=acc[1][1];x_o1_z2<=acc[1][2];x_o1_z3<=acc[1][3];
                x_o2_z0<=acc[2][0];x_o2_z1<=acc[2][1];x_o2_z2<=acc[2][2];x_o2_z3<=acc[2][3];
                done<=1; state<=ST_IDLE;
            end
            default: state<=ST_IDLE;
        endcase
    end
endmodule
