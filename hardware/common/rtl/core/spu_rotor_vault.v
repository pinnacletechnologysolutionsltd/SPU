// spu_rotor_vault.v (v1.1 - Sovereign SQR Storage)
// Objective: Efficient storage for 13 prime-weighted rotors.
// Optimization: Uses iCE40 256Kbit SPRAM (Mapped to axis_ptr).

module spu_rotor_vault (
    input  wire        clk,
    input  wire [3:0]  addr,    // axis_ptr (0-12)
    output reg  [31:0] rotor_out // {Ra, Rb} - SQR v3.1
);

    reg [31:0] vault_data [0:31];

    initial begin
        $readmemh("spu_rotor_vault.mem", vault_data);
    end

    always @(posedge clk) begin
        rotor_out <= vault_data[addr];
    end

endmodule
