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
    localparam PROG_SIZE = 10;
    wire [63:0] prog_words [0:PROG_SIZE-1];
    assign prog_words[0] = 64'h1D00_00FF_0000_0100;  // QLDI QR0, -1, 0, 0, 1
    assign prog_words[1] = 64'h1600_0000_0000_0000;  // HEX  R0, QR0
    assign prog_words[2] = 64'h1C01_0000_0100_0000;  // ROTC QR1, QR0, 1
    assign prog_words[3] = 64'h1601_0100_0000_0000;  // HEX  R1, QR1
    assign prog_words[4] = 64'h1C02_0000_0200_0000;  // ROTC QR2, QR0, 2
    assign prog_words[5] = 64'h1602_0200_0000_0000;  // HEX  R2, QR2
    assign prog_words[6] = 64'h1C03_0000_0400_0000;  // ROTC QR3, QR0, 4
    assign prog_words[7] = 64'h1603_0300_0000_0000;  // HEX  R3, QR3
    assign prog_words[8] = 64'h1D04_00FF_0000_FF00;  // QLDI QR4, -1, 0, 0, -1
    assign prog_words[9] = 64'h1604_0400_0000_0000;  // HEX  R4, QR4

    // ── Execution FSM ───────────────────────────────────────────────
    localparam S_IDLE = 0, S_FETCH = 2, S_WAIT = 3;
    reg [2:0] state;
    reg [7:0] pc;
    reg       boot_done_d1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            pc <= 0;
            inst_valid <= 0;
            inst_word <= 0;
            halted <= 0;
            pc_out <= 0;
            program_size <= PROG_SIZE;
            boot_done_d1 <= 0;
        end else begin
            inst_valid <= 0;
            boot_done_d1 <= boot_done;
            case (state)
                S_IDLE: begin
                    halted <= 0;
                    // One-shot: start on rising edge of boot_done
                    if (boot_done && !boot_done_d1) begin
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
                    if (inst_done)
                        state <= S_FETCH;
                end
            endcase
        end
    end

endmodule
