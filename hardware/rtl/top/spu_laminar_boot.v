// spu_laminar_boot.v
// Debug bootloader: read JEDEC ID from SPI flash, then hydrate the core with a
// deterministic 13-prime seed set for processor bring-up.
module spu_laminar_boot (
    input  clk,       // Expected 12MHz domain
    input  rst_n,
    // SPI Physical Interface
    output reg flash_cs,
    output wire flash_sck,
    input  flash_miso,
    output reg flash_mosi,
    output reg [23:0] jedec_id,
    // Internal BRAM Interface
    output reg [23:0] bram_data,
    output reg [3:0]  bram_addr,
    output reg        bram_we,
    // SDRAM Inhaler Interface
    output reg        mem_burst_wr,
    output reg [24:0] mem_addr,
    output reg [831:0] mem_wr_manifold,
    input  wire       mem_burst_done,
    output reg        boot_done
);

    // Flash Addresses
    localparam [7:0]  JEDEC_CMD           = 8'h9F;

    reg [5:0] state;
    reg [7:0] bit_cnt;
    reg [31:0] shift_reg;
    reg [3:0]  prime_cnt;
    reg [5:0]  sck_div;
    reg        sck_en;

    // SDRAM Inhaler Regs
    reg [6:0]  element_cnt;     // 0-117
    reg [7:0]  burst_cnt;       // Bursts per element
    reg [5:0]  word_in_burst;   // 0-51 (52 words = 832 bits)

    assign flash_sck = sck_en ? sck_div[5] : 1'b0;
    wire sck_rise = (sck_div == 6'd31);
    wire sck_fall = (sck_div == 6'd63);

    function [23:0] seed_prime;
        input [3:0] idx;
        begin
            case (idx)
                4'd0:  seed_prime = 24'd2;
                4'd1:  seed_prime = 24'd3;
                4'd2:  seed_prime = 24'd5;
                4'd3:  seed_prime = 24'd7;
                4'd4:  seed_prime = 24'd11;
                4'd5:  seed_prime = 24'd13;
                4'd6:  seed_prime = 24'd17;
                4'd7:  seed_prime = 24'd19;
                4'd8:  seed_prime = 24'd23;
                4'd9:  seed_prime = 24'd29;
                4'd10: seed_prime = 24'd31;
                4'd11: seed_prime = 24'd37;
                4'd12: seed_prime = 24'd41;
                default: seed_prime = 24'd0;
            endcase
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= 0;
            flash_cs <= 1;
            flash_mosi <= 0;
            jedec_id <= 0;
            boot_done <= 0;
            bram_we <= 0;
            bram_addr <= 0;
            sck_div <= 0;
            sck_en <= 0;
            prime_cnt <= 0;
            bit_cnt <= 0;
            bram_data <= 0;
            mem_burst_wr <= 0;
            mem_addr <= 0;
            mem_wr_manifold <= 0;
            element_cnt <= 0;
            burst_cnt <= 0;
            word_in_burst <= 0;
            shift_reg <= 0;
        end else if (!boot_done) begin
            sck_div <= sck_div + 1'b1;

            case (state)
                0: begin // Initial Idle -> Read JEDEC ID
                    flash_cs <= 0;
                    sck_en <= 1'b1;
                    shift_reg <= {JEDEC_CMD, 24'h0};
                    flash_mosi <= JEDEC_CMD[7];
                    bit_cnt <= 0;
                    state <= 1;
                    sck_div <= 0;
                end

                1: begin // Send JEDEC command (8 bits)
                    if (sck_fall) begin
                        shift_reg <= {shift_reg[30:0], 1'b0};
                        if (bit_cnt == 7) begin
                            state <= 2;
                            bit_cnt <= 0;
                            flash_mosi <= 1'b0;
                        end else begin
                            bit_cnt <= bit_cnt + 1;
                            flash_mosi <= shift_reg[30];
                        end
                    end
                end

                2: begin // Read JEDEC ID (24 bits)
                    if (sck_fall) begin
                        if (bit_cnt == 23) begin
                            sck_en <= 1'b0;
                            state <= 3;
                        end else begin
                            bit_cnt <= bit_cnt + 1;
                        end
                    end else if (sck_rise) begin
                        shift_reg <= {shift_reg[30:0], flash_miso};
                        if (bit_cnt == 23) begin
                            jedec_id <= {shift_reg[22:0], flash_miso};
                            bram_data <= seed_prime(4'd0);
                            bram_addr <= 4'd0;
                            bram_we <= 1;
                            prime_cnt <= 4'd1;
                        end
                    end
                end

                3: begin // Write deterministic seed primes into all 13 slots
                    flash_cs <= 1;
                    bram_we <= 1;
                    bram_addr <= prime_cnt;
                    bram_data <= seed_prime(prime_cnt);
                    if (prime_cnt == 4'd12) begin
                        state <= 4;
                    end else begin
                        prime_cnt <= prime_cnt + 1'b1;
                    end
                end

                4: begin // Final Cleanup
                    flash_cs <= 1;
                    bram_we <= 0;
                    boot_done <= 1;
                end
            endcase
        end
    end
endmodule
