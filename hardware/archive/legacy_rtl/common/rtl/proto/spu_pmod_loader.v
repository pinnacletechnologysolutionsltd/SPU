// spu_pmod_loader.v (v1.0 - Sovereign Boot)
// Objective: Stream 13-axis Thomson Primes from PMOD to Cortex.
// Protocol: Bit-serial ingestion on 'load_pulse' trigger.

module spu_pmod_loader #(
    parameter CHORD_WIDTH = 64,
    parameter AXIS_COUNT  = 13
)(
    input  wire        clk,
    input  wire        rst_n,
    
    // PMOD Interface (Simple SPI-mode serial input)
    input  wire        pmod_sclk,
    input  wire        pmod_mosi,
    input  wire        pmod_cs_n,
    
    // Cortex Interface
    output reg         load_done,
    output reg [831:0] prime_manifold,
    output reg         prime_valid
);

    // 13 axes * 64 bits = 832 bits total.
    reg [831:0] shift_reg;
    reg [9:0]   bit_cnt;   // Need to count up to 831

    always @(posedge pmod_sclk or negedge rst_n) begin
        if (!rst_n) begin
            shift_reg <= 832'h0;
            bit_cnt   <= 10'h0;
            load_done <= 1'b0;
        end else if (!pmod_cs_n) begin
            if (bit_cnt < 10'd832) begin
                shift_reg <= {shift_reg[830:0], pmod_mosi};
                bit_cnt   <= bit_cnt + 10'd1;
                // Assert done immediately on the 832nd bit
                if (bit_cnt == 10'd831) begin
                    load_done <= 1'b1;
                end
            end
        end
    end

    // Clock Domain Crossing: Latch the prime manifold when loading is done
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            prime_manifold <= 832'h0;
            prime_valid    <= 1'b0;
        end else if (load_done && !prime_valid) begin
            prime_manifold <= shift_reg;
            prime_valid    <= 1'b1;
        end else if (!load_done) begin
            prime_valid    <= 1'b0;
        end
    end

endmodule
