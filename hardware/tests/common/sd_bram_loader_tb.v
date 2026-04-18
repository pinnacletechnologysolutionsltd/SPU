`timescale 1ns / 1ps

module tb;
    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk; // 100 MHz clock for simulation

    wire sd_cs;
    wire sd_sck;
    wire sd_mosi;
    wire sd_miso;

    wire boot_done;
    wire boot_error;

    // procedural-scope variables (declared here for Verilog compatibility)
    integer j;
    reg [7:0] expected;

    // Instantiate DUT: load two 512-byte blocks (1024 bytes)
    sd_bram_loader #(.BOOT_BYTES(1024), .BLOCK_SIZE(512), .ADDR_WIDTH(32), .CLK_DIV(1)) uut (
        .clk(clk),
        .rst_n(rst_n),
        .auto_boot(1'b1),
        .boot_done(boot_done),
        .boot_error(boot_error),
        .sd_cs(sd_cs),
        .sd_sck(sd_sck),
        .sd_mosi(sd_mosi),
        .sd_miso(sd_miso)
    );

    // Behavioral SD card model
    sim_sd_card sim (.sd_cs(sd_cs), .sd_sck(sd_sck), .sd_mosi(sd_mosi), .sd_miso(sd_miso));

    initial begin
        $dumpfile("build/sd_bram_loader_tb.vcd");
        $dumpvars(0, tb);

        // reset pulse
        rst_n = 1'b0;
        #100;
        rst_n = 1'b1;

        // wait for completion
        wait (boot_done == 1'b1);
        #100;

        // check memory
        // j and expected declared at module scope
        for (j = 0; j < 1024; j = j + 1) begin
            if (j < 512)
                expected = (0 + (j & 8'hFF));
            else
                expected = (1 + ((j - 512) & 8'hFF));

            if (uut.boot_mem[j] !== expected) begin
                $display("TB: FAIL at byte %0d: got %02x expected %02x", j, uut.boot_mem[j], expected);
                $finish;
            end
        end

        $display("TB: PASS");
        $finish;
    end

endmodule
