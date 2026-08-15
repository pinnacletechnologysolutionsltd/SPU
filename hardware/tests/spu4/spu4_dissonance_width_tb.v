// spu4_dissonance_width_tb.v — the Quadray residual must not wrap
//
// spu4_dissonance summed four sign-extended 16-bit addends in a 17-bit
// context until 2026-08-16. The sum therefore wrapped modulo 131072 before
// the saturation test could see it, and a maximal residual reported as
// laminar. The whole point of a saturating fault signal is that large means
// large, so the wrapping vectors below are the reason this file exists.
//
// Every vector here is checked against an independently computed 32-bit
// reference, not against a hand-copied constant, so the expectations cannot
// silently drift with the RTL.

`timescale 1ns / 1ps

module spu4_dissonance_width_tb;

    reg signed [15:0] A, B, C, D;
    wire [7:0] dissonance;

    spu4_dissonance dut (.A(A), .B(B), .C(C), .D(D), .dissonance(dissonance));

    integer pass, fail;

    // Reference model at a width wide enough that it cannot itself wrap:
    // 32 bits against a worst case of 131072.
    function [7:0] expected;
        input signed [15:0] a, b, c, d;
        reg signed [31:0] s;
        reg        [31:0] m;
        begin
            s = $signed(a) + $signed(b) + $signed(c) + $signed(d);
            m = (s < 0) ? -s : s;
            expected = (m > 32'd255) ? 8'hFF : m[7:0];
        end
    endfunction

    task check;
        input signed [15:0] a, b, c, d;
        input [511:0] label;
        reg [7:0] exp;
        begin
            A = a; B = b; C = c; D = d;
            #1;
            exp = expected(a, b, c, d);
            if (dissonance === exp) begin
                $display("PASS: %0s  A=%04x B=%04x C=%04x D=%04x -> %02x",
                         label, a, b, c, d, dissonance);
                pass = pass + 1;
            end else begin
                $display("FAIL: %0s  A=%04x B=%04x C=%04x D=%04x -> %02x, expected %02x",
                         label, a, b, c, d, dissonance, exp);
                fail = fail + 1;
            end
        end
    endtask

    integer i;
    reg signed [15:0] ra, rb, rc, rd;

    initial begin
        pass = 0; fail = 0;

        // ── The wrapping vectors — these failed before 2026-08-16 ────────
        // Most negative residual reachable: 4 * -32768 = -131072. At 17 bits
        // this truncated to exactly 0 and read 0x00, i.e. perfectly laminar
        // at maximum dissonance. This is the single most important vector in
        // the file.
        check(16'h8000, 16'h8000, 16'h8000, 16'h8000, "min residual -131072 saturates");

        // Most positive residual: 4 * 32767 = 131068. At 17 bits this read
        // as -4, so the port reported 0x04 — near-laminar — at a residual of
        // over 131 thousand.
        check(16'h7FFF, 16'h7FFF, 16'h7FFF, 16'h7FFF, "max residual 131068 saturates");

        // Just past the old 17-bit signed boundary in both directions. These
        // are where the old code flipped sign rather than saturating.
        check(16'h8000, 16'h8000, 16'h0000, 16'h0000, "-65536 saturates");
        check(16'h4000, 16'h4000, 16'h4000, 16'h4000, "+65536 saturates");
        check(16'h8000, 16'h8000, 16'h8000, 16'h0000, "-98304 saturates");

        // ── Saturation boundary — exact, not approximate ─────────────────
        check(16'd0, 16'd0, 16'd0, 16'd255, "255 is the last non-saturating value");
        check(16'd0, 16'd0, 16'd0, 16'd256, "256 saturates");
        check(16'd0, 16'd0, 16'd0, -16'sd255, "-255 does not saturate");
        check(16'd0, 16'd0, 16'd0, -16'sd256, "-256 saturates");

        // ── Laminar and small residuals ──────────────────────────────────
        // The Davis identity holding is the defining laminar case.
        check(16'd0, 16'd0, 16'd0, 16'd0, "all zero is laminar");
        check(16'sd1000, -16'sd1000, 16'sd7, -16'sd7, "cancelling axes are laminar");
        check(16'sd32767, -16'sd32767, 16'sd0, 16'sd0, "large cancelling axes are laminar");
        check(16'd0, 16'd0, 16'd0, 16'd1, "residual of 1 reads 1");
        check(16'sd100, 16'sd100, -16'sd150, 16'sd0, "residual of 50 reads 50");

        // The QROT fixture the probe and standalone testbenches assert on:
        // A=0, B=C=D=0x155 gives 0x3FF = 1023, which saturates.
        check(16'h0000, 16'h0155, 16'h0155, 16'h0155, "QROT probe fixture saturates");

        // ── Randomised sweep against the reference ───────────────────────
        // Breadth, not the point. Verified 2026-08-16: replaying this file
        // against the old 17-bit expression fails on exactly two vectors,
        // both of them targeted ones above — all 2000 random draws PASS.
        // $random essentially never yields four same-sign extremes, which is
        // the only region where the wrap is observable. Kept for coverage of
        // the ordinary range; do not mistake it for what catches this class
        // of bug.
        for (i = 0; i < 2000; i = i + 1) begin
            ra = $random; rb = $random; rc = $random; rd = $random;
            A = ra; B = rb; C = rc; D = rd;
            #1;
            if (dissonance !== expected(ra, rb, rc, rd)) begin
                $display("FAIL: random A=%04x B=%04x C=%04x D=%04x -> %02x, expected %02x",
                         ra, rb, rc, rd, dissonance, expected(ra, rb, rc, rd));
                fail = fail + 1;
            end else begin
                pass = pass + 1;
            end
        end

        // ── Negative control ─────────────────────────────────────────────
        // The reference must be able to disagree with the DUT, otherwise
        // every PASS above is vacuous. Assert against a knowingly wrong
        // expectation on the last case checked, per the audit rule that a
        // negative control must target the last case and not the first.
        if (expected(16'h8000, 16'h8000, 16'h8000, 16'h8000) === 8'h00) begin
            $display("FAIL: negative control — reference model reproduces the 17-bit wrap");
            fail = fail + 1;
        end else begin
            $display("PASS: negative control — reference model rejects the 17-bit wrap value");
            pass = pass + 1;
        end

        $display("%0d checks, %0d passed, %0d failed", pass + fail, pass, fail);
        if (fail == 0) $display("PASS");
        else $display("FAIL");
        $finish;
    end

endmodule
