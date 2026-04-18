// SPU-13 Isotropic Annealer (v2.9.17)
// Function: Injects sub-Planckian Golden Ratio perturbations to prevent 'Lattice Lock'.
// Logic: XORs the LSBs with a Fibonacci-LFSR sequence.

module spu_annealer (
    input  wire         clk,
    input  wire         reset,
    input  wire         enable,       // OP_PERTURB trigger
    input  wire [831:0] reg_in,
    output wire [831:0] reg_out
);

    // 1. Fibonacci LFSR (The 'Golden Noise' Generator)
    // Produces a deterministic, aperiodic pulse based on the Golden Ratio.
    reg [12:0] lfsr;
    always @(posedge clk or posedge reset) begin
        if (reset) lfsr <= 13'h1FFF;
        else       lfsr <= {lfsr[11:0], lfsr[12] ^ lfsr[7] ^ lfsr[4] ^ lfsr[2]};
    end

    // 2. Sub-Planckian Perturbation
    // We only perturb the Least Significant Bits (LSBs) of the ABCD lanes.
    // This provides 'Thermal Jitter' to shake the system out of grid-snapping.
    genvar i;
    generate
        for (i = 0; i < 13; i = i + 1) begin : perturb_lanes
            assign reg_out[i*64 +: 64] = enable ? (reg_in[i*64 +: 64] ^ {63'b0, lfsr[i]}) 
                                                : reg_in[i*64 +: 64];
        end
    endgenerate

endmodule
