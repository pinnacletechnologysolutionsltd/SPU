// spu4_dream_sequencer.v (v1.0 - Sentinel Autonomy)
// Objective: 16-entry Instruction Sequencer for Autonomous SPU-4.
// Architecture: 4-bit PC, 16-bit Instructions.

module spu4_dream_sequencer (
    input  wire        clk,
    input  wire        rst_n,
    
    // Programming Interface (From RP2040 PIO or Boot Master)
    input  wire        prog_en,
    input  wire [3:0]  prog_addr,
    input  wire [15:0] prog_data,
    input  wire        inhale_done,
    
    // ALU Interface
    output reg  [15:0] current_instr,
    output reg         alu_start,
    input  wire        alu_done,
    output wire        alu_hush, // Clock gating signal
    
    // Status
    output reg  [3:0]  pc
);

    // 1. Dream Buffer (16 x 16-bit BRAM)
    reg [15:0] dream_buffer [0:15];
    
    reg [2:0] state;
    localparam S_BOOT   = 3'd0;
    localparam S_INHALE = 3'd1;
    localparam S_DREAM  = 3'd2;

    assign alu_hush = (state == S_DREAM) && (current_instr[11]); // Bit 11 is Soft-Start/Hush

    // 2. Program Counter & Fetch
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc <= 4'h0;
            current_instr <= 16'h0;
            alu_start <= 1'b0;
            state <= S_BOOT;
        end else begin
            case (state)
                S_BOOT: begin
                    if (prog_en) state <= S_INHALE;
                    else if (inhale_done) state <= S_DREAM;
                end
                
                S_INHALE: begin
                    dream_buffer[prog_addr] <= prog_data;
                    if (!prog_en) state <= S_BOOT;
                end
                
                S_DREAM: begin
                    current_instr <= dream_buffer[pc];
                    
                    // Lithic-L Lite:
                    // 0x2XXX = ROTATE
                    // 0x3XXX = GOTO n
                    
                    if (current_instr[15:12] == 4'h2 && !alu_start && !alu_done) begin
                        alu_start <= 1'b1;
                    end else if (alu_done && alu_start) begin
                        alu_start <= 1'b0;
                        pc <= pc + 4'h1;
                    end else if (current_instr[15:12] == 4'h3) begin
                        pc <= current_instr[3:0];
                    end else if (current_instr[15:12] != 4'h2) begin
                        pc <= pc + 4'h1;
                    end
                end
            endcase
        end
    end

endmodule
