// SPU-13 Serial Multiplier (v1.0 Ephemeralized)
// Target: iCE40LP1K (iCeSugar Nano)
// Objective: 16x16 -> 32-bit multiply using minimal LUTs.
// Speed: 16 cycles per 'Sip'.

module spu_serial_multiplier (
    input  wire        clk,
    input  wire        reset,
    input  wire [15:0] a,
    input  wire [15:0] b,
    input  wire        start,
    output reg  [31:0] product,
    output wire        ready
);

    reg [3:0]  count;
    reg [15:0] shift_a;
    reg [31:0] shift_b;
    reg        busy;

    assign ready = !busy;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            product <= 32'b0;
            count <= 0;
            busy <= 0;
            shift_a <= 0;
            shift_b <= 0;
        end else if (start && !busy) begin
            busy <= 1;
            count <= 0;
            product <= 32'b0;
            shift_a <= a;
            shift_b <= {16'b0, b};
        end else if (busy) begin
            if (shift_a[0]) begin
                product <= product + shift_b;
            end
            shift_a <= shift_a >> 1;
            shift_b <= shift_b << 1;
            count <= count + 1;
            if (count == 15) busy <= 0;
        end
    end

endmodule
