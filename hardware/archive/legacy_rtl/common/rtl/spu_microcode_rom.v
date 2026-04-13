// spu_microcode_rom.v
module spu_microcode_rom (
    input [7:0] opcode,
    input sync_alert,
    output reg [17:0] delta_out
);
    reg [23:0] rom_data [0:255];

    initial begin
        $readmemh("spu_init.mem", rom_data);
    end

    always @(*) begin
        // Provide the lower 18 bits of the BRAM anchor to the processor pipeline
        delta_out = rom_data[opcode][17:0];
    end
endmodule
