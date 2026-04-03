// SPU-1 SIMD Parallel Adder (SADD)
// Performs 8 parallel 32-bit additions across two 256-bit Quadray registers.

module spu_sadd (
    input  [255:0] u,
    input  [255:0] v,
    output [255:0] sum
);

    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : add_lanes
            assign sum[i*32 +: 32] = u[i*32 +: 32] + v[i*32 +: 32];
        end
    endgenerate

endmodule
