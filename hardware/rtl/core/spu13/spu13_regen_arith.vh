// spu13_regen_arith.vh — Q2.40 trim/BQE helper functions for spu13_regen.v
// (contract_regen_stageB_2026-08-20.md). `include`d verbatim; not a
// standalone compilation unit. Split out of spu13_regen.v for the
// 150-line Lithic cap (AGENTS.md) — pure combinational functions, no state.

// Q2.40 trim (Taylor 1/cos(t), t = ak*2^-16) + BQE recovery
function [41:0] trim_const;
    input [15:0] ak;
    reg [31:0] ak2;
    reg [63:0] ak4;
    begin
        ak2 = ak * ak;
        ak4 = ak2 * ak2;
        trim_const = 42'sd1099511627776    // 1.0 = 2^40
                   + ({{24{ak2[31]}}, ak2, 7'b0})
                   + ((ak4 * 64'd13653) >> 40);  // 5*t^4/24, t=ak*2^-16
    end
endfunction

// BQE: v = round(meas * trim * 2^(m+2)) ; meas, trim in Q2.40
function [31:0] bqe;
    input [41:0] meas;
    input [41:0] trim;
    input [9:0]  m;
    reg [83:0] prod;
    reg signed [83:0] ssum;
    begin
        prod = {{42{meas[41]}}, meas} * {{42{trim[41]}}, trim};
        if (78 >= m) begin
            if (77 >= m) begin
                // arithmetic (sign-extending) shift of the rounded sum;
                // prod is unsigned but the recovered value is signed
                ssum = $signed(prod) + $signed(84'd1 << (77 - m));
                bqe = ssum >>> (78 - m);
            end else
                bqe = $signed(prod) >>> (78 - m);
        end else
            bqe = 0;
    end
endfunction
