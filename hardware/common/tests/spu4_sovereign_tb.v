`timescale 1ns/1ps

// Simple SPI Flash Model (v1.0)
module spi_flash_model (
    input  wire sck,
    input  wire cs_n,
    input  wire mosi,
    output reg  miso
);
    reg [7:0] data [0:255]; // Small model
    reg [7:0] shift_reg;
    reg [7:0] cmd;
    reg [23:0] addr;
    reg [2:0] state;
    reg [7:0] bit_cnt;

    integer i;
    initial begin
        miso = 0;
        state = 0;
        bit_cnt = 0;
        // Seed some 'Dream' instructions at 0xF000 (mapped to 0x10 in our model)
        // 0x2000 (ROTATE)
        data[24'h10] = 8'h20; data[24'h11] = 8'h00;
        // 0x3000 (GOTO 0)
        data[24'h12] = 8'h30; data[24'h13] = 8'h00;
    end

    always @(posedge sck) begin
        if (!cs_n) begin
            case (state)
                0: begin // CMD
                    cmd <= {cmd[6:0], mosi};
                    if (bit_cnt == 7) begin state <= 1; bit_cnt <= 0; end
                    else bit_cnt <= bit_cnt + 1;
                end
                1: begin // ADDR
                    addr <= {addr[22:0], mosi};
                    if (bit_cnt == 23) begin state <= 2; bit_cnt <= 0; end
                    else bit_cnt <= bit_cnt + 1;
                end
                2: begin // DATA out
                    miso <= data[addr[7:0]][7-bit_cnt[2:0]];
                    if (bit_cnt[2:0] == 7) addr <= addr + 1;
                    bit_cnt <= bit_cnt + 1;
                end
            endcase
        end
    end
endmodule

module spu4_sovereign_tb;
    reg clk, reset;
    wire spi_cs_n, spi_sck, spi_mosi, spi_miso;
    wire [15:0] A_out, B_out, C_out, D_out;
    wire bloom_complete;

    // 1. Flash Model
    spi_flash_model u_flash (
        .sck(spi_sck), .cs_n(spi_cs_n), .mosi(spi_mosi), .miso(spi_miso)
    );

    // 2. Sovereign SPU-4 Core
    spu4_core u_sentinel (
        .clk(clk), .reset(reset),
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck), .spi_mosi(spi_mosi), .spi_miso(spi_miso),
        .prog_en_aux(1'b0), .prog_addr_aux(4'h0), .prog_data_aux(16'h0),
        .mode_autonomous(1'b1),
        .A_in(16'h0100), .B_in(16'h0), .C_in(16'h0), .D_in(16'h0),
        .bus_ready(1'b1),
        .A_out(A_out), .B_out(B_out), .C_out(C_out), .D_out(D_out),
        .bloom_complete(bloom_complete)
    );

    always #41.66 clk = ~clk;

    initial begin
        $dumpfile("sovereign_inhale.vcd");
        $dumpvars(0, spu4_sovereign_tb);
        clk = 0; reset = 1; #200; reset = 0;

        $display("--- [Sentinel Sovereignty] Initiating Refractive Inhale ---");
        
        // Wait for inhale to complete (approx 1000 cycles)
        #100000;
        
        if (u_sentinel.inhale_done)
            $display("[PASS] Sovereign Inhale Complete. SPU-4 is Dreaming.");
        else
            $display("[FAIL] Inhale Timeout.");

        #100000;
        $finish;
    end
endmodule
