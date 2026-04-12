// Parameterized chiral phinary adder for SPU-4 (phinary-aware)
// WIDTH: total packed width (integer+surd)
// INT_BITS: number of integer bits (lower bits); SURD_BITS = WIDTH-INT_BITS
// LAMINAR_THR: numeric threshold in the packed domain (default: 10 << INT_BITS)

module chiral_phinary_adder_param #(
    parameter WIDTH = 16,
    parameter INT_BITS = 8,
    parameter LAMINAR_THR = (10 << INT_BITS)
) (
    input  wire                  clk,
    input  wire                  rst,        // synchronous active-high reset
    input  wire [WIDTH-1:0]      surd_A,
    input  wire [WIDTH-1:0]      surd_B,
    input  wire                  chirality,  // 0: canonical (void flip), 1: chiral (carry into integer)
    output reg  [WIDTH-1:0]      surd_Sum,
    output reg                   void_state,
    output reg                   overflow
);

localparam SURD_BITS = WIDTH - INT_BITS;

// Internal widths
reg [INT_BITS:0] int_sum;         // INT_BITS + 1
reg [SURD_BITS:0] surd_sum;       // SURD_BITS + 1
reg [WIDTH:0]      sum_val;       // combined value with +1 guard
reg [INT_BITS-1:0] new_int;
reg [SURD_BITS-1:0] new_surd;
reg [WIDTH:0] tmp_diff;

integer i;

always @(posedge clk) begin
    if (rst) begin
        surd_Sum  <= {WIDTH{1'b0}};
        void_state <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // extract components
        int_sum  = surd_A[INT_BITS-1:0] + surd_B[INT_BITS-1:0];
        surd_sum = surd_A[WIDTH-1:INT_BITS] + surd_B[WIDTH-1:INT_BITS];

        // pack into single wide integer for comparison
        // simple and portable packing: shift the surd component into the high bits
        sum_val = (surd_sum << INT_BITS) + int_sum;

        overflow <= 1'b0;

        if (sum_val > LAMINAR_THR) begin
            overflow <= 1'b1;
            if (chirality == 1'b0) begin
                // canonical laminar fold: toggle the Janus bit and subtract threshold
                tmp_diff = sum_val - LAMINAR_THR;
                void_state <= ~void_state;
                surd_Sum <= tmp_diff[WIDTH-1:0];
            end else begin
                // chiral behaviour: bias carry into integer component instead of void flip
                new_int  = (int_sum + 1) & ((1<<INT_BITS)-1);
                new_surd = surd_sum[SURD_BITS-1:0];
                surd_Sum <= {new_surd, new_int};
            end
        end else begin
            surd_Sum <= sum_val[WIDTH-1:0];
        end
    end
end

endmodule
