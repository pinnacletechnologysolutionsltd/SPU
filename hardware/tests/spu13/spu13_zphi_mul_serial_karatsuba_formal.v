// Reduced-width sequential equivalence proof for the three-product candidate.
// The unrestricted signed identity is documented separately; reduced widths
// make exhaustive bit-vector multiplication tractable for the formal engine.

`define ASSERT assert

module spu13_zphi_mul_serial_karatsuba_formal (
    input wire clk
);
    localparam X_W = 4;
    localparam Y_W = 3;
    localparam OUT_W = X_W + Y_W + 2;

    (* anyconst *) reg signed [X_W-1:0] xa;
    (* anyconst *) reg signed [X_W-1:0] xb;
    (* anyconst *) reg signed [Y_W-1:0] ya;
    (* anyconst *) reg signed [Y_W-1:0] yb;

    reg [3:0] cycle;
    initial cycle = 0;
    always @(posedge clk) cycle <= cycle + 1'b1;

    wire rst_n = (cycle != 0);
    wire start = (cycle == 1);

    wire ref_busy, ref_done, fast_busy, fast_done;
    wire signed [OUT_W-1:0] ref_a, ref_b, fast_a, fast_b;

    spu13_zphi_mul_serial #(
        .X_W(X_W), .Y_W(Y_W), .OUT_W(OUT_W)
    ) u_ref (
        .clk(clk), .rst_n(rst_n), .start(start),
        .xa(xa), .xb(xb), .ya(ya), .yb(yb),
        .busy(ref_busy), .done(ref_done), .out_a(ref_a), .out_b(ref_b)
    );

    spu13_zphi_mul_serial_karatsuba #(
        .X_W(X_W), .Y_W(Y_W), .OUT_W(OUT_W)
    ) u_fast (
        .clk(clk), .rst_n(rst_n), .start(start),
        .xa(xa), .xb(xb), .ya(ya), .yb(yb),
        .busy(fast_busy), .done(fast_done), .out_a(fast_a), .out_b(fast_b)
    );

    reg saw_fast;
    reg signed [OUT_W-1:0] saved_a, saved_b;
    initial begin
        saw_fast = 0;
        saved_a = 0;
        saved_b = 0;
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            saw_fast <= 0;
        end else begin
            if (fast_done) begin
                `ASSERT(!fast_busy);
                `ASSERT(cycle == 5);
                saw_fast <= 1;
                saved_a <= fast_a;
                saved_b <= fast_b;
            end
            if (ref_done) begin
                `ASSERT(!ref_busy);
                `ASSERT(cycle == 6);
                `ASSERT(saw_fast);
                `ASSERT(saved_a == ref_a);
                `ASSERT(saved_b == ref_b);
            end
            if (cycle == 6)
                `ASSERT(ref_done);
        end
    end
endmodule
