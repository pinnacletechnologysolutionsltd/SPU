// Reduced-width sequential equivalence proof for the three-product candidate.
// The unrestricted signed identity is documented separately; reduced widths
// make exhaustive bit-vector multiplication tractable for the formal engine.
// Two independent transactions exercise return-to-idle and operand recapture.
// At the wider configuration, transaction 0 spans full-width X and narrow Y;
// transaction 1 spans narrow X and full-width Y.  This checks both widened
// operand paths and their signed carry bits without an impractical full-domain
// 8x6 distributivity solve.

`define ASSERT assert

module spu13_zphi_mul_serial_karatsuba_formal #(
    parameter X_W = 4,
    parameter Y_W = 3,
    parameter WIDTH_PLUMBING = 0
) (
    input wire clk
);
    localparam OUT_W = X_W + Y_W + 2;
    localparam NARROW_W = 2;

    (* anyconst *) reg signed [X_W-1:0] xa_0, xb_0;
    (* anyconst *) reg signed [Y_W-1:0] ya_0, yb_0;
    (* anyconst *) reg signed [X_W-1:0] xa_1, xb_1;
    (* anyconst *) reg signed [Y_W-1:0] ya_1, yb_1;
    (* anyconst *) reg signed [NARROW_W-1:0] xa_1_narrow, xb_1_narrow;
    (* anyconst *) reg signed [NARROW_W-1:0] ya_0_narrow, yb_0_narrow;

    reg [3:0] cycle;
    initial cycle = 0;
    always @(posedge clk) cycle <= cycle + 1'b1;

    wire rst_n = (cycle != 0);
    wire start = (cycle == 1) || (cycle == 6);
    wire second_transaction = (cycle >= 6);
    wire signed [X_W-1:0] xa_1_selected = WIDTH_PLUMBING ?
        {{(X_W-NARROW_W){xa_1_narrow[NARROW_W-1]}}, xa_1_narrow} : xa_1;
    wire signed [X_W-1:0] xb_1_selected = WIDTH_PLUMBING ?
        {{(X_W-NARROW_W){xb_1_narrow[NARROW_W-1]}}, xb_1_narrow} : xb_1;
    wire signed [Y_W-1:0] ya_0_selected = WIDTH_PLUMBING ?
        {{(Y_W-NARROW_W){ya_0_narrow[NARROW_W-1]}}, ya_0_narrow} : ya_0;
    wire signed [Y_W-1:0] yb_0_selected = WIDTH_PLUMBING ?
        {{(Y_W-NARROW_W){yb_0_narrow[NARROW_W-1]}}, yb_0_narrow} : yb_0;
    wire signed [X_W-1:0] xa = second_transaction ? xa_1_selected : xa_0;
    wire signed [X_W-1:0] xb = second_transaction ? xb_1_selected : xb_0;
    wire signed [Y_W-1:0] ya = second_transaction ? ya_1 : ya_0_selected;
    wire signed [Y_W-1:0] yb = second_transaction ? yb_1 : yb_0_selected;

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
                `ASSERT((cycle == 5) || (cycle == 10));
                saw_fast <= 1;
                saved_a <= fast_a;
                saved_b <= fast_b;
            end
            if (ref_done) begin
                `ASSERT(!ref_busy);
                `ASSERT((cycle == 6) || (cycle == 11));
                `ASSERT(saw_fast);
                `ASSERT(saved_a == ref_a);
                `ASSERT(saved_b == ref_b);
                saw_fast <= 0;
            end
            if (cycle == 6) begin
                `ASSERT(ref_done);
                `ASSERT(!ref_busy);
                `ASSERT(!fast_busy);
                `ASSERT(!fast_done);
                `ASSERT(start);
            end
            if (cycle == 7) begin
                `ASSERT(ref_busy);
                `ASSERT(fast_busy);
                `ASSERT(!ref_done);
                `ASSERT(!fast_done);
            end
            if (cycle == 11)
                `ASSERT(ref_done);
        end
    end
endmodule
