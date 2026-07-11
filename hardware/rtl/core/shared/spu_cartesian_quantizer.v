// spu_cartesian_quantizer.v
// Cartesian bridge ingest: S24.8 fixed-point (value * scale) -> packed
// RationalSurd {P[15:0], 16'd0}, round-half-to-even, saturating.
// Contract: docs/CARTESIAN_BRIDGE_SPEC.md §7; oracle:
// software/lib/cartesian_bridge.py quantize_scalar. Floats never exist
// on the fabric — host/southbridge owns any float->S24.8 conversion.
module spu_cartesian_quantizer (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        in_valid,
    input  wire signed [31:0] in_fixed,
    output reg         out_valid,
    output reg  [31:0] out_surd,
    output reg         out_saturated
);

    wire signed [23:0] int24;
    wire        [7:0]  frac;
    wire               round_up;
    wire signed [24:0] rounded;
    wire               sat_hi;
    wire               sat_lo;
    wire signed [15:0] packed_p;

    assign int24 = in_fixed[31:8];
    assign frac = in_fixed[7:0];

    assign round_up = frac[7] & (|frac[6:0] | int24[0]);
    assign rounded = {int24[23], int24} + {{24{1'b0}}, round_up};

    assign sat_hi = (rounded > 25'sd32767);
    assign sat_lo = (rounded < -25'sd32768);

    assign packed_p = sat_hi ? 16'sh7fff :
                      sat_lo ? 16'sh8000 :
                      rounded[15:0];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            out_valid <= 1'b0;
            out_surd <= 32'd0;
            out_saturated <= 1'b0;
        end else begin
            out_valid <= in_valid;
            out_surd <= {packed_p, 16'd0};
            out_saturated <= in_valid & (sat_hi | sat_lo);
        end
    end

endmodule
