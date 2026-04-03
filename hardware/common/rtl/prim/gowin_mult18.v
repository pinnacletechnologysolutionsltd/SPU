// gowin_mult18.v — Gowin DSP wrapper for 18×18 signed multiply
// Abstracts MULT18X18 (GW1N/GW2A), MULT18X18D (GW5A), and ALU54D accumulate.
//
// DEVICE parameter:
//   "GW1N"  — GW1NR-9 (Tang Nano 9K)       — inferred multiply
//   "GW2A"  — GW2A-18  (Tang Primer 20K)    — explicit ALU54D for accumulate path
//   "GW5A"  — GW5A-25  (Tang Primer 25K)    — MULT18X18D (output registered, +1 cycle)
//   "SIM"   — simulation / fallback          — inferred multiply, no vendor cells
//
// All inputs: 18-bit signed (caller sign-extends 16-bit P/Q to 18 bits).
// Product:    36-bit signed (no truncation — caller normalises with >>>16).
// ACCUM mode: when ACCUM=1, output = prev_result + (A*B). Uses ALU54D on GW2A,
//             inferred add on other devices.
//
// CC0 1.0 Universal.

`ifndef GOWIN_MULT18_V
`define GOWIN_MULT18_V

module gowin_mult18 #(
    parameter DEVICE  = "GW5A",  // "GW1N" | "GW2A" | "GW5A" | "SIM"
    parameter ACCUM   = 0        // 1 = accumulate mode (add prev_out to product)
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire        ce,        // clock enable
    input  wire signed [17:0] A,  // multiplicand (sign-extended 16-bit P or Q)
    input  wire signed [17:0] B,  // multiplier
    input  wire signed [35:0] C,  // accumulate addend (used when ACCUM=1)
    output reg  signed [35:0] P   // product (or product+C when ACCUM=1)
);

generate
    // ─────────────────────────────────────────────────────────────────────────
    // GW2A: explicit ALU54D for accumulate path; inferred MULT18X18 otherwise
    // ALU54D pins: A[17:0], B[17:0], C[53:0] → DOUT[53:0]
    // ACCUM=1: DOUT = A*B + C54  →  we use C54 = {18'b0, C[35:0]}
    // ─────────────────────────────────────────────────────────────────────────
    if (DEVICE == "GW2A" && ACCUM == 1) begin : gen_alu54d

        wire signed [53:0] c54   = {{18{C[35]}}, C};
        wire signed [53:0] dout54;

        ALU54D #(
            .AREG(1),  // register A input
            .BREG(1),  // register B input
            .CREG(1),  // register C input
            .PREG(1)   // register product output
        ) u_alu54d (
            .A    (A),
            .B    (B),
            .C    (c54),
            .CLK  (clk),
            .CE   (ce),
            .RESET(~rst_n),
            .DOUT (dout54)
        );

        // Truncate 54-bit result to 36 bits (upper 18 bits are sign extension
        // for our operand range — overflow indicates genuine manifold instability)
        always @(posedge clk or negedge rst_n)
            if (!rst_n) P <= 36'sd0;
            else if (ce) P <= dout54[35:0];

    // ─────────────────────────────────────────────────────────────────────────
    // GW5A: MULT18X18D — registered outputs, 1-cycle latency
    // Synthesis infers MULT18X18D automatically from registered assign.
    // Explicit instantiation avoided: Gowin EDA's mapper is authoritative.
    // ─────────────────────────────────────────────────────────────────────────
    end else if (DEVICE == "GW5A") begin : gen_gw5a

        // Let Gowin EDA infer MULT18X18D from registered multiply.
        // Synthesis constraint: set_multicycle_path -from [get_cells *gen_gw5a*] -to 2
        reg signed [35:0] p_reg;
        always @(posedge clk or negedge rst_n)
            if (!rst_n) p_reg <= 36'sd0;
            else if (ce) p_reg <= A * B;

        always @(posedge clk or negedge rst_n)
            if (!rst_n) P <= 36'sd0;
            else if (ce) P <= (ACCUM) ? p_reg + C : p_reg;

    // ─────────────────────────────────────────────────────────────────────────
    // GW1N / SIM / fallback: inferred combinatorial multiply + optional accum
    // Synthesis maps to MULT18X18 on GW1N. Pure logic in simulation.
    // ─────────────────────────────────────────────────────────────────────────
    end else begin : gen_infer

        always @(posedge clk or negedge rst_n)
            if (!rst_n) P <= 36'sd0;
            else if (ce) P <= (ACCUM) ? (A * B) + C : A * B;

    end
endgenerate

endmodule

`endif // GOWIN_MULT18_V
