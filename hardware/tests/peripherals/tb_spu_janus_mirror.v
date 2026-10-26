// tb_spu_janus_mirror.v — Testbench for spu_janus_mirror v2.0
// CC0 1.0 Universal.
//
// Tests the Q(√3) conjugate + Janus snap classification.
// All inputs are Q8.8 fixed-point packed as {P[15:0], Q[15:0]}.
//
// Test matrix:
//   T1  (3 + 0·√3): K = 9,   snap_laminar
//   T2  (0 + 1·√3): K = -3,  snap_shadow
//   T3  (0 + 0·√3): K = 0,   snap_null
//   T4  (2 + 1·√3): K = 4-3=1, snap_laminar  (Pell unit step)
//   T5  conjugate check: shadow_out of (2+1·√3) == (2-1·√3)
//   T6  (1 + 1·√3): K = 1-3=-2, snap_shadow  (inside √3 cone)
//   T7  negative P: (-2 + 1·√3): K = 4-3=1, snap_laminar

`timescale 1ns/1ps

module tb_spu_janus_mirror;

    localparam WIDTH = 16;
    localparam CLK_HALF = 5;  // 100 MHz

    reg                  clk   = 0;
    reg                  rst_n = 0;
    reg  [WIDTH*2-1:0]   surd_in;

    wire [WIDTH*2-1:0]           shadow_out;
    wire signed [WIDTH*2-1:0]    quadrance_out;
    wire                         snap_laminar;
    wire                         snap_null;
    wire                         snap_shadow;

    always #CLK_HALF clk = ~clk;

    spu_janus_mirror #(.WIDTH(WIDTH)) uut (
        .clk         (clk),
        .rst_n       (rst_n),
        .surd_in     (surd_in),
        .shadow_out  (shadow_out),
        .quadrance_out(quadrance_out),
        .snap_laminar(snap_laminar),
        .snap_null   (snap_null),
        .snap_shadow (snap_shadow)
    );

    // pack helper: Q8.8 fixed-point — integer n maps to n<<8
    function [WIDTH-1:0] fp;
        input signed [31:0] n;
        begin fp = n <<< 8; end
    endfunction

    function [WIDTH*2-1:0] pack;
        input signed [31:0] p, q;
        begin pack = {fp(q), fp(p)}; end  // {Q[WIDTH-1:0], P[WIDTH-1:0]}
    endfunction

    // Quadrance in integer units (divide result by 2^16 for Q8.8 squared)
    // Since P=p<<8, Q=q<<8: K_raw = (p<<8)²-(3*(q<<8)²) = (p²-3q²)<<16
    // So quadrance_out>>>16 = p²-3q² in integer.
    function signed [31:0] expected_K;
        input signed [31:0] p, q;
        begin expected_K = (p*p - 3*q*q) <<< 16; end
    endfunction

    integer pass = 0, fail = 0;
    integer t;

    // Drive a test: apply surd_in, wait 2 cycles for pipeline, check outputs.
    task run_test;
        input [127:0]        tname;    // display string (up to 16 chars)
        input signed [31:0]  p_int, q_int;
        input                exp_laminar, exp_null, exp_shadow;
        input signed [31:0]  exp_K_int;   // expected K in integer units
        input signed [31:0]  exp_shadow_p, exp_shadow_q; // expected conjugate

        reg [WIDTH*2-1:0] exp_shadow_packed;
        reg signed [31:0] got_K;
        reg signed [15:0] got_P, got_Q;
        begin
            surd_in = pack(p_int, q_int);
            @(posedge clk); @(posedge clk); // 2 pipeline stages
            #1; // settle combinatorial

            exp_shadow_packed = {fp(exp_shadow_q), fp(exp_shadow_p)};
            got_K  = $signed(quadrance_out) >>> 16;  // strip Q8.8 squared scaling
            got_P  = shadow_out[WIDTH-1:0];
            got_Q  = shadow_out[WIDTH*2-1:WIDTH];

            if (snap_laminar !== exp_laminar ||
                snap_null    !== exp_null    ||
                snap_shadow  !== exp_shadow  ||
                got_K        !== exp_K_int   ||
                shadow_out   !== exp_shadow_packed) begin

                $display("FAIL %0s: P=%0d Q=%0d", tname, p_int, q_int);
                $display("       snap: L=%b N=%b S=%b  (exp L=%b N=%b S=%b)",
                    snap_laminar, snap_null, snap_shadow,
                    exp_laminar, exp_null, exp_shadow);
                $display("       K=%0d (exp %0d)", got_K, exp_K_int);
                $display("       shadow P=%0d Q=%0d (exp P=%0d Q=%0d)",
                    $signed(got_P)>>>8, $signed(got_Q)>>>8,
                    exp_shadow_p, exp_shadow_q);
                fail = fail + 1;
            end else begin
                $display("PASS %0s", tname);
                pass = pass + 1;
            end
        end
    endtask

    initial begin
        // Reset
        rst_n   = 0;
        surd_in = 0;
        repeat(4) @(posedge clk);
        rst_n = 1;
        @(posedge clk);

        // T1: (3 + 0·√3): K = 9, laminar; shadow = (3 - 0·√3) = (3,0)
        run_test("T1 pure_rat ", 3, 0, 1,0,0, 9,  3, 0);

        // T2: (0 + 1·√3): K = -3, shadow; shadow = (0 - 1·√3) = (0,-1)
        run_test("T2 pure_surd", 0, 1, 0,0,1, -3, 0,-1);

        // T3: (0 + 0·√3): K = 0, null
        run_test("T3 zero     ", 0, 0, 0,1,0,  0,  0, 0);

        // T4: (2 + 1·√3): K = 4-3=1, laminar; shadow = (2,-1)  [Pell unit]
        run_test("T4 pell_unit", 2, 1, 1,0,0,  1,  2,-1);

        // T5: (1 + 1·√3): K = 1-3=-2, shadow; shadow = (1,-1)
        run_test("T5 shadow_co", 1, 1, 0,0,1, -2,  1,-1);

        // T6: (-2 + 1·√3): K = 4-3=1, laminar; shadow = (-2,-1)
        run_test("T6 neg_P    ",-2, 1, 1,0,0,  1, -2,-1);

        // T7: (0 + 0·√3) after reset — re-check null after non-zero input
        run_test("T7 null_chk ", 0, 0, 0,1,0,  0,  0, 0);

        $display("");
        $display("Results: %0d/%0d PASS", pass, pass+fail);
        if (fail == 0) $display("ALL PASS — Janus mirror bit-exact");
        else           $display("FAIL — %0d test(s) failed", fail);

        $finish;
    end

endmodule
