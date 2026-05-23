// spu_sequencer.v — SPU-13 Standalone Instruction Sequencer (v1.0)
// Drives the core's inst_word/inst_valid ports from a BRAM program.
// Loads program from .mem file at synthesis time.
//
// The core already has instruction decode (QLDI, ROTC in gen_qrf block).
// The sequencer just feeds it 64-bit words one at a time.
//
// CC0 1.0 Universal.

module spu_sequencer #(
    parameter IMEM_DEPTH = 256,
    parameter IMEM_ADDR_WIDTH = 8,
    parameter MEM_FILE = "hw_test.mem"
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        boot_done,      // start execution after boot

    // Instruction output → core
    output reg         inst_valid,
    output reg  [63:0] inst_word,

    // Core feedback
    input  wire        inst_done,      // core finished instruction
    
    // Status  
    output reg  [7:0]  pc_out,
    output reg         halted,
    output reg  [7:0]  program_size
);

    // ── Instruction BRAM ────────────────────────────────────────────
    (* ram_style = "block" *)
    reg [63:0] imem [0:IMEM_DEPTH-1];

    // Load from .mem file at initialization
    integer _i;
    initial begin
        for (_i = 0; _i < IMEM_DEPTH; _i = _i + 1)
            imem[_i] = 64'd0;
        $readmemh(MEM_FILE, imem);
    end

    // Count valid instructions (non-zero words)
    reg [7:0] prog_end;
    integer _j;
    always @(*) begin
        prog_end = 0;
        for (_j = 0; _j < IMEM_DEPTH; _j = _j + 1) begin
            if (imem[_j] != 64'd0)
                prog_end = _j + 1;
        end
    end

    // ── Execution FSM ───────────────────────────────────────────────
    localparam S_IDLE = 0, S_WAIT_BOOT = 1, S_FETCH = 2, S_WAIT = 3;
    reg [2:0] state;
    reg [7:0] pc;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            pc <= 0;
            inst_valid <= 0;
            inst_word <= 0;
            halted <= 0;
            pc_out <= 0;
            program_size <= 0;
        end else begin
            inst_valid <= 0;  // pulse

            case (state)
                S_IDLE: begin
                    halted <= 0;
                    program_size <= prog_end;
                    if (boot_done && prog_end > 0) begin
                        pc <= 0;
                        state <= S_FETCH;
                    end
                end

                S_FETCH: begin
                    if (pc < prog_end) begin
                        inst_word <= imem[pc];
                        inst_valid <= 1;
                        pc_out <= pc;
                        pc <= pc + 1;
                        state <= S_WAIT;
                    end else begin
                        halted <= 1;
                        state <= S_IDLE;
                    end
                end

                S_WAIT: begin
                    if (inst_done) begin
                        state <= S_FETCH;
                    end
                end
            endcase
        end
    end

endmodule
