// SPU-13 Laminar RAM Translator (v1.0)
// Objective: Fractal RAM Alignment via Bit-Interleaving.
// Logic: Interleave axes {a, b, c} into a single Z-order address.
// Vibe: The End of Memory Fragmentation.

module spu_laminar_ram (
    input  wire [7:0]  q_a, // Quadray Axis A
    input  wire [7:0]  q_b, // Quadray Axis B
    input  wire [7:0]  q_c, // Quadray Axis C
    output wire [23:0] fractal_addr
);

    // Fractal Interleaving: [a7][b7][c7][a6][b6][c6]...[a0][b0][c0]
    assign fractal_addr = {
        q_a[7], q_b[7], q_c[7],
        q_a[6], q_b[6], q_c[6],
        q_a[5], q_b[5], q_c[5],
        q_a[4], q_b[4], q_c[4],
        q_a[3], q_b[3], q_c[3],
        q_a[2], q_b[2], q_c[2],
        q_a[1], q_b[1], q_c[1],
        q_a[0], q_b[0], q_c[0]
    };

endmodule
