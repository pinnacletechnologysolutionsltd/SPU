// spu_cfg_mux.v
// Configuration Multiplexer for autonomous hardware boot.
// Routes data from the `spu_hw_bootrom` to the async FIFO during boot.
// Once boot_done = 1, permanently switches control to the SPU IO bridge.

module spu_cfg_mux (
    input  wire        boot_done,

    // Port 0: Hardware Bootrom (Active when boot_done = 0)
    input  wire        hw_fifo_wr,
    input  wire [77:0] hw_fifo_data,

    // Port 1: SPU IO Bridge (Active when boot_done = 1)
    input  wire        io_fifo_wr,
    input  wire [77:0] io_fifo_data,

    // Output to spi_async_fifo
    output wire        out_fifo_wr,
    output wire [77:0] out_fifo_data
);

    assign out_fifo_wr   = boot_done ? io_fifo_wr   : hw_fifo_wr;
    assign out_fifo_data = boot_done ? io_fifo_data : hw_fifo_data;

endmodule
