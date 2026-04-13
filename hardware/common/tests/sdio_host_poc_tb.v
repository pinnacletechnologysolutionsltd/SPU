`timescale 1ns/1ps

module sdio_host_poc_tb;

reg clk;
reg rst_n;
reg start_read;
reg [31:0] lba;
wire busy;
wire done;
wire error;
wire sd_clk;
wire sd_cmd;
wire [3:0] sd_dat;
wire [31:0] block_sum;

// Instantiate PoC
sdio_host_poc uut (
    .clk(clk),
    .rst_n(rst_n),
    .start_read(start_read),
    .lba(lba),
    .busy(busy),
    .done(done),
    .error(error),
    .sd_clk(sd_clk),
    .sd_cmd(sd_cmd),
    .sd_dat(sd_dat),
    .block_sum(block_sum)
);

initial begin
    $dumpfile("sdb_poc.vcd");
    $dumpvars(0, sdio_host_poc_tb);
end

// Clock: 50 MHz
initial clk = 0;
always #10 clk = ~clk;

initial begin
    // reset
    rst_n = 1'b0;
    start_read = 1'b0;
    lba = 32'd0;
    #100;
    rst_n = 1'b1;
    #50;

    // trigger read
    @(posedge clk);
    start_read = 1'b1;
    @(posedge clk);
    start_read = 1'b0;

    // wait for done
    wait (done == 1'b1);
    #20;

    $display("PoC done: block_sum=%0d", block_sum);
    // Expected pattern: mem[i] = i[7:0] for i=0..511
    // Sum = 2 * sum(0..255) = 2*(255*256/2) = 65280
    if (block_sum == 32'd65280) begin
        $display("SDIO PoC TB: PASS");
        $finish;
    end else begin
        $display("SDIO PoC TB: FAIL - expected 65280");
        $finish;
    end
end

endmodule
