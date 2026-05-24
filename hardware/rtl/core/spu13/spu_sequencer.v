// spu_sequencer.v — SPU-13 Standalone Instruction Sequencer (v1.0)
// Drives the core's inst_word/inst_valid ports from embedded program ROM.
// Program is hardcoded (small programs for initial bring-up).
// CC0 1.0 Universal.

module spu_sequencer #(
    parameter IMEM_DEPTH = 32
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        boot_done,
    output reg         inst_valid,
    output reg  [63:0] inst_word,
    input  wire        inst_done,
    output reg  [7:0]  pc_out,
    output reg         halted,
    output reg  [7:0]  program_size
);
    // ── Program ROM ──────────────────────────────────────────────────
    // QLDI test: write (-1,0,0,1) to QR0, read it, then ROTC + read
    localparam PROG_SIZE = 5;
    wire [63:0] prog_words [0:PROG_SIZE-1];
    assign prog_words[0] = 64'h1D00_00FF_0000_0100;  // QLDI QR0, -1, 0, 0, 1
    assign prog_words[1] = 64'h1600_0000_0000_0000;  // HEX  R0, QR0
    assign prog_words[2] = 64'h1C01_0000_0100_0000;  // ROTC QR1, QR0, 1 (60°)
    assign prog_words[3] = 64'h1601_0100_0000_0000;  // HEX  R1, QR1
    assign prog_words[4] = 64'h1C02_0000_0200_0000;  // ROTC QR2, QR0, 2 (120°)

    // ── Execution FSM ───────────────────────────────────────────────
    localparam S_IDLE = 0, S_FETCH = 2, S_WAIT = 3, S_DELAY = 4;
    reg [2:0] state;
    reg [7:0] pc;
    reg [15:0] delay_cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            pc <= 0;
            inst_valid <= 0;
            inst_word <= 0;
            halted <= 0;
            pc_out <= 0;
            program_size <= PROG_SIZE;
        end else begin
            inst_valid <= 0;
            case (state)
                S_IDLE: begin
                    halted <= 0;
                    if (boot_done) begin
                        pc <= 0;
                        state <= S_FETCH;
                    end
                end
                S_FETCH: begin
                    if (pc < PROG_SIZE) begin
                        inst_word <= prog_words[pc];
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
                        delay_cnt <= 16000;  // ~10ms at 6.25MHz → enough for UART
                        state <= S_DELAY;
                    end
                end
                S_DELAY: begin
                    if (delay_cnt > 0)
                        delay_cnt <= delay_cnt - 1;
                    else
                        state <= S_FETCH;
                end
            endcase
        end
    end

endmodule
