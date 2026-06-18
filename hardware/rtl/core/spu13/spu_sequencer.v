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
    // robotics_fk_closure.sas — 27 words
    // Tests: inverse closure, P5 cycle, FK chain, self-inverse, period-6 orbit
    localparam PROG_SIZE = 27;
    wire [63:0] prog_words [0:PROG_SIZE-1];
    assign prog_words[0]  = 64'h1D00000100000000;  // QLDI QR0, (1,0,0,0)
    assign prog_words[1]  = 64'h1600000000000000;  // HEX  R0, QR0
    assign prog_words[2]  = 64'h1C01000001000000;  // ROTC QR1, QR0, 1 (60°)
    assign prog_words[3]  = 64'h1602010000000000;  // HEX  R2, QR1
    assign prog_words[4]  = 64'h1C02010004000000;  // ROTC QR2, QR1, 4 (240° inv)
    assign prog_words[5]  = 64'h1604020000000000;  // HEX  R4, QR2
    assign prog_words[6]  = 64'h1D03000000010000;  // QLDI QR3, (0,0,1,0)
    assign prog_words[7]  = 64'h1C04030002000000;  // ROTC QR4, QR3, 2 (P5 fwd)
    assign prog_words[8]  = 64'h1606040000000000;  // HEX  R6, QR4
    assign prog_words[9]  = 64'h1C05040005000000;  // ROTC QR5, QR4, 5 (P5 inv)
    assign prog_words[10] = 64'h1608050000000000;  // HEX  R8, QR5
    assign prog_words[11] = 64'h1D06000001000000;  // QLDI QR6, (0,1,0,0)
    assign prog_words[12] = 64'h1C07060001000000;  // ROTC QR7, QR6, 1 (60°)
    assign prog_words[13] = 64'h1C08070004000000;  // ROTC QR8, QR7, 4 (240°)
    assign prog_words[14] = 64'h160A080000000000;  // HEX  R10, QR8
    assign prog_words[15] = 64'h1D09000100000000;  // QLDI QR9, (1,0,0,0)
    assign prog_words[16] = 64'h1C0A090003000000;  // ROTC QR10, QR9, 3 (120°)
    assign prog_words[17] = 64'h1C0B0A0003000000;  // ROTC QR11, QR10, 3 (120°)
    assign prog_words[18] = 64'h160C0B0000000000;  // HEX  R12, QR11
    assign prog_words[19] = 64'h1D0C000100000000;  // QLDI QR12, (1,0,0,0)
    assign prog_words[20] = 64'h1C000C0001000000;  // ROTC QR0, QR12, 1
    assign prog_words[21] = 64'h1C00000001000000;  // ROTC QR0, QR0, 1
    assign prog_words[22] = 64'h1C00000001000000;  // ROTC QR0, QR0, 1
    assign prog_words[23] = 64'h1C00000001000000;  // ROTC QR0, QR0, 1
    assign prog_words[24] = 64'h1C00000001000000;  // ROTC QR0, QR0, 1
    assign prog_words[25] = 64'h1C00000001000000;  // ROTC QR0, QR0, 1 (6th → identity)
    assign prog_words[26] = 64'h160E000000000000;  // HEX  R14, QR0

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
