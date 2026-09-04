// hal_hdmi_tmds_tb.v — first testbench for the DVI 1.0 TMDS encoder.
//
// hal_hdmi_tmds.v shipped untested from its creation until 2026-09-04.
// This checks it against an INDEPENDENT reference model of the DVI 1.0
// encoding algorithm written from the specification, not copied from the
// DUT, plus the algorithm's own structural invariants.
`timescale 1ns/1ps
module hal_hdmi_tmds_tb;

    reg         clk = 0, rst_n = 0;
    reg  [7:0]  data = 8'd0;
    reg  [1:0]  ctrl = 2'b00;
    reg         active = 1'b0;
    wire [9:0]  tmds_out;

    hal_hdmi_tmds dut (.clk(clk), .rst_n(rst_n), .data(data),
                       .ctrl(ctrl), .active(active), .tmds_out(tmds_out));

    always #5 clk = ~clk;

    integer pass = 1;
    integer checks = 0;

    task fail;
        begin
            pass = 0;
        end
    endtask

    // ── Independent reference model, written from the DVI 1.0 spec ───────
    reg signed [4:0] ref_cnt;
    reg  [8:0]       ref_qm;
    reg  [9:0]       ref_out;
    integer          n1d, n1q, n0q, i;

    task ref_encode(input [7:0] d);
        reg xnor_mode;
        begin
            n1d = 0;
            for (i = 0; i < 8; i = i + 1) n1d = n1d + d[i];
            xnor_mode = (n1d > 4) || (n1d == 4 && d[0] == 1'b0);
            ref_qm[0] = d[0];
            for (i = 1; i < 8; i = i + 1)
                ref_qm[i] = xnor_mode ? ~(ref_qm[i-1] ^ d[i])
                                      :  (ref_qm[i-1] ^ d[i]);
            ref_qm[8] = ~xnor_mode;

            n1q = 0;
            for (i = 0; i < 8; i = i + 1) n1q = n1q + ref_qm[i];
            n0q = 8 - n1q;

            if (ref_cnt == 0 || n1q == n0q) begin
                ref_out = {~ref_qm[8], ref_qm[8],
                           ref_qm[8] ? ref_qm[7:0] : ~ref_qm[7:0]};
                ref_cnt = ref_cnt + (ref_qm[8] ? (n1q - n0q) : (n0q - n1q));
            end else if ((ref_cnt > 0 && n1q > n0q) ||
                         (ref_cnt < 0 && n0q > n1q)) begin
                ref_out = {1'b1, ref_qm[8], ~ref_qm[7:0]};
                ref_cnt = ref_cnt + (ref_qm[8] ? 2 : 0) + (n0q - n1q);
            end else begin
                ref_out = {1'b0, ref_qm[8], ref_qm[7:0]};
                ref_cnt = ref_cnt - (ref_qm[8] ? 0 : 2) + (n1q - n0q);
            end
        end
    endtask

    function integer transitions(input [9:0] s);
        integer k, t;
        begin
            t = 0;
            for (k = 0; k < 9; k = k + 1) if (s[k] != s[k+1]) t = t + 1;
            transitions = t;
        end
    endfunction

    integer d_i, seq;
    reg [9:0] expect_q;
    reg signed [8:0] disparity;

    initial begin
        #12 rst_n = 1;

        // ── 1. Control period: all four DVI control words ────────────────
        active = 1'b0;
        begin : ctrl_check
            reg [9:0] expect_ctrl [0:3];
            expect_ctrl[0] = 10'b1101010100;
            expect_ctrl[1] = 10'b0010101011;
            expect_ctrl[2] = 10'b0101010100;
            expect_ctrl[3] = 10'b1010101011;
            for (d_i = 0; d_i < 4; d_i = d_i + 1) begin
                ctrl = d_i[1:0];
                @(posedge clk); #1;
                checks = checks + 1;
                if (tmds_out !== expect_ctrl[d_i]) begin
                    $display("FAIL: ctrl %0d -> %b, expected %b",
                             d_i, tmds_out, expect_ctrl[d_i]);
                    fail;
                end
            end
        end

        // ── 2. All 256 data values vs the independent reference ──────────
        // Reset both DUT and reference disparity to a known common state.
        active = 1'b0; ctrl = 2'b00;
        @(posedge clk); #1;          // DUT clears cnt during control period
        ref_cnt = 0;

        active = 1'b1;
        for (d_i = 0; d_i < 256; d_i = d_i + 1) begin
            data = d_i[7:0];
            ref_encode(d_i[7:0]);
            expect_q = ref_out;
            @(posedge clk); #1;
            checks = checks + 1;
            if (tmds_out !== expect_q) begin
                $display("FAIL: data %0d -> %b, reference says %b",
                         d_i, tmds_out, expect_q);
                fail;
            end
            checks = checks + 1;
            if (transitions(tmds_out) > 5) begin
                $display("FAIL: data %0d symbol %b has %0d transitions (>5)",
                         d_i, tmds_out, transitions(tmds_out));
                fail;
            end
        end

        // ── 3. DC balance over a long pseudorandom stream ────────────────
        disparity = 0;
        for (seq = 0; seq < 4000; seq = seq + 1) begin
            data = $random;
            @(posedge clk); #1;
            for (i = 0; i < 10; i = i + 1)
                disparity = disparity + (tmds_out[i] ? 1 : -1);
            checks = checks + 1;
            if (disparity > 40 || disparity < -40) begin
                $display("FAIL: running disparity %0d exceeded +/-40 at step %0d",
                         disparity, seq);
                fail;
            end
        end

        // ── 4. Negative control: the checks above must be able to fail ───
        checks = checks + 1;
        if (transitions(10'b1010101010) != 9) begin
            $display("FAIL: transition counter is broken (negative control)");
            fail;
        end
        checks = checks + 1;
        if (10'b1101010100 === 10'b0010101011) begin
            $display("FAIL: control-word comparison is vacuous (negative control)");
            fail;
        end

        $display("checks executed: %0d", checks);
        if (pass) $display("PASS: hal_hdmi_tmds_tb");
        else      $display("FAIL: hal_hdmi_tmds_tb");
        $finish;
    end
endmodule
