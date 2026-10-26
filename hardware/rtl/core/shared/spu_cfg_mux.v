// spu_cfg_mux.v
// Configuration Multiplexer for autonomous hardware boot.
// Routes legacy 78-bit bootrom records to the 85-bit RPLU CDC payload during
// boot. Once boot_done = 1, permanently switches control to the SPU IO bridge.

module spu_cfg_mux (
    input  wire        boot_done,

    // Port 0: Hardware Bootrom (Active when boot_done = 0)
    input  wire        hw_fifo_wr,
    input  wire [77:0] hw_fifo_data,

    // Port 1: SPU IO Bridge (Active when boot_done = 1)
    input  wire        io_fifo_wr,
    input  wire [84:0] io_fifo_data,

    // Output to spi_async_fifo
    output wire        out_fifo_wr,
    output wire [84:0] out_fifo_data
);

    wire [84:0] hw_fifo_data_wide;
    assign hw_fifo_data_wide = {
        hw_fifo_data[77:75],
        7'd0, hw_fifo_data[74],
        hw_fifo_data[73:64],
        hw_fifo_data[63:0]
    };

    assign out_fifo_wr   = boot_done ? io_fifo_wr   : hw_fifo_wr;
    assign out_fifo_data = boot_done ? io_fifo_data : hw_fifo_data_wide;

endmodule
