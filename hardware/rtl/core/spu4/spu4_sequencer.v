`timescale 1ns / 1ps

// spu4_sequencer.v — Standalone sequencer for SPU-4.
//
// Replaces spu4_dream_sequencer + spu4_boot_master with a clean
// PC-based fetch/decode/execute pipeline.  64-entry × 24-bit program
// memory loaded via SPI or embedded boot ROM.
//
// Pipeline:  FETCH → DECODE → EXECUTE → WRITEBACK
// Each stage is 1 cycle except EXECUTE (multi-cycle for ALU ops).

module spu4_sequencer #(
    parameter MEM_DEPTH = 64,
    parameter ADDR_W    = 6
) (
    input  wire         clk,
    input  wire         rst_n,

    // Program load interface (from SPI or PIO)
    input  wire         prog_we,
    input  wire [ADDR_W-1:0] prog_addr,
    input  wire [23:0]  prog_data,

    // Execution control
    input  wire         run,            // pulse to start execution
    input  wire         sentinel_mode,
    input  wire         piranha_pulse,
    output reg          busy,           // high while executing
    output reg          done,           // pulse on HALT or program end

    // To decoder / ALU pipeline
    output reg  [23:0]  instruction,    // current instruction
    output reg          alu_start,      // pulse to start ALU
    input  wire         alu_done,       // ALU finished
    output reg          reg_we,         // register write enable
    output reg  [2:0]   reg_dest,       // destination register
    output reg  [7:0]   reg_imm,        // immediate value

    // Branch (from decoder comparison)
    input  wire         branch_taken,   // from CMP logic

    // Status
    output reg  [ADDR_W-1:0] pc
);
    // ── Program memory ───────────────────────────────────────────────
    reg [23:0] prog_mem [0:MEM_DEPTH-1];
    reg [23:0] boot_rom [0:3];  // embedded boot: just HALT

    initial begin
        boot_rom[0] = 24'h00_00_00;  // NOP
        boot_rom[1] = 24'h00_00_00;  // NOP
        boot_rom[2] = 24'h00_00_00;  // NOP
        boot_rom[3] = 24'h01_00_00;  // HALT
    end

    // ── Boot state ───────────────────────────────────────────────────
    // boot_done starts high: no boot ROM copy on first clock edge.
    // The probe writes the program via prog_we before asserting run.
    // This avoids a race where boot ROM overwrites the first program write.
    reg boot_done;
    initial boot_done = 1;

    integer bi;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (bi = 0; bi < MEM_DEPTH; bi = bi + 1)
                prog_mem[bi] <= 24'h00_00_00;
        end else if (prog_we) begin
            prog_mem[prog_addr] <= prog_data;
        end
    end

    // ── FSM ──────────────────────────────────────────────────────────
    localparam S_IDLE    = 3'd0;
    localparam S_FETCH   = 3'd1;
    localparam S_EXEC    = 3'd2;
    localparam S_WAIT_ALU= 3'd3;
    localparam S_WB      = 3'd4;
    localparam S_HALT    = 3'd5;

    reg [2:0] state;
    reg [7:0] opcode;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            pc <= 0;
            instruction <= 0;
            alu_start <= 0;
            reg_we <= 0;
            reg_dest <= 0;
            reg_imm <= 0;
            busy <= 0;
            done <= 0;
        end else begin
            // Defaults
            alu_start <= 0;
            reg_we <= 0;
            done <= 0;

            case (state)
                S_IDLE: begin
                    busy <= 0;
                    pc <= 0;
                    if (run) begin
                        busy <= 1;
                        state <= S_FETCH;
                    end
                end

                S_FETCH: begin
                    // Fetch instruction from program memory
                    instruction <= prog_mem[pc];
                    opcode <= prog_mem[pc][23:16];
                    state <= S_EXEC;
                end

                S_EXEC: begin
                    // Decode and execute
                    case (opcode)
                        8'h00: begin  // NOP
                            pc <= pc + 1;
                            state <= S_FETCH;
                        end
                        8'h01: begin  // HALT
                            busy <= 0;
                            done <= 1;
                            state <= S_HALT;
                        end
                        8'h10: begin  // QLDI: load immediate into register
                            reg_dest <= instruction[15:8];
                            reg_imm  <= instruction[7:0];
                            reg_we   <= 1;
                            pc <= pc + 1;
                            state <= S_FETCH;
                        end
                        8'h40,        // QADD
                        8'h45: begin  // QROT
                            alu_start <= 1;
                            state <= S_WAIT_ALU;
                        end
                        8'h30: begin  // GOTO (branch always)
                            pc <= instruction[ADDR_W-1:0];
                            state <= S_FETCH;
                        end
                        8'h31: begin  // JZ (branch if zero / branch_taken)
                            if (branch_taken)
                                pc <= instruction[ADDR_W-1:0];
                            else
                                pc <= pc + 1;
                            state <= S_FETCH;
                        end
                        8'h80: begin  // SNAP
                            // Assert lock — handled by decoder flags
                            pc <= pc + 1;
                            state <= S_FETCH;
                        end
                        8'hA0: begin  // W60T
                            // Whisper transmit — handled by decoder flags
                            pc <= pc + 1;
                            state <= S_FETCH;
                        end
                        default: begin // unrecognized → skip
                            pc <= pc + 1;
                            state <= S_FETCH;
                        end
                    endcase
                end

                S_WAIT_ALU: begin
                    if (alu_done) begin
                        pc <= pc + 1;
                        state <= S_FETCH;
                    end
                end

                S_HALT: begin
                    // Stay here until reset or new run
                    if (run) begin
                        busy <= 1;
                        state <= S_FETCH;
                    end
                end
            endcase
        end
    end

endmodule
