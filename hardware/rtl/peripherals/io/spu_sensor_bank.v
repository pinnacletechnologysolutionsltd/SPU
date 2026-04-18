// spu_sensor_bank.v — Rational Sensor Bank  v1.1
// Stores up to 8 RationalSurd sensor readings (32-bit each: P[31:16] Q[15:0]).
// Addresses 0x80–0x87 on the SovereignBus.
// Supports both write (sensor DMA/inject) and read (manifold query).

`default_nettype none

module spu_sensor_bank #(
    parameter BASE_ADDR = 8'h80   // First sensor address
)(
    input  wire        clk,
    input  wire        reset,

    // SovereignBus slave
    input  wire [7:0]  bus_addr,
    input  wire [31:0] bus_wdata,
    input  wire        bus_wen,
    input  wire        bus_ren,
    output reg  [31:0] bus_rdata,
    output reg         bus_ready
);

    // 8 × 32-bit sensor registers
    reg [31:0] regs [0:7];
    integer i;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            for (i = 0; i < 8; i = i + 1)
                regs[i] <= 32'h00010000;  // unity RationalSurd (1 + 0·√3)
            bus_ready <= 1'b0;
            bus_rdata <= 32'h0;
        end else begin
            bus_ready <= 1'b0;

            if (bus_wen && bus_addr >= BASE_ADDR && bus_addr < BASE_ADDR + 8) begin
                regs[bus_addr - BASE_ADDR] <= bus_wdata;
                bus_ready <= 1'b1;
            end

            if (bus_ren && bus_addr >= BASE_ADDR && bus_addr < BASE_ADDR + 8) begin
                bus_rdata <= regs[bus_addr - BASE_ADDR];
                bus_ready <= 1'b1;
            end
        end
    end

endmodule
`default_nettype wire
