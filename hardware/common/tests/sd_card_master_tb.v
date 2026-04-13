// sd_card_master_tb.v — testbench for sd_card_master with sim_sd_card
`timescale 1ns / 1ps

module sd_card_master_tb;

localparam BLOCK_SIZE = 512;

reg clk = 0;
always #5 clk = ~clk; // 100 MHz

reg rst_n;
reg start_read;
reg [31:0] block_addr;
wire busy;
wire data_valid;
wire [7:0] data_out;
wire last;
wire sd_cs, sd_sck, sd_mosi;
wire sd_miso;

sd_card_master #(.BLOCK_SIZE_BYTES(BLOCK_SIZE)) dut (
    .clk(clk),
    .rst_n(rst_n),
    .start_read(start_read),
    .block_addr(block_addr),
    .busy(busy),
    .data_valid(data_valid),
    .data_out(data_out),
    .last(last),
    .sd_cs(sd_cs),
    .sd_sck(sd_sck),
    .sd_mosi(sd_mosi),
    .sd_miso(sd_miso)
);

sim_sd_card simcard (
    .sd_cs(sd_cs),
    .sd_sck(sd_sck),
    .sd_mosi(sd_mosi),
    .sd_miso(sd_miso)
);

reg [7:0] rx_mem [0:BLOCK_SIZE-1];
integer idx;
integer k;

initial begin
    rst_n = 0;
    start_read = 0;
    block_addr = 32'd0;
    #100;
    rst_n = 1;
    #100;

    // Issue a start_read pulse
    @(posedge clk);
    start_read = 1;
    @(posedge clk);
    start_read = 0;

    idx = 0;
    // Collect bytes until 'last' asserted
    while (1) begin
        @(posedge clk);
        if (data_valid) begin
            rx_mem[idx] = data_out;
            if (last) begin
                idx = idx + 1;
                break;
            end
            idx = idx + 1;
        end
    end

    $display("Received %0d bytes", idx);

    // Verify deterministic pattern: data_out == block_addr[7:0] + (byte_index & 0xFF)
    for (k = 0; k < BLOCK_SIZE; k = k + 1) begin
        if (rx_mem[k] !== (block_addr[7:0] + (k & 8'hFF))) begin
            $display("Mismatch at %0d: got %02x expect %02x", k, rx_mem[k], (block_addr[7:0] + (k & 8'hFF)));
            $finish;
        end
    end

    $display("PASS");
    $finish;
end

endmodule
