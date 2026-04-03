// spu_ghost_boot.v (v1.1 - Fractal Hydration)
// Objective: Inhale Ghost OS and Thomson Primes from External SPI Flash.
// Standard: Phi-Gated Timing (8, 13, 21 Fibonacci intervals).

`include "spu_arch_defines.vh"

module spu_ghost_boot (
    input  wire        clk,          // 12-24 MHz System Clock
    input  wire        rst_n,
    
    // --- Fibonacci Timing Pulses (from Sierpinski Clock) ---
    input  wire        phi_8,
    input  wire        phi_13,
    input  wire        phi_21,

    // --- External SPI Interface (PMOD) ---
    output reg         ext_spi_cs_n,
    output reg         ext_spi_sck,
    output reg         ext_spi_mosi,
    input  wire        ext_spi_miso,
    
    // --- Internal Manifold/BRAM Interface ---
    output reg         boot_done,
    output reg [3:0]   prime_addr,
    output reg [23:0]  prime_data,
    output reg         prime_we
);

    // Use the 21-cycle pulse for latching/sampling and 13 for clock toggling.
    // This provides a "Laminar" wide timing margin.
    
    // 1. Boot State Machine
    localparam S_IDLE       = 4'd0;
    localparam S_INIT_CMD   = 4'd1;
    localparam S_READ_ADDR  = 4'd2;
    localparam S_INHALE_DATA = 4'd3;
    localparam S_COMMIT     = 4'd4;
    localparam S_DONE       = 4'd5;

    reg [3:0]  state;
    reg [7:0]  bit_cnt;
    reg [31:0] shift_reg;
    
    // Flash Mapping (Sovereign Standard)
    localparam [7:0]  CMD_READ = 8'h03;
    localparam [23:0] OS_BASE  = 24'h000000;
    localparam [23:0] PRIMES_BASE = 24'h100000;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            ext_spi_cs_n <= 1;
            ext_spi_sck <= 0;
            boot_done <= 0;
            prime_we <= 0;
            prime_addr <= 0;
            bit_cnt <= 0;
            ext_spi_mosi <= 0;
        end else begin
            case (state)
                S_IDLE: begin
                    if (phi_8) begin
                        ext_spi_cs_n <= 0;
                        shift_reg <= {CMD_READ, PRIMES_BASE};
                        bit_cnt <= 31;
                        state <= S_INIT_CMD;
                    end
                end

                S_INIT_CMD, S_READ_ADDR: begin
                    // Toggle SCK on Phi-13 and Phi-21
                    if (phi_13) begin
                        ext_spi_sck <= 1;
                        ext_spi_mosi <= shift_reg[bit_cnt];
                    end else if (phi_21) begin
                        ext_spi_sck <= 0;
                        if (bit_cnt == 0) state <= S_INHALE_DATA;
                        else bit_cnt <= bit_cnt - 1;
                    end
                end

                S_INHALE_DATA: begin
                    if (phi_13) begin
                        ext_spi_sck <= 1;
                    end else if (phi_21) begin
                        ext_spi_sck <= 0;
                        // Sample MISO on falling edge intersection
                        shift_reg <= {shift_reg[22:0], ext_spi_miso};
                        bit_cnt <= bit_cnt + 1;
                        if (bit_cnt == 23) begin
                            bit_cnt <= 0;
                            state <= S_COMMIT;
                        end
                    end
                end

                S_COMMIT: begin
                    // Use Phi-8 for BRAM write strobe
                    if (phi_8) begin
                        prime_data <= shift_reg[23:0];
                        prime_we <= 1;
                    end else if (phi_13) begin
                        prime_we <= 0;
                        state <= (prime_addr == 12) ? S_DONE : S_INHALE_DATA;
                        if (prime_addr < 12) prime_addr <= prime_addr + 1;
                    end
                end

                S_DONE: begin
                    ext_spi_cs_n <= 1;
                    boot_done <= 1;
                end
            endcase
        end
    end

endmodule
