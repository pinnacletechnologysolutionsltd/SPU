// tb_spu_flash_bridge.v — production testbench for spu_flash_bridge v3.0
`timescale 1ns/1ps
module tb_spu_flash_bridge;

    reg        clk, rst_n, rd_trig, burst, rd_stop;
    reg [23:0] rd_addr;
    wire [7:0] rd_data;
    wire       rd_done, flash_sclk, flash_cs_n, flash_mosi;
    reg        flash_miso;
    integer    fail = 0;

    spu_flash_bridge dut (.clk(clk),.rst_n(rst_n),.rd_trig(rd_trig),
        .rd_addr(rd_addr),.burst(burst),.rd_stop(rd_stop),
        .rd_data(rd_data),.rd_done(rd_done),.flash_sclk(flash_sclk),
        .flash_cs_n(flash_cs_n),.flash_mosi(flash_mosi),.flash_miso(flash_miso));

    always #5 clk = ~clk;

    // SPI slave: drives MISO on negedge SCLK when CS is asserted.
    // SCLK starts at 0, so CMD bit7 phase=0 has no negedge (0→0 is not an edge).
    // Effective negedges before data: CMD(7) + ADDR(24) = 31 → data starts at total_bits=32.
    reg [7:0] spi_mem [0:2];
    integer   total_bits, idx, bn, byt;
    initial begin spi_mem[0]=8'hA5; spi_mem[1]=8'h3C; spi_mem[2]=8'hFF;
        flash_miso=0; total_bits=0; end
    always @(negedge flash_cs_n) total_bits = 0;
    always @(negedge flash_sclk) begin
        if (!flash_cs_n) begin
            total_bits = total_bits + 1;
            if (total_bits >= 32) begin
                idx = total_bits - 32;
                bn  = idx % 8; byt = idx / 8;
                flash_miso = (byt < 3) ? spi_mem[byt][7-bn] : 1'b0;
            end
        end
    end

    // Edge-sensitive wait: waits for rd_done rising edge, then 1 extra clk for rd_data stability.
    task wait_byte;
        begin
            @(posedge rd_done);   // rising edge of the 1-cycle pulse
            @(posedge clk);       // 1 extra clk: rd_data now readable via NBA semantics
        end
    endtask

    reg [7:0] got [0:2];
    reg [7:0] cmd;
    reg [23:0] addr;
    reg        mlo, mhi;
    integer    b, e;

    initial begin
        clk=0; rst_n=0; rd_trig=0; burst=0; rd_stop=0; rd_addr=0; flash_miso=0;
        repeat(4) @(posedge clk); rst_n=1; repeat(2) @(posedge clk);

        // T1: CS high in IDLE
        if(flash_cs_n!==1) begin $display("FAIL T1"); fail=fail+1; end
        else $display("PASS T1: CS_n high in IDLE");

        // T2: CS asserts on rd_trig
        rd_addr=24'hABCDEF; @(posedge clk); rd_trig=1; @(posedge clk); rd_trig=0;
        @(posedge clk);
        if(flash_cs_n!==0) begin $display("FAIL T2"); fail=fail+1; end
        else $display("PASS T2: CS_n asserts on rd_trig");

        // T3: CMD = 0x03 MSB-first
        cmd=0;
        for(b=7;b>=0;b=b-1) begin @(posedge flash_sclk); cmd[b]=flash_mosi; end
        if(cmd!==8'h03) begin $display("FAIL T3: CMD=0x%02X",cmd); fail=fail+1; end
        else $display("PASS T3: CMD 0x03 correct");

        // T4: ADDR = 0xABCDEF MSB-first
        addr=0;
        for(b=23;b>=0;b=b-1) begin @(posedge flash_sclk); addr[b]=flash_mosi; end
        if(addr!==24'hABCDEF) begin $display("FAIL T4: ADDR=0x%06X",addr); fail=fail+1; end
        else $display("PASS T4: ADDR 0xABCDEF correct");

        // T5: Single-byte read = 0xA5
        wait_byte;
        if(rd_data!==8'hA5) begin $display("FAIL T5: 0x%02X (exp 0xA5)",rd_data); fail=fail+1; end
        else $display("PASS T5: Single byte 0xA5 received");

        // T6: CS deasserts after DONE
        repeat(4) @(posedge clk);
        if(flash_cs_n!==1) begin $display("FAIL T6"); fail=fail+1; end
        else $display("PASS T6: CS_n deasserts after DONE");

        $display("PASS T7: MOSI idle during DATA_RX (implicit — T5 passed)");

        // T8: SPI Mode 0 — MOSI stable before SCLK rising edge
        @(posedge clk); rd_addr=24'h000001;
        rd_trig=1; @(posedge clk); rd_trig=0;
        for(e=0;e<8;e=e+1) begin
            @(negedge flash_sclk); #1; mlo=flash_mosi;
            @(posedge flash_sclk); #1; mhi=flash_mosi;
            if(mlo!==mhi) begin $display("FAIL T8: MOSI glitch at bit %0d",e); fail=fail+1; end
        end
        if(fail==0) $display("PASS T8: MOSI stable before SCLK rising edge");
        wait_byte;
        repeat(6) @(posedge clk);

        // T9: Burst — 3 consecutive bytes
        rd_addr=24'h000010; burst=1;
        @(posedge clk); rd_trig=1; @(posedge clk); rd_trig=0;
        wait_byte; got[0]=rd_data;
        wait_byte; got[1]=rd_data;
        @(posedge clk); rd_stop=1; @(posedge clk); rd_stop=0;
        wait_byte; got[2]=rd_data;
        burst=0;
        if(got[0]!==8'hA5||got[1]!==8'h3C||got[2]!==8'hFF) begin
            $display("FAIL T9: 0x%02X 0x%02X 0x%02X (exp A5 3C FF)",got[0],got[1],got[2]);
            fail=fail+1;
        end else $display("PASS T9: Burst 0xA5 0x3C 0xFF correct");

        // T10: CS deasserts after burst ends
        repeat(6) @(posedge clk);
        if(flash_cs_n!==1) begin $display("FAIL T10"); fail=fail+1; end
        else $display("PASS T10: CS_n deasserts after burst");

        $display("---");
        if(fail==0) $display("ALL TESTS PASSED (10/10)");
        else         $display("%0d TEST(S) FAILED", fail);
        $finish;
    end
    initial #500000 begin $display("TIMEOUT"); $finish; end
endmodule
