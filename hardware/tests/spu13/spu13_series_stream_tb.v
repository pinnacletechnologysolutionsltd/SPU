`timescale 1ns / 1ps

// spu13_series_stream_tb.v — Golden-vector testbench for series stream controller
//
// Tests against 3 vectors generated from the Python oracle
// (jet_ring_N.py × digon_recursive.py).  Each vector provides
// Taylor-shifted coefficients c0,c1,c2 and the expected series root x.
//
// The DUT uses two shared-resource instances:
//   u_inverter — spu13_fp4_inverter (with private multiplier u_tmult)
//   u_dut      — spu13_series_stream (with private multiplier u_jmult)

module spu13_series_stream_tb;

    reg clk, rst_n, start;

    // ── Coefficient inputs (3 jets = 36 × 32-bit wires) ─────────────
    reg [31:0] c0_o0_z0, c0_o0_z1, c0_o0_z2, c0_o0_z3;
    reg [31:0] c0_o1_z0, c0_o1_z1, c0_o1_z2, c0_o1_z3;
    reg [31:0] c0_o2_z0, c0_o2_z1, c0_o2_z2, c0_o2_z3;

    reg [31:0] c1_o0_z0, c1_o0_z1, c1_o0_z2, c1_o0_z3;
    reg [31:0] c1_o1_z0, c1_o1_z1, c1_o1_z2, c1_o1_z3;
    reg [31:0] c1_o2_z0, c1_o2_z1, c1_o2_z2, c1_o2_z3;

    reg [31:0] c2_o0_z0, c2_o0_z1, c2_o0_z2, c2_o0_z3;
    reg [31:0] c2_o1_z0, c2_o1_z1, c2_o1_z2, c2_o1_z3;
    reg [31:0] c2_o2_z0, c2_o2_z1, c2_o2_z2, c2_o2_z3;

    // ── Output ──────────────────────────────────────────────────────
    wire [31:0] x_o0_z0, x_o0_z1, x_o0_z2, x_o0_z3;
    wire [31:0] x_o1_z0, x_o1_z1, x_o1_z2, x_o1_z3;
    wire [31:0] x_o2_z0, x_o2_z1, x_o2_z2, x_o2_z3;
    wire done, err_singular;

    // ── Inverter interface ───────────────────────────────────────────
    wire        inv_start;
    wire [31:0] inv_z0, inv_z1, inv_z2, inv_z3;
    wire [31:0] inv_r0, inv_r1, inv_r2, inv_r3;
    wire        inv_done, inv_flags_v;

    // Tower's private multiplier
    wire        tmult_start;
    wire [31:0] tmult_a0, tmult_a1, tmult_a2, tmult_a3;
    wire [31:0] tmult_b0, tmult_b1, tmult_b2, tmult_b3;
    wire [31:0] tmult_r0, tmult_r1, tmult_r2, tmult_r3;
    wire        tmult_done, tmult_busy;

    // ── Controller's multiplier interface ────────────────────────────
    wire        jmult_start;
    wire [31:0] jmult_a0, jmult_a1, jmult_a2, jmult_a3;
    wire [31:0] jmult_b0, jmult_b1, jmult_b2, jmult_b3;
    wire [31:0] jmult_r0, jmult_r1, jmult_r2, jmult_r3;
    wire        jmult_done;

    // ── DUT: Series stream controller ────────────────────────────────
    spu13_series_stream u_dut (
        .clk(clk), .rst_n(rst_n), .start(start),

        .c0_o0_z0(c0_o0_z0), .c0_o0_z1(c0_o0_z1),
        .c0_o0_z2(c0_o0_z2), .c0_o0_z3(c0_o0_z3),
        .c0_o1_z0(c0_o1_z0), .c0_o1_z1(c0_o1_z1),
        .c0_o1_z2(c0_o1_z2), .c0_o1_z3(c0_o1_z3),
        .c0_o2_z0(c0_o2_z0), .c0_o2_z1(c0_o2_z1),
        .c0_o2_z2(c0_o2_z2), .c0_o2_z3(c0_o2_z3),

        .c1_o0_z0(c1_o0_z0), .c1_o0_z1(c1_o0_z1),
        .c1_o0_z2(c1_o0_z2), .c1_o0_z3(c1_o0_z3),
        .c1_o1_z0(c1_o1_z0), .c1_o1_z1(c1_o1_z1),
        .c1_o1_z2(c1_o1_z2), .c1_o1_z3(c1_o1_z3),
        .c1_o2_z0(c1_o2_z0), .c1_o2_z1(c1_o2_z1),
        .c1_o2_z2(c1_o2_z2), .c1_o2_z3(c1_o2_z3),

        .c2_o0_z0(c2_o0_z0), .c2_o0_z1(c2_o0_z1),
        .c2_o0_z2(c2_o0_z2), .c2_o0_z3(c2_o0_z3),
        .c2_o1_z0(c2_o1_z0), .c2_o1_z1(c2_o1_z1),
        .c2_o1_z2(c2_o1_z2), .c2_o1_z3(c2_o1_z3),
        .c2_o2_z0(c2_o2_z0), .c2_o2_z1(c2_o2_z1),
        .c2_o2_z2(c2_o2_z2), .c2_o2_z3(c2_o2_z3),

        .x_o0_z0(x_o0_z0), .x_o0_z1(x_o0_z1),
        .x_o0_z2(x_o0_z2), .x_o0_z3(x_o0_z3),
        .x_o1_z0(x_o1_z0), .x_o1_z1(x_o1_z1),
        .x_o1_z2(x_o1_z2), .x_o1_z3(x_o1_z3),
        .x_o2_z0(x_o2_z0), .x_o2_z1(x_o2_z1),
        .x_o2_z2(x_o2_z2), .x_o2_z3(x_o2_z3),
        .done(done), .err_singular(err_singular),

        .inv_start(inv_start),
        .inv_z0(inv_z0), .inv_z1(inv_z1),
        .inv_z2(inv_z2), .inv_z3(inv_z3),
        .inv_r0(inv_r0), .inv_r1(inv_r1),
        .inv_r2(inv_r2), .inv_r3(inv_r3),
        .inv_done(inv_done), .inv_flags_v(inv_flags_v),

        .mult_start(jmult_start),
        .mult_a0(jmult_a0), .mult_a1(jmult_a1),
        .mult_a2(jmult_a2), .mult_a3(jmult_a3),
        .mult_b0(jmult_b0), .mult_b1(jmult_b1),
        .mult_b2(jmult_b2), .mult_b3(jmult_b3),
        .mult_r0(jmult_r0), .mult_r1(jmult_r1),
        .mult_r2(jmult_r2), .mult_r3(jmult_r3),
        .mult_done(jmult_done)
    );

    // ── Fp4 inverter (tower) with private multiplier ─────────────────
    spu13_fp4_inverter u_inverter (
        .clk(clk), .rst_n(rst_n), .start(inv_start),
        .z0(inv_z0), .z1(inv_z1), .z2(inv_z2), .z3(inv_z3),
        .inv0(inv_r0), .inv1(inv_r1), .inv2(inv_r2), .inv3(inv_r3),
        .done(inv_done), .busy(), .flags_v(inv_flags_v),
        .mult_start(tmult_start),
        .mult_a0(tmult_a0), .mult_a1(tmult_a1),
        .mult_a2(tmult_a2), .mult_a3(tmult_a3),
        .mult_b0(tmult_b0), .mult_b1(tmult_b1),
        .mult_b2(tmult_b2), .mult_b3(tmult_b3),
        .mult_r0(tmult_r0), .mult_r1(tmult_r1),
        .mult_r2(tmult_r2), .mult_r3(tmult_r3),
        .mult_done(tmult_done), .mult_busy(tmult_busy)
    );

    // ── Tower multiplier ─────────────────────────────────────────────
    spu13_m31_multiplier u_tmult (
        .clk(clk), .rst_n(rst_n), .start(tmult_start),
        .a0(tmult_a0), .a1(tmult_a1), .a2(tmult_a2), .a3(tmult_a3),
        .b0(tmult_b0), .b1(tmult_b1), .b2(tmult_b2), .b3(tmult_b3),
        .r0(tmult_r0), .r1(tmult_r1), .r2(tmult_r2), .r3(tmult_r3),
        .done(tmult_done), .busy(tmult_busy), .rns_error()
    );

    // ── Jet multiplier (controller's private) ────────────────────────
    spu13_m31_multiplier u_jmult (
        .clk(clk), .rst_n(rst_n), .start(jmult_start),
        .a0(jmult_a0), .a1(jmult_a1), .a2(jmult_a2), .a3(jmult_a3),
        .b0(jmult_b0), .b1(jmult_b1), .b2(jmult_b2), .b3(jmult_b3),
        .r0(jmult_r0), .r1(jmult_r1), .r2(jmult_r2), .r3(jmult_r3),
        .done(jmult_done), .busy(), .rns_error()
    );

    // ── Clock ────────────────────────────────────────────────────────
    always #5 clk = ~clk;

    // ── Resource pulse counters ──────────────────────────────────────
    // The point of the static-schedule design: exactly 27 shared-mult
    // launches and 1 tower launch per evaluation, data-independent.
    // (27 includes the dead product at schedule slot 19 — tighten to 26
    // when that slot is trimmed.)  Singular input: 1 tower, 0 mults.
    integer mult_pulses = 0, inv_pulses = 0;
    integer mult_mark = 0, inv_mark = 0;
    always @(posedge clk) begin
        if (jmult_start) mult_pulses = mult_pulses + 1;
        if (inv_start)   inv_pulses  = inv_pulses + 1;
    end

    // ── Test harness ─────────────────────────────────────────────────
    integer test_pass, test_total;

    task set_c0_jet;
        input [31:0] o0z0,o0z1,o0z2,o0z3, o1z0,o1z1,o1z2,o1z3, o2z0,o2z1,o2z2,o2z3;
        begin
            c0_o0_z0=o0z0; c0_o0_z1=o0z1; c0_o0_z2=o0z2; c0_o0_z3=o0z3;
            c0_o1_z0=o1z0; c0_o1_z1=o1z1; c0_o1_z2=o1z2; c0_o1_z3=o1z3;
            c0_o2_z0=o2z0; c0_o2_z1=o2z1; c0_o2_z2=o2z2; c0_o2_z3=o2z3;
        end
    endtask

    task set_c1_jet;
        input [31:0] o0z0,o0z1,o0z2,o0z3, o1z0,o1z1,o1z2,o1z3, o2z0,o2z1,o2z2,o2z3;
        begin
            c1_o0_z0=o0z0; c1_o0_z1=o0z1; c1_o0_z2=o0z2; c1_o0_z3=o0z3;
            c1_o1_z0=o1z0; c1_o1_z1=o1z1; c1_o1_z2=o1z2; c1_o1_z3=o1z3;
            c1_o2_z0=o2z0; c1_o2_z1=o2z1; c1_o2_z2=o2z2; c1_o2_z3=o2z3;
        end
    endtask

    task set_c2_jet;
        input [31:0] o0z0,o0z1,o0z2,o0z3, o1z0,o1z1,o1z2,o1z3, o2z0,o2z1,o2z2,o2z3;
        begin
            c2_o0_z0=o0z0; c2_o0_z1=o0z1; c2_o0_z2=o0z2; c2_o0_z3=o0z3;
            c2_o1_z0=o1z0; c2_o1_z1=o1z1; c2_o1_z2=o1z2; c2_o1_z3=o1z3;
            c2_o2_z0=o2z0; c2_o2_z1=o2z1; c2_o2_z2=o2z2; c2_o2_z3=o2z3;
        end
    endtask

    task run_stream;
        begin
            mult_mark = mult_pulses;
            inv_mark  = inv_pulses;
            start = 1; #10; start = 0;
            wait(done); #2;
        end
    endtask

    task check_counts;
        input [255:0] label;
        input integer exp_mults;
        begin
            test_total = test_total + 1;
            if ((mult_pulses - mult_mark) === exp_mults &&
                (inv_pulses - inv_mark) === 1)
                test_pass = test_pass + 1;
            else
                $display("FAIL: %0s counts: %0d mults / %0d towers, expected %0d / 1",
                         label, mult_pulses - mult_mark,
                         inv_pulses - inv_mark, exp_mults);
        end
    endtask

    task check_jet;
        input [255:0] label;
        input [31:0] e00,e01,e02,e03, e10,e11,e12,e13, e20,e21,e22,e23;
        integer ok;
        begin
            test_total = test_total + 1;
            ok = (x_o0_z0===e00 && x_o0_z1===e01 && x_o0_z2===e02 && x_o0_z3===e03 &&
                  x_o1_z0===e10 && x_o1_z1===e11 && x_o1_z2===e12 && x_o1_z3===e13 &&
                  x_o2_z0===e20 && x_o2_z1===e21 && x_o2_z2===e22 && x_o2_z3===e23);
            if (ok) test_pass = test_pass + 1;
            else begin
                $display("FAIL: %0s", label);
                $display("  x0=(%h,%h,%h,%h) exp=(%h,%h,%h,%h)",
                    x_o0_z0,x_o0_z1,x_o0_z2,x_o0_z3, e00,e01,e02,e03);
                $display("  x1=(%h,%h,%h,%h) exp=(%h,%h,%h,%h)",
                    x_o1_z0,x_o1_z1,x_o1_z2,x_o1_z3, e10,e11,e12,e13);
                $display("  x2=(%h,%h,%h,%h) exp=(%h,%h,%h,%h)",
                    x_o2_z0,x_o2_z1,x_o2_z2,x_o2_z3, e20,e21,e22,e23);
            end
        end
    endtask

    initial begin
        clk = 0; rst_n = 0;
        test_pass = 0; test_total = 0;
        start = 0;
        set_c0_jet(0,0,0,0, 0,0,0,0, 0,0,0,0);
        set_c1_jet(0,0,0,0, 0,0,0,0, 0,0,0,0);
        set_c2_jet(0,0,0,0, 0,0,0,0, 0,0,0,0);
        #20 rst_n = 1; #10;

        // ── Vector 1: random perturbed quintic ───────────────────────
        // c0 (O(eps): eps0=0)
        set_c0_jet(
            32'h00000000, 32'h00000000, 32'h00000000, 32'h00000000,
            32'h6f32c1ec, 32'h1f6639a5, 32'h2d28317a, 32'h7b723650,
            32'h08d6fead, 32'h4fa63ab9, 32'h4af77ae4, 32'h73341f4e);
        // c1 (unit)
        set_c1_jet(
            32'h3bf44136, 32'h4388a816, 32'h2773bd9e, 32'h6b56498f,
            32'h24678311, 32'h20d382ea, 32'h0fdee902, 32'h56960e1d,
            32'h3ee12ef0, 32'h3554f1fe, 32'h4bfd30d7, 32'h5890ab02);
        // c2
        set_c2_jet(
            32'h55295e94, 32'h28270840, 32'h401542a7, 32'h0b24cdee,
            32'h140899ef, 32'h1505bb35, 32'h31306bb7, 32'h1edc17ea,
            32'h641ee5b4, 32'h33898c9d, 32'h7d4660cf, 32'h36772c57);
        run_stream();
        check_jet("Vector 1",
            32'h00000000, 32'h00000000, 32'h00000000, 32'h00000000,
            32'h20559f77, 32'h6fbd0431, 32'h1124c960, 32'h3fb71afa,
            32'h712934dc, 32'h38aef7be, 32'h2f2039fe, 32'h251cffc6);
        test_total = test_total + 1;
        if (!err_singular) test_pass = test_pass + 1;
        else $display("FAIL: Vector 1 err_singular asserted");
        check_counts("Vector 1", 27);

        // ── Vector 2: random perturbed quintic ───────────────────────
        set_c0_jet(
            32'h00000000, 32'h00000000, 32'h00000000, 32'h00000000,
            32'h62fdf583, 32'h15506c8f, 32'h20dc2994, 32'h37f6031f,
            32'h4eb79d70, 32'h57e2bf8f, 32'h171b1e2a, 32'h3f5d917a);
        set_c1_jet(
            32'h79e3fa30, 32'h3a152b39, 32'h5df3919a, 32'h20247429,
            32'h3ad81fd7, 32'h433cdeca, 32'h36ee19ee, 32'h2f506145,
            32'h26079295, 32'h63f8baae, 32'h51bde113, 32'h0f6499a4);
        set_c2_jet(
            32'h011a7658, 32'h2887f416, 32'h7c2c85e3, 32'h2df1dc4d,
            32'h68a72abb, 32'h42094481, 32'h37b55902, 32'h47f7ba50,
            32'h1297cf12, 32'h289e4ff2, 32'h6aef8d95, 32'h2cdb72a4);
        run_stream();
        check_jet("Vector 2",
            32'h00000000, 32'h00000000, 32'h00000000, 32'h00000000,
            32'h3ecd8e7a, 32'h7e65574d, 32'h38a4ef29, 32'h5f0d08b1,
            32'h49e14b33, 32'h46cbe052, 32'h71049c04, 32'h3a2dee01);
        test_total = test_total + 1;
        if (!err_singular) test_pass = test_pass + 1;
        else $display("FAIL: Vector 2 err_singular asserted");
        check_counts("Vector 2", 27);

        // ── Vector 3: random perturbed quintic ───────────────────────
        set_c0_jet(
            32'h00000000, 32'h00000000, 32'h00000000, 32'h00000000,
            32'h59796491, 32'h7d53de0e, 32'h09675a64, 32'h6a53879e,
            32'h052ce363, 32'h0394a16c, 32'h072a7560, 32'h373b2a51);
        set_c1_jet(
            32'h3d4a142c, 32'h455cd440, 32'h3efedb6d, 32'h3967d370,
            32'h6d499fb2, 32'h22eab6dd, 32'h6ec30a19, 32'h5d8a2c32,
            32'h23d24873, 32'h24afb747, 32'h52aa45e7, 32'h2ed56d44);
        set_c2_jet(
            32'h1b85e8f2, 32'h6aa1025a, 32'h49d9a96a, 32'h3cf93715,
            32'h4b11aaff, 32'h16fa54ab, 32'h40d15ed1, 32'h5faeb9f7,
            32'h45d51fc5, 32'h01fb5cda, 32'h64ba2a72, 32'h36e70826);
        run_stream();
        check_jet("Vector 3",
            32'h00000000, 32'h00000000, 32'h00000000, 32'h00000000,
            32'h21aa4ac5, 32'h2e54dafd, 32'h1d21759f, 32'h6b8a0098,
            32'h49d09c9c, 32'h33b9c024, 32'h19deeb08, 32'h51cc9507);
        test_total = test_total + 1;
        if (!err_singular) test_pass = test_pass + 1;
        else $display("FAIL: Vector 3 err_singular asserted");
        check_counts("Vector 3", 27);

        // ── Vector 4: singular c1 (zero-norm eps^0) ──────────────────
        // (sqrt15, 0, 0, 1) has zero A31 norm; negation preserves it.
        // Expect: err_singular, done pulse, 1 tower launch, 0 multiplies.
        set_c1_jet(
            32'h5311db4d, 32'h00000000, 32'h00000000, 32'h00000001,
            32'h3ad81fd7, 32'h433cdeca, 32'h36ee19ee, 32'h2f506145,
            32'h26079295, 32'h63f8baae, 32'h51bde113, 32'h0f6499a4);
        run_stream();
        test_total = test_total + 1;
        if (err_singular === 1'b1) test_pass = test_pass + 1;
        else $display("FAIL: Vector 4 err_singular not asserted on zero-norm c1");
        test_total = test_total + 1;
        if ((mult_pulses - mult_mark) === 0 && (inv_pulses - inv_mark) === 1)
            test_pass = test_pass + 1;
        else
            $display("FAIL: Vector 4 counts: %0d mults / %0d towers, expected 0 / 1",
                     mult_pulses - mult_mark, inv_pulses - inv_mark);

        // ── Report ───────────────────────────────────────────────────
        if (test_pass == test_total)
            $display("PASS: spu13_series_stream_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: spu13_series_stream_tb (%0d/%0d)", test_pass, test_total);
        $finish;
    end

endmodule
