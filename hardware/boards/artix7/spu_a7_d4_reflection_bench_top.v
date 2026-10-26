// Matched route harness for the D4 reflection microarchitecture comparison.
// Inputs come from identical changing on-chip state in both candidates; LEDs
// expose lane parities and invalid status so the complete output remains live.
module spu_a7_d4_reflection_bench_top #(
    parameter integer GENERIC_REFLECTION = 0
) (
    input  wire       clk_100mhz,
    output reg  [4:0] led_out = 5'b0
);
    reg [63:0] stimulus = 64'hd4_2026_89ab_cdef;
    reg [1:0] root_sel = 2'b0;
    wire [63:0] reflected;
    wire invalid_flag;
    (* keep = "true" *) wire [63:0] observed_reflection = reflected;

    always @(posedge clk_100mhz) begin
        stimulus <= {stimulus[62:0], stimulus[63] ^ stimulus[62] ^
                     stimulus[60] ^ stimulus[59]};
        root_sel <= root_sel + 2'd1;
        led_out <= {invalid_flag, ^observed_reflection[63:48],
                    ^observed_reflection[47:32],
                    ^observed_reflection[31:16],
                    ^observed_reflection[15:0]};
    end

    generate
        if (GENERIC_REFLECTION != 0) begin : g_generic
            spu_d4_reflection_generic reflection (
                .in_v(stimulus), .root_sel(root_sel),
                .out_v(reflected), .invalid_flag(invalid_flag));
        end else begin : g_specialized
            spu_d4_reflection_unit reflection (
                .in_v(stimulus), .root_sel(root_sel),
                .out_v(reflected), .invalid_flag(invalid_flag));
        end
    endgenerate
endmodule
