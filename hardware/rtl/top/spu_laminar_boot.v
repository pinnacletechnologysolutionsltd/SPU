// spu_laminar_boot.v
// Hydrates the SPU-13 BRAM with Thomson Primes from SPI Flash PMOD.
module spu_laminar_boot (
    input  clk,
    input  rst_n,
    // SPI Physical Interface
    output reg flash_cs,
    output reg flash_sck,
    input  flash_miso,
    output reg flash_mosi,
    // Internal BRAM Interface
    output reg [23:0] bram_data,
    output reg [3:0]  bram_addr,
    output reg        bram_we,
    output reg        boot_done
);

    // Flash Address where Thomson Primes live (0x100000)
    localparam [23:0] START_ADDR = 24'h100000;
    localparam [7:0]  READ_CMD   = 8'h03; // Standard SPI Read

    reg [5:0] state;
    reg [7:0] bit_cnt;
    reg [23:0] shift_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= 0;
            flash_cs <= 1;
            boot_done <= 0;
            bram_we <= 0;
            bram_addr <= 0;
        end else if (!boot_done) begin
            case (state)
                0: begin // Begin Transaction
                    flash_cs <= 0;
                    shift_reg <= {READ_CMD, START_ADDR[23:8]}; // Partial load
                    state <= 1;
                    bit_cnt <= 0;
                end
                
                1: begin // Clock out Command + Address (simplified for brevity)
                    // ... SPI Bit-Banging Logic ...
                    bit_cnt <= bit_cnt + 1;
                    if (bit_cnt == 31) state <= 2;
                end

                2: begin // Read 24-bit Prime from Flash
                    bram_data <= shift_reg; 
                    bram_we <= 1;
                    state <= 3;
                end

                3: begin // Increment and Repeat until 13 Primes are Loaded
                    bram_we <= 0;
                    if (bram_addr == 12) begin
                        boot_done <= 1;
                        flash_cs <= 1;
                    end else begin
                        bram_addr <= bram_addr + 1;
                        state <= 2;
                    end
                end
            endcase
        end
    end
endmodule
