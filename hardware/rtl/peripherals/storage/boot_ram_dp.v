`timescale 1ns / 1ps

// boot_ram_dp.v — dual-clock, single-write-port, single-read-port boot RAM
// Write port: clk_write domain (used by sd_bram_loader)
// Read  port: clk_read domain  (used by SPU-4 sentinel fetch)

module boot_ram_dp #(
    parameter ADDR_WIDTH = 10,
    parameter DATA_WIDTH = 24
) (
    input  wire                      clk_write,
    input  wire                      we,
    input  wire [ADDR_WIDTH-1:0]     addr_write,
    input  wire [DATA_WIDTH-1:0]     write_data,

    input  wire                      clk_read,
    input  wire [ADDR_WIDTH-1:0]     addr_read,
    output reg  [DATA_WIDTH-1:0]     read_data
);

    localparam DEPTH = (1 << ADDR_WIDTH);

    // Hint synthesis tools to map this array to block RAM on supported flows.
    (* ram_style = "block", keep = "true", dont_touch = "true" *) reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
    integer i;
    initial begin
        for (i = 0; i < DEPTH; i = i + 1) begin
            mem[i] = {DATA_WIDTH{1'b0}};
        end
    end

    // write port (synchronous to clk_write)
    always @(posedge clk_write) begin
        if (we) mem[addr_write] <= write_data;
    end

    // read port (synchronous to clk_read) — one-cycle latency
    always @(posedge clk_read) begin
        read_data <= mem[addr_read];
    end

endmodule
