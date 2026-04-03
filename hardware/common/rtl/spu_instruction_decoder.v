// spu_instruction_decoder.v
module spu_instruction_decoder (
    input  wire [12:0] instr,
    output wire [2:0]  opcode,
    output wire [4:0]  reg_addr,
    output wire [3:0]  basis,
    output wire        snap_en,
    output wire        janus_mode
);
    assign snap_en = instr[12];
    assign opcode  = instr[11:9];
    assign reg_addr = instr[8:4];
    assign basis = instr[3:0];
    assign janus_mode = !instr[12];
endmodule
