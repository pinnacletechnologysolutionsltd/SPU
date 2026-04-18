// Chiral asymmetrical phinary adder
// 2-bit integer + 2-bit surd encoding (surd:bits[3:2], integer:bits[1:0])
// Chirality selects folding behaviour when the packed value exceeds a laminar threshold.

module chiral_phinary_adder (
    input  wire        clk,
    input  wire        rst,        // synchronous active-high reset
    input  wire [3:0]  surd_A,
    input  wire [3:0]  surd_B,
    input  wire        chirality,  // 0: normal (void flip), 1: chiral (carry into integer)
    output reg  [3:0]  surd_Sum,
    output reg         void_state,
    output reg         overflow
);

// local temporaries
reg [3:0] int_sum;   // can hold larger sums
reg [3:0] surd_sum;  // can hold larger sums
reg [4:0] sum_val;   // combined sum_val can exceed 4 bits before threshold
reg [1:0] new_int;
reg [1:0] new_surd;

// laminar threshold (encoded packing threshold)
localparam [4:0] LAMINAR_THR = 5'd10; // canonical threshold

always @(posedge clk) begin
    if (rst) begin
        surd_Sum  <= 4'b0000;
        void_state <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // compute component sums (blocking so sum_val reflects the current operands)
        int_sum  = surd_A[1:0] + surd_B[1:0];
        surd_sum = surd_A[3:2] + surd_B[3:2];
        sum_val  = (surd_sum << 2) + int_sum; // full packing before threshold

        overflow <= 1'b0;

        if (sum_val > LAMINAR_THR) begin
            overflow <= 1'b1;
            if (chirality == 1'b0) begin
                // canonical laminar fold: toggle the Janus bit and subtract threshold
                void_state <= ~void_state;
                surd_Sum <= (sum_val - LAMINAR_THR) & 4'hF;
            end else begin
                // chiral behaviour: bias carry into integer component instead of void flip
                new_int  = (int_sum + 1) & 2'b11;    // wrap in 2 bits
                new_surd = surd_sum[1:0];
                surd_Sum <= {new_surd, new_int};
            end
        end else begin
            surd_Sum <= sum_val[3:0];
        end
    end
end

endmodule
