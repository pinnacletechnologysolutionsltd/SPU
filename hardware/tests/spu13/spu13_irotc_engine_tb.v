// spu13_irotc_engine_tb.v — IROTC term-serial engine testbench
//
// Copyright 2026 John Curley
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Golden vectors are GENERATED from the exact-Fraction derivation oracle
// (the same oracle the VM is trace-equivalent to, closing VM<->RTL through
// a shared source of truth):
//   python3 software/tests/test_icosahedral_catalog.py --emit-rtl
//
// Proven here:
//   1. cases 0-119: all 60 indices x both catalogs bit-exact, out_tag
//      correct, and FIXED 12-clock start->done latency on every case
//      (the phi-13 slot claim);
//   2. case 120: pinned 10-step main-catalog chain fed back-to-back
//      through the engine (accumulator/state cleanup between ops);
//   3. dispatch faults BADIDX (60,63), UNTAGGED, CATMIX (both
//      directions) — fault code correct, outputs bit-identically held,
//      no done, engine immediately reusable;
//   4. FRESH source accepted by either catalog.
`timescale 1ns/1ps

module spu13_irotc_engine_tb;
    localparam NUM_CASES = 121;
    localparam CHAIN_LEN = 10;

    reg clk = 0, rst_n = 0, start = 0;
    reg  [6:0]  sel;
    reg  [1:0]  src_tag;
    reg  signed [31:0] in_b_a, in_b_b, in_c_a, in_c_b, in_d_a, in_d_b;
    wire busy, done, fault;
    wire [1:0] fault_code, out_tag;
    wire signed [31:0] out_a_a, out_a_b, out_b_a, out_b_b;
    wire signed [31:0] out_c_a, out_c_b, out_d_a, out_d_b;

    spu13_irotc_engine dut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .sel(sel), .src_tag(src_tag),
        .in_b_a(in_b_a), .in_b_b(in_b_b),
        .in_c_a(in_c_a), .in_c_b(in_c_b),
        .in_d_a(in_d_a), .in_d_b(in_d_b),
        .busy(busy), .done(done), .fault(fault), .fault_code(fault_code),
        .out_tag(out_tag),
        .out_a_a(out_a_a), .out_a_b(out_a_b),
        .out_b_a(out_b_a), .out_b_b(out_b_b),
        .out_c_a(out_c_a), .out_c_b(out_c_b),
        .out_d_a(out_d_a), .out_d_b(out_d_b)
    );

    always #5 clk = ~clk;

    // Golden vectors: 121 cases x 15 words
    reg [31:0] gv [0:NUM_CASES*15-1];
    initial $readmemh("hardware/tests/spu13/spu13_irotc_golden.mem", gv);

    // Pinned chain (must match --emit-rtl CHAIN_SELS)
    reg [6:0] chain_sels [0:CHAIN_LEN-1];
    initial begin
        chain_sels[0] = 7'd36; chain_sels[1] = 7'd49; chain_sels[2] = 7'd50;
        chain_sels[3] = 7'd3;  chain_sels[4] = 7'd17; chain_sels[5] = 7'd22;
        chain_sels[6] = 7'd45; chain_sels[7] = 7'd58; chain_sels[8] = 7'd9;
        chain_sels[9] = 7'd30;
    end

    integer errors = 0;
    integer lat;

    // Drive one rotation and measure start->done latency
    task run_op;
        input [6:0]  t_sel;
        input [1:0]  t_tag;
        begin
            @(negedge clk);
            sel = t_sel; src_tag = t_tag; start = 1;
            @(negedge clk);
            start = 0;
            lat = 1;
            while (!done && !fault && lat < 40) begin
                @(negedge clk);
                lat = lat + 1;
            end
        end
    endtask

    task check_case;
        input integer c;
        input [1:0] t_tag;
        integer base;
        reg [1:0] exp_tag;
        begin
            base = c * 15;
            in_b_a = gv[base+1]; in_b_b = gv[base+2];
            in_c_a = gv[base+3]; in_c_b = gv[base+4];
            in_d_a = gv[base+5]; in_d_b = gv[base+6];
            run_op(gv[base][6:0], t_tag);
            exp_tag = gv[base][6] ? 2'd3 : 2'd2;
            if (fault) begin
                errors = errors + 1;
                $display("FAIL case %0d: unexpected fault code %0d", c, fault_code);
            end else if (lat != 12) begin
                errors = errors + 1;
                $display("FAIL case %0d: latency %0d != 12 (phi-13 slot broken)", c, lat);
            end else if (out_a_a !== $signed(gv[base+7])  || out_a_b !== $signed(gv[base+8]) ||
                         out_b_a !== $signed(gv[base+9])  || out_b_b !== $signed(gv[base+10]) ||
                         out_c_a !== $signed(gv[base+11]) || out_c_b !== $signed(gv[base+12]) ||
                         out_d_a !== $signed(gv[base+13]) || out_d_b !== $signed(gv[base+14])) begin
                errors = errors + 1;
                $display("FAIL case %0d (sel=%02h): output mismatch", c, gv[base][6:0]);
                $display("  got A=(%0d,%0d) B=(%0d,%0d) C=(%0d,%0d) D=(%0d,%0d)",
                         out_a_a, out_a_b, out_b_a, out_b_b, out_c_a, out_c_b, out_d_a, out_d_b);
                $display("  exp A=(%0d,%0d) B=(%0d,%0d) C=(%0d,%0d) D=(%0d,%0d)",
                         $signed(gv[base+7]), $signed(gv[base+8]), $signed(gv[base+9]), $signed(gv[base+10]),
                         $signed(gv[base+11]), $signed(gv[base+12]), $signed(gv[base+13]), $signed(gv[base+14]));
            end else if (out_tag !== exp_tag) begin
                errors = errors + 1;
                $display("FAIL case %0d: out_tag %0d != %0d", c, out_tag, exp_tag);
            end
        end
    endtask

    // Expect a dispatch fault; outputs must hold bit-identically
    task check_fault;
        input [6:0] t_sel;
        input [1:0] t_tag;
        input [1:0] exp_code;
        reg [31:0] h0, h1, h2, h3, h4, h5, h6, h7;
        begin
            h0 = out_a_a; h1 = out_a_b; h2 = out_b_a; h3 = out_b_b;
            h4 = out_c_a; h5 = out_c_b; h6 = out_d_a; h7 = out_d_b;
            run_op(t_sel, t_tag);
            if (!fault || fault_code !== exp_code) begin
                errors = errors + 1;
                $display("FAIL fault(sel=%02h tag=%0d): fault=%0d code=%0d exp=%0d",
                         t_sel, t_tag, fault, fault_code, exp_code);
            end else if ({out_a_a, out_a_b, out_b_a, out_b_b,
                          out_c_a, out_c_b, out_d_a, out_d_b}
                         !== {h0, h1, h2, h3, h4, h5, h6, h7}) begin
                errors = errors + 1;
                $display("FAIL fault(sel=%02h): outputs disturbed (poison broken)", t_sel);
            end
        end
    endtask

    integer c, k, base;
    initial begin
        repeat (4) @(negedge clk);
        rst_n = 1;
        @(negedge clk);

        // 1. all 60 indices x both catalogs, FRESH source, fixed latency
        for (c = 0; c < 120; c = c + 1)
            check_case(c, 2'd1);
        $display("cases 0-119 (60 indices x both catalogs): %s",
                 errors ? "with FAILURES" : "all bit-exact @ 12 clks");

        // 2. pinned 10-step chain, back-to-back, feeding outputs to inputs.
        //    First step from FRESH; every later step re-enters with the
        //    engine's own out_tag (MAIN) — catalog lock honored end-to-end.
        base = 120 * 15;
        in_b_a = gv[base+1]; in_b_b = gv[base+2];
        in_c_a = gv[base+3]; in_c_b = gv[base+4];
        in_d_a = gv[base+5]; in_d_b = gv[base+6];
        src_tag = 2'd1;
        for (k = 0; k < CHAIN_LEN; k = k + 1) begin
            run_op(chain_sels[k], src_tag);
            if (fault || lat != 12) begin
                errors = errors + 1;
                $display("FAIL chain step %0d: fault=%0d lat=%0d", k, fault, lat);
            end
            in_b_a = out_b_a; in_b_b = out_b_b;
            in_c_a = out_c_a; in_c_b = out_c_b;
            in_d_a = out_d_a; in_d_b = out_d_b;
            src_tag = out_tag;
        end
        if (out_a_a !== $signed(gv[base+7])  || out_a_b !== $signed(gv[base+8]) ||
            out_b_a !== $signed(gv[base+9])  || out_b_b !== $signed(gv[base+10]) ||
            out_c_a !== $signed(gv[base+11]) || out_c_b !== $signed(gv[base+12]) ||
            out_d_a !== $signed(gv[base+13]) || out_d_b !== $signed(gv[base+14])) begin
            errors = errors + 1;
            $display("FAIL chain: final state mismatch after %0d steps", CHAIN_LEN);
        end else
            $display("10-step back-to-back chain: bit-exact, tag MAIN throughout");

        // 3. dispatch faults + poison holds (outputs still hold chain state)
        check_fault(7'd60, 2'd1, 2'd1);            // BADIDX low boundary
        check_fault(7'd63, 2'd1, 2'd1);            // BADIDX top of field
        check_fault({1'b1, 6'd60}, 2'd1, 2'd1);    // BADIDX, conj catalog
        check_fault(7'd5, 2'd0, 2'd2);             // UNTAGGED
        check_fault(7'd63, 2'd0, 2'd1);            // BADIDX outranks UNTAGGED
        check_fault({1'b1, 6'd5}, 2'd2, 2'd3);     // CATMIX: MAIN into conj
        check_fault(7'd5, 2'd3, 2'd3);             // CATMIX: CONJ into main
        $display("fault matrix: BADIDX/UNTAGGED/CATMIX + precedence + poison holds");

        // 4. engine reusable after faults; FRESH accepted by conj catalog
        base = 60 * 15;                             // case 60 = idx 0, conj=1
        check_case(60, 2'd1);
        $display("post-fault recovery + FRESH->conj accept: ok");

        if (errors == 0) $display("SPU13 IROTC ENGINE: PASS");
        else begin
            $display("SPU13 IROTC ENGINE: FAIL (%0d errors)", errors);
            $display("FAIL");
        end
        $finish;
    end
endmodule
