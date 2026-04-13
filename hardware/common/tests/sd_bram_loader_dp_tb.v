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

    wire boot_wr_en;
    wire [9:0] boot_wr_addr;
    wire [23:0] boot_wr_data;

    // Instantiate DUT: load two 512-byte blocks (1024 bytes)
    sd_bram_loader_dp #(.BOOT_BYTES(1024), .BLOCK_SIZE(512), .BOOT_WORD_ADDR_WIDTH(10)) uut (
        .clk(clk),
        .rst_n(rst_n),
        .auto_boot(1'b1),
        .boot_done(boot_done),
        .boot_error(boot_error),
        .boot_wr_en(boot_wr_en),
        .boot_wr_addr(boot_wr_addr),
        .boot_wr_data(boot_wr_data),
        .sd_cs(sd_cs),
        .sd_sck(sd_sck),
        .sd_mosi(sd_mosi),
        .sd_miso(sd_miso)
    );

    // Boot RAM (capture writes)
    boot_ram_dp #(.ADDR_WIDTH(10), .DATA_WIDTH(24)) u_boot (
        .clk_write(clk),
        .we(boot_wr_en),
        .addr_write(boot_wr_addr),
        .write_data(boot_wr_data),
        .clk_read(clk),
        .addr_read(10'd0),
        .read_data()
    );

    // Behavioral SD card model
    sim_sd_card sim (.sd_cs(sd_cs), .sd_sck(sd_sck), .sd_mosi(sd_mosi), .sd_miso(sd_miso));

    // variables for checking
    integer j;
    reg [7:0] expected;
    integer word_idx;
    reg [23:0] w;
    reg [7:0] b;

    initial begin
        $dumpfile("build/sd_bram_loader_dp_tb.vcd");
        $dumpvars(0, tb);

        // reset pulse
        rst_n = 1'b0;
        #100;
        rst_n = 1'b1;

        // wait for completion
        wait (boot_done == 1'b1);
        #100;

        // check memory bytes
        for (j = 0; j < 1024; j = j + 1) begin
            if (j < 512)
                expected = (0 + (j & 8'hFF));
            else
                expected = (1 + ((j - 512) & 8'hFF));

            word_idx = j / 3;
            w = u_boot.mem[word_idx];
            b = w >> ((2 - (j % 3)) * 8);

            if (b !== expected) begin
                $display("TB: FAIL at byte %0d: got %02x expected %02x", j, b, expected);
                $finish;
            end
        end

        $display("TB: PASS");
        $finish;
    end

endmodule
