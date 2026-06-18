// spu_sequencer.v — SPU-13 Standalone Instruction Sequencer (v1.0)
// Drives the core's inst_word/inst_valid ports from embedded program ROM.
// Program is hardcoded (small programs for initial bring-up).
// CC0 1.0 Universal.

module spu_sequencer #(
    parameter IMEM_DEPTH = 64
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
    // som_train_demo.sas — 49 words, 4-epoch SOM training
    localparam PROG_SIZE = 49;
    wire [63:0] prog_words [0:PROG_SIZE-1];
    assign prog_words[ 0] = 64'h1d00000400000000;
    assign prog_words[ 1] = 64'h2a00000000000000;
    assign prog_words[ 2] = 64'h2b00000001000000;
    assign prog_words[ 3] = 64'h1d0000fe03000000;
    assign prog_words[ 4] = 64'h2a00000000000000;
    assign prog_words[ 5] = 64'h2b00000001000000;
    assign prog_words[ 6] = 64'h1d000001fd000000;
    assign prog_words[ 7] = 64'h2a00000000000000;
    assign prog_words[ 8] = 64'h2b00000001000000;
    assign prog_words[ 9] = 64'h1d00000000000000;
    assign prog_words[10] = 64'h2a00000000000000;
    assign prog_words[11] = 64'h2b00000001000000;
    assign prog_words[12] = 64'h1d00000400000000;
    assign prog_words[13] = 64'h2a00000000000000;
    assign prog_words[14] = 64'h2b00000002000000;
    assign prog_words[15] = 64'h1d0000fe03000000;
    assign prog_words[16] = 64'h2a00000000000000;
    assign prog_words[17] = 64'h2b00000002000000;
    assign prog_words[18] = 64'h1d000001fd000000;
    assign prog_words[19] = 64'h2a00000000000000;
    assign prog_words[20] = 64'h2b00000002000000;
    assign prog_words[21] = 64'h1d00000000000000;
    assign prog_words[22] = 64'h2a00000000000000;
    assign prog_words[23] = 64'h2b00000002000000;
    assign prog_words[24] = 64'h1d00000400000000;
    assign prog_words[25] = 64'h2a00000000000000;
    assign prog_words[26] = 64'h2b00000003000000;
    assign prog_words[27] = 64'h1d0000fe03000000;
    assign prog_words[28] = 64'h2a00000000000000;
    assign prog_words[29] = 64'h2b00000003000000;
    assign prog_words[30] = 64'h1d000001fd000000;
    assign prog_words[31] = 64'h2a00000000000000;
    assign prog_words[32] = 64'h2b00000003000000;
    assign prog_words[33] = 64'h1d00000000000000;
    assign prog_words[34] = 64'h2a00000000000000;
    assign prog_words[35] = 64'h2b00000003000000;
    assign prog_words[36] = 64'h1d00000400000000;
    assign prog_words[37] = 64'h2a00000000000000;
    assign prog_words[38] = 64'h2b00000004000000;
    assign prog_words[39] = 64'h1d0000fe03000000;
    assign prog_words[40] = 64'h2a00000000000000;
    assign prog_words[41] = 64'h2b00000004000000;
    assign prog_words[42] = 64'h1d000001fd000000;
    assign prog_words[43] = 64'h2a00000000000000;
    assign prog_words[44] = 64'h2b00000004000000;
    assign prog_words[45] = 64'h1d00000000000000;
    assign prog_words[46] = 64'h2a00000000000000;
    assign prog_words[47] = 64'h2b00000004000000;
    assign prog_words[48] = 64'hff00000000000000;

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
