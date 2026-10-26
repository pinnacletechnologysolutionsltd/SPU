// Sequential transaction proofs for the three-product Z[phi] candidate.
//
// Arithmetic equivalence remains exhaustive at 4x3.  The 8x6 task proves
// both widened signed operand paths while keeping the opposite operand narrow.
// Actual production widths are covered by directed extrema and deterministic
// random simulation in spu13_zphi_mul_serial_karatsuba_tb.v; an exhaustive
// 72x34 or 39x39 bit-vector multiplier proof is not tractable here.

`define ASSERT assert

module spu13_zphi_mul_serial_karatsuba_formal #(
    parameter X_W = 4,
    parameter Y_W = 3,
    parameter WIDTH_PLUMBING = 0
) (
    input wire clk
);
    localparam OUT_W = X_W + Y_W + 2;
    localparam PRODUCT_W = X_W + Y_W;
    localparam NARROW_W = 2;

    (* anyconst *) reg signed [X_W-1:0] xa_0, xb_0;
    (* anyconst *) reg signed [Y_W-1:0] ya_0, yb_0;
    (* anyconst *) reg signed [X_W-1:0] xa_1, xb_1;
    (* anyconst *) reg signed [Y_W-1:0] ya_1, yb_1;
    (* anyconst *) reg signed [NARROW_W-1:0] xa_1_narrow, xb_1_narrow;
    (* anyconst *) reg signed [NARROW_W-1:0] ya_0_narrow, yb_0_narrow;
    (* anyseq *) reg signed [X_W-1:0] noise_xa, noise_xb;
    (* anyseq *) reg signed [Y_W-1:0] noise_ya, noise_yb;

    reg [3:0] cycle;
    initial cycle = 0;
    always @(posedge clk) cycle <= cycle + 1'b1;

    wire rst_n = (cycle != 0);
    // Cycles 2 and 7 deliberately collide with an active transaction in the
    // exhaustive semantic proof.  The wider plumbing task retains its prior
    // two-start trace to keep the signed-width multiplication solve bounded.
    wire semantic_start = (cycle == 1) || (cycle == 2) ||
                          (cycle == 6) || (cycle == 7);
    wire start = WIDTH_PLUMBING ? ((cycle == 1) || (cycle == 6))
                                : semantic_start;
    wire signed [X_W-1:0] xa_1_selected = WIDTH_PLUMBING ?
        {{(X_W-NARROW_W){xa_1_narrow[NARROW_W-1]}}, xa_1_narrow} : xa_1;
    wire signed [X_W-1:0] xb_1_selected = WIDTH_PLUMBING ?
        {{(X_W-NARROW_W){xb_1_narrow[NARROW_W-1]}}, xb_1_narrow} : xb_1;
    wire signed [Y_W-1:0] ya_0_selected = WIDTH_PLUMBING ?
        {{(Y_W-NARROW_W){ya_0_narrow[NARROW_W-1]}}, ya_0_narrow} : ya_0;
    wire signed [Y_W-1:0] yb_0_selected = WIDTH_PLUMBING ?
        {{(Y_W-NARROW_W){yb_0_narrow[NARROW_W-1]}}, yb_0_narrow} : yb_0;

    // Only accepted idle-start cycles present transaction operands in the
    // semantic proof.  Every busy cycle sees arbitrary external changes.  The
    // wider plumbing task holds each operand tuple stable, as in the original
    // tractable 8x6 proof, while the 72x34/39x39 simulation mutates full-width
    // operands directly.
    wire signed [X_W-1:0] semantic_xa = (cycle == 1) ? xa_0 :
                                      (cycle == 6) ? xa_1_selected : noise_xa;
    wire signed [X_W-1:0] semantic_xb = (cycle == 1) ? xb_0 :
                                      (cycle == 6) ? xb_1_selected : noise_xb;
    wire signed [Y_W-1:0] semantic_ya = (cycle == 1) ? ya_0_selected :
                                      (cycle == 6) ? ya_1 : noise_ya;
    wire signed [Y_W-1:0] semantic_yb = (cycle == 1) ? yb_0_selected :
                                      (cycle == 6) ? yb_1 : noise_yb;
    wire second_transaction = (cycle >= 6);
    wire signed [X_W-1:0] xa = WIDTH_PLUMBING ?
        (second_transaction ? xa_1_selected : xa_0) : semantic_xa;
    wire signed [X_W-1:0] xb = WIDTH_PLUMBING ?
        (second_transaction ? xb_1_selected : xb_0) : semantic_xb;
    wire signed [Y_W-1:0] ya = WIDTH_PLUMBING ?
        (second_transaction ? ya_1 : ya_0_selected) : semantic_ya;
    wire signed [Y_W-1:0] yb = WIDTH_PLUMBING ?
        (second_transaction ? yb_1 : yb_0_selected) : semantic_yb;

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

    function signed [OUT_W-1:0] mul_ext;
        input signed [X_W-1:0] fx;
        input signed [Y_W-1:0] fy;
        reg signed [PRODUCT_W-1:0] raw;
        begin
            raw = fx * fy;
            mul_ext = {{(OUT_W-PRODUCT_W){raw[PRODUCT_W-1]}}, raw};
        end
    endfunction

    wire signed [OUT_W-1:0] expected_a_0 =
        mul_ext(xa_0, ya_0_selected) + mul_ext(xb_0, yb_0_selected);
    wire signed [OUT_W-1:0] expected_b_0 =
        mul_ext(xa_0, yb_0_selected) + mul_ext(xb_0, ya_0_selected) +
        mul_ext(xb_0, yb_0_selected);
    wire signed [OUT_W-1:0] expected_a_1 =
        mul_ext(xa_1_selected, ya_1) + mul_ext(xb_1_selected, yb_1);
    wire signed [OUT_W-1:0] expected_b_1 =
        mul_ext(xa_1_selected, yb_1) + mul_ext(xb_1_selected, ya_1) +
        mul_ext(xb_1_selected, yb_1);

    reg signed [OUT_W-1:0] saved_fast_a, saved_fast_b;
    reg signed [OUT_W-1:0] saved_ref_a, saved_ref_b;
    initial begin
        saved_fast_a = 0;
        saved_fast_b = 0;
        saved_ref_a = 0;
        saved_ref_b = 0;
    end

    always @(posedge clk) begin
        if (rst_n) begin
            if (cycle >= 1 && cycle <= 12) begin
                // Exact busy windows pin three versus four evaluation cycles.
                `ASSERT(fast_busy == (((cycle >= 2) && (cycle <= 4)) ||
                                      ((cycle >= 7) && (cycle <= 9))));
                `ASSERT(ref_busy == (((cycle >= 2) && (cycle <= 5)) ||
                                     ((cycle >= 7) && (cycle <= 10))));
                `ASSERT(fast_done == ((cycle == 5) || (cycle == 10)));
                `ASSERT(ref_done == ((cycle == 6) || (cycle == 11)));
            end

            // Because every post-acceptance input is arbitrary anyseq noise
            // and cycles 2/7 also assert start, these golden-result checks
            // externally prove operand capture and ignored busy starts.
            if (fast_done) begin
                `ASSERT(!fast_busy);
                if ((cycle == 5) && !WIDTH_PLUMBING) begin
                    `ASSERT(fast_a == expected_a_0);
                    `ASSERT(fast_b == expected_b_0);
                end else if (!WIDTH_PLUMBING) begin
                    `ASSERT(cycle == 10);
                    `ASSERT(fast_a == expected_a_1);
                    `ASSERT(fast_b == expected_b_1);
                end
                saved_fast_a <= fast_a;
                saved_fast_b <= fast_b;
            end

            if (ref_done) begin
                `ASSERT(!ref_busy);
                if ((cycle == 6) && !WIDTH_PLUMBING) begin
                    `ASSERT(ref_a == expected_a_0);
                    `ASSERT(ref_b == expected_b_0);
                end else if (!WIDTH_PLUMBING) begin
                    `ASSERT(cycle == 11);
                    `ASSERT(ref_a == expected_a_1);
                    `ASSERT(ref_b == expected_b_1);
                end
                `ASSERT(saved_fast_a == ref_a);
                `ASSERT(saved_fast_b == ref_b);
                saved_ref_a <= ref_a;
                saved_ref_b <= ref_b;
            end

            // Registered results remain stable throughout the next operation
            // until that implementation's own done edge.
            if (cycle >= 6 && cycle <= 9) begin
                `ASSERT(fast_a == saved_fast_a);
                `ASSERT(fast_b == saved_fast_b);
            end
            if (cycle >= 7 && cycle <= 10) begin
                `ASSERT(ref_a == saved_ref_a);
                `ASSERT(ref_b == saved_ref_b);
            end
        end
    end
endmodule

// A separate bounded trace resets both implementations during phase 1, proves
// that the aborted transaction cannot complete later, and then proves an
// independent recovery transaction with the original latency relationship.
module spu13_zphi_mul_serial_karatsuba_reset_formal #(
    parameter X_W = 4,
    parameter Y_W = 3
) (
    input wire clk
);
    localparam OUT_W = X_W + Y_W + 2;
    localparam PRODUCT_W = X_W + Y_W;

    (* anyconst *) reg signed [X_W-1:0] abort_xa, abort_xb;
    (* anyconst *) reg signed [Y_W-1:0] abort_ya, abort_yb;
    (* anyconst *) reg signed [X_W-1:0] recover_xa, recover_xb;
    (* anyconst *) reg signed [Y_W-1:0] recover_ya, recover_yb;
    (* anyseq *) reg signed [X_W-1:0] noise_xa, noise_xb;
    (* anyseq *) reg signed [Y_W-1:0] noise_ya, noise_yb;

    reg [3:0] cycle;
    initial cycle = 0;
    always @(posedge clk) cycle <= cycle + 1'b1;

    wire rst_n = (cycle != 0) && (cycle != 3);
    wire start = (cycle == 1) || (cycle == 5);
    wire signed [X_W-1:0] xa = (cycle == 1) ? abort_xa :
                                      (cycle == 5) ? recover_xa : noise_xa;
    wire signed [X_W-1:0] xb = (cycle == 1) ? abort_xb :
                                      (cycle == 5) ? recover_xb : noise_xb;
    wire signed [Y_W-1:0] ya = (cycle == 1) ? abort_ya :
                                      (cycle == 5) ? recover_ya : noise_ya;
    wire signed [Y_W-1:0] yb = (cycle == 1) ? abort_yb :
                                      (cycle == 5) ? recover_yb : noise_yb;

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

    function signed [OUT_W-1:0] mul_ext;
        input signed [X_W-1:0] fx;
        input signed [Y_W-1:0] fy;
        reg signed [PRODUCT_W-1:0] raw;
        begin
            raw = fx * fy;
            mul_ext = {{(OUT_W-PRODUCT_W){raw[PRODUCT_W-1]}}, raw};
        end
    endfunction

    wire signed [OUT_W-1:0] expected_a =
        mul_ext(recover_xa, recover_ya) + mul_ext(recover_xb, recover_yb);
    wire signed [OUT_W-1:0] expected_b =
        mul_ext(recover_xa, recover_yb) + mul_ext(recover_xb, recover_ya) +
        mul_ext(recover_xb, recover_yb);

    reg signed [OUT_W-1:0] saved_fast_a, saved_fast_b;
    initial begin
        saved_fast_a = 0;
        saved_fast_b = 0;
    end

    always @(posedge clk) begin
        if (cycle == 4) begin
            `ASSERT(!ref_busy && !fast_busy);
            `ASSERT(!ref_done && !fast_done);
            `ASSERT(ref_a == 0 && ref_b == 0);
            `ASSERT(fast_a == 0 && fast_b == 0);
        end
        if (cycle == 5) begin
            `ASSERT(!ref_busy && !fast_busy);
            `ASSERT(!ref_done && !fast_done);
        end
        if (cycle >= 6 && cycle <= 8)
            `ASSERT(ref_busy && fast_busy && !ref_done && !fast_done);
        if (cycle == 9) begin
            `ASSERT(fast_done && !fast_busy);
            `ASSERT(ref_busy && !ref_done);
            `ASSERT(fast_a == expected_a && fast_b == expected_b);
            saved_fast_a <= fast_a;
            saved_fast_b <= fast_b;
        end
        if (cycle == 10) begin
            `ASSERT(!fast_done && !fast_busy);
            `ASSERT(ref_done && !ref_busy);
            `ASSERT(ref_a == expected_a && ref_b == expected_b);
            `ASSERT(saved_fast_a == ref_a && saved_fast_b == ref_b);
        end
        if (cycle == 11) begin
            `ASSERT(!fast_done && !ref_done);
            `ASSERT(!fast_busy && !ref_busy);
            `ASSERT(fast_a == expected_a && fast_b == expected_b);
            `ASSERT(ref_a == expected_a && ref_b == expected_b);
        end
    end
endmodule
