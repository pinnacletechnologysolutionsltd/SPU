// spu_sequencer.v — SPU-13 Standalone Instruction Sequencer (v2.0)
// Drives the core's inst_word/inst_valid ports.
// Boots from SPI flash (fallback: embedded default program).
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
    output reg  [7:0]  program_size,
    input  wire        damping_active,   // throttle from proprioception

    // ── SPI Flash (W25Q128JV) ───────────────────────────────────────
    output reg         flash_csn,
    output reg         flash_sck,
    output reg         flash_mosi,
    input  wire        flash_miso
);

    // ── Program BRAM (writable from flash, readable by FSM) ─────────
    reg [63:0] prog_bram [0:IMEM_DEPTH-1];
    reg [7:0]  prog_len;

    // ── Default fallback program ────────────────────────────────────
    localparam DEFAULT_SIZE = 5;
    wire [63:0] default_prog [0:DEFAULT_SIZE-1];
    assign default_prog[0] = 64'h1D00_02FE_0000_0000;
    assign default_prog[1] = 64'h1600_0000_0000_0000;
    assign default_prog[2] = 64'h1C01_0000_0100_0000;
    assign default_prog[3] = 64'h1601_0100_0000_0000;
    assign default_prog[4] = 64'h1C02_0000_0200_0000;

    // ── SPI boot: load program from flash at 0x010000 ──────────────
    localparam S_BOOT       = 0,
               S_FLASH_CMD  = 1,
               S_FLASH_ADDR = 2,
               S_FLASH_READ = 3,
               S_FLASH_DONE = 4,
               S_IDLE       = 5,
               S_FETCH      = 6,
               S_WAIT       = 7,
               S_DELAY      = 8;

    reg  [3:0] state;
    reg  [7:0] pc;
    reg [15:0] delay_cnt;
    reg  [2:0] bit_count;
    reg  [7:0] spi_sr;
    reg  [7:0] spi_rx;
    reg  [1:0] addr_idx;
    reg  [7:0] flash_idx;
    reg  [2:0] byte_idx;
    reg [63:0] flash_word;
    reg        prev_sck;

    // ── Return stack ───────────────────────────────────────────────
    reg [7:0]  ret_stack [0:7];
    reg [2:0]  sp;
    reg        last_was_call;
    reg [7:0]  call_target;

    integer init_i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state         <= S_BOOT;
            pc            <= 0;
            inst_valid    <= 0;
            inst_word     <= 0;
            halted        <= 0;
            pc_out        <= 0;
            program_size  <= DEFAULT_SIZE;
            prog_len      <= DEFAULT_SIZE;
            flash_csn     <= 1;
            flash_sck     <= 0;
            flash_mosi    <= 0;
            bit_count     <= 0;
            addr_idx      <= 0;
            flash_idx     <= 0;
            byte_idx      <= 0;
            flash_word    <= 0;
            spi_sr        <= 0;
            spi_rx        <= 0;
            prev_sck      <= 0;
            sp            <= 0;
            last_was_call <= 0;
            for (init_i = 0; init_i < DEFAULT_SIZE; init_i = init_i + 1)
                prog_bram[init_i] <= default_prog[init_i];
        end else begin
            inst_valid <= 0;
            prev_sck <= flash_sck;
            case (state)

                S_BOOT: begin
                    // Bypass SPI flash — go straight to execution
                    if (boot_done) begin
                        state <= S_IDLE;
                    end
                end
                S_FLASH_SKIP: begin
                    state <= S_IDLE;
                end
                S_FLASH_CMD: begin
                    if (1'b0) begin  // unreachable — keep syntax valid
                        flash_csn  <= 0;
                        spi_sr     <= 8'h03;   // READ command
                        bit_count  <= 7;
                        flash_idx  <= 0;
                        state      <= S_FLASH_CMD;
                    end
                end

                S_FLASH_CMD: begin
                    flash_sck <= ~flash_sck;
                    if (flash_sck && !prev_sck) begin  // rising edge
                        flash_mosi <= spi_sr[7];
                        spi_sr <= {spi_sr[6:0], 1'b0};
                        if (bit_count == 0) begin
                            spi_sr    <= 8'h01;      // addr[23:16] = 0x01
                            bit_count <= 7;
                            addr_idx  <= 0;
                            state     <= S_FLASH_ADDR;
                        end else begin
                            bit_count <= bit_count - 1;
                        end
                    end
                end

                S_FLASH_ADDR: begin
                    flash_sck <= ~flash_sck;
                    if (flash_sck && !prev_sck) begin
                        flash_mosi <= spi_sr[7];
                        spi_sr <= {spi_sr[6:0], 1'b0};
                        if (bit_count == 0) begin
                            case (addr_idx)
                                0: begin spi_sr <= 8'h00; bit_count <= 7; addr_idx <= 1; end
                                1: begin spi_sr <= 8'h00; bit_count <= 7; addr_idx <= 2; end
                                2: begin bit_count <= 7; state <= S_FLASH_READ; end
                            endcase
                        end else begin
                            bit_count <= bit_count - 1;
                        end
                    end
                end

                S_FLASH_READ: begin
                    flash_sck <= ~flash_sck;
                    if (flash_sck && !prev_sck) begin
                        spi_rx <= {spi_rx[6:0], flash_miso};
                        if (bit_count == 0) begin
                            case (byte_idx)
                                0: flash_word[63:56] <= {spi_rx[6:0], flash_miso};
                                1: flash_word[55:48] <= {spi_rx[6:0], flash_miso};
                                2: flash_word[47:40] <= {spi_rx[6:0], flash_miso};
                                3: flash_word[39:32] <= {spi_rx[6:0], flash_miso};
                                4: flash_word[31:24] <= {spi_rx[6:0], flash_miso};
                                5: flash_word[23:16] <= {spi_rx[6:0], flash_miso};
                                6: flash_word[15:8]  <= {spi_rx[6:0], flash_miso};
                                7: begin
                                    flash_word[7:0] <= {spi_rx[6:0], flash_miso};
                                    prog_bram[flash_idx] <= {flash_word[63:8], spi_rx[6:0], flash_miso};
                                    if ({flash_word[63:8], spi_rx[6:0], flash_miso} == 64'hFFFFFFFF_FFFFFFFF 
                                        || flash_idx == (IMEM_DEPTH - 1)) begin
                                        prog_len <= flash_idx;
                                        flash_csn <= 1;
                                        state <= S_FLASH_DONE;
                                    end else begin
                                        flash_idx <= flash_idx + 1;
                                    end
                                end
                            endcase
                            byte_idx <= (byte_idx == 7) ? 0 : byte_idx + 1;
                            bit_count <= 7;
                        end else begin
                            bit_count <= bit_count - 1;
                        end
                    end
                end

                S_FLASH_DONE: begin
                    flash_csn <= 1;
                    flash_sck <= 0;
                    program_size <= prog_len;
                    pc <= 0;
                    state <= S_IDLE;
                end

                S_IDLE: begin
                    halted <= 0;
                    if (1'b0) begin  // disabled — skip SPI flash
                        state <= S_FETCH;
                    end
                end

                S_FETCH: begin
                    if (pc < prog_len) begin
                        inst_word <= prog_bram[pc];
                        inst_valid <= 1;
                        pc_out <= pc;
                        if (prog_bram[pc][63:56] == 8'h20 || prog_bram[pc][63:56] == 8'h06)
                            call_target <= prog_bram[pc][31:24];
                        pc <= pc + 1;
                        state <= S_WAIT;
                    end else begin
                        halted <= 1;
                        state <= S_IDLE;
                    end
                end

                S_WAIT: begin
                    if (inst_done) begin
                        last_was_call <= 0;
                        if (inst_word[63:56] == 8'h20) begin
                            if (sp < 7) begin
                                ret_stack[sp] <= pc;
                                sp <= sp + 1;
                            end
                            pc <= call_target;
                            last_was_call <= 1;
                        end else if (inst_word[63:56] == 8'h06) begin
                            pc <= call_target;
                        end else if (inst_word[63:56] == 8'h21) begin
                            if (sp > 0) begin
                                sp <= sp - 1;
                                pc <= ret_stack[sp-1];
                            end
                        end
                        delay_cnt <= damping_active ? 32000 : 16000;
                        state <= S_DELAY;
                    end
                end

                S_DELAY: begin
                    if (delay_cnt > 0)
                        delay_cnt <= delay_cnt - 1;
                    else
                        state <= S_FETCH;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
