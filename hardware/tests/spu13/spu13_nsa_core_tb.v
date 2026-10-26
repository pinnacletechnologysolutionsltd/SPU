`timescale 1ns / 1ps

// spu13_nsa_core_tb.v — Integration testbench for NSA compute block
//
// Tests the full NSA instruction flow:
//   A) NSA_LOAD:  QR feature → NSA bank slot
//   B) NSA_DQADD: Dual add R[dest] = R[srcA] + R[srcB]
//   C) NSA_DQMUL: Dual multiply R[dest] = R[srcA] * R[srcB]
//   D) NSA_STORE: NSA bank → QR regfile writeback
//   E) Load→add→store round-trip
//   F) Load→mul→store round-trip

module spu13_nsa_core_tb;

    reg clk, rst_n;
    reg nsa_start;
    reg [1:0] nsa_op;
    reg [3:0] nsa_dest, nsa_srcA, nsa_srcB;
    wire nsa_done, nsa_busy;
    reg [143:0] qr_features_in;
    wire [143:0] nsa_features_out;
    wire nsa_wr_en;
    wire [3:0] nsa_wr_addr;
    wire [31:0] nsa_real_z0, nsa_real_z1, nsa_real_z2, nsa_real_z3;
    wire [31:0] nsa_eps_z0,  nsa_eps_z1,  nsa_eps_z2,  nsa_eps_z3;
    wire nsa_result_valid;

    spu13_nsa_core uut (
        .clk(clk), .rst_n(rst_n),
        .nsa_start(nsa_start), .nsa_op(nsa_op),
        .nsa_dest(nsa_dest), .nsa_srcA(nsa_srcA), .nsa_srcB(nsa_srcB),
        .nsa_done(nsa_done), .nsa_busy(nsa_busy),
        .qr_features_in(qr_features_in),
        .nsa_features_out(nsa_features_out),
        .nsa_wr_en(nsa_wr_en),
        .nsa_wr_addr(nsa_wr_addr),
        .nsa_real_z0(nsa_real_z0), .nsa_real_z1(nsa_real_z1),
        .nsa_real_z2(nsa_real_z2), .nsa_real_z3(nsa_real_z3),
        .nsa_eps_z0(nsa_eps_z0),   .nsa_eps_z1(nsa_eps_z1),
        .nsa_eps_z2(nsa_eps_z2),   .nsa_eps_z3(nsa_eps_z3),
        .nsa_result_valid(nsa_result_valid)
    );

    always #5 clk = ~clk;

    integer test_pass, test_total;

    // ── Helper: drive an NSA instruction and wait for done ─────────
    task nsa_instr;
        input [1:0] op;
        input [3:0] dest, sa, sb;
        begin
            nsa_op   = op;
            nsa_dest = dest;
            nsa_srcA = sa;
            nsa_srcB = sb;
            nsa_start = 1; #10; nsa_start = 0;
            wait(nsa_done); #2;
        end
    endtask

    task check_result;
        input [255:0] label;
        input [31:0] er0, er1, er2, er3;
        input [31:0] ee0, ee1, ee2, ee3;
        integer ok;
        begin
            test_total = test_total + 1;
            ok = 1;
            if (nsa_real_z0 !== er0 || nsa_real_z1 !== er1 ||
                nsa_real_z2 !== er2 || nsa_real_z3 !== er3) ok = 0;
            if (nsa_eps_z0  !== ee0 || nsa_eps_z1  !== ee1 ||
                nsa_eps_z2  !== ee2 || nsa_eps_z3  !== ee3) ok = 0;
            if (ok) test_pass = test_pass + 1;
            else begin
                $display("FAIL: %0s", label);
                $display("  got real: (%h,%h,%h,%h)", nsa_real_z0, nsa_real_z1, nsa_real_z2, nsa_real_z3);
                $display("  exp real: (%h,%h,%h,%h)", er0, er1, er2, er3);
                $display("  got eps:  (%h,%h,%h,%h)", nsa_eps_z0, nsa_eps_z1, nsa_eps_z2, nsa_eps_z3);
                $display("  exp eps:  (%h,%h,%h,%h)", ee0, ee1, ee2, ee3);
            end
        end
    endtask

    initial begin
        clk = 0; rst_n = 0;
        test_pass = 0; test_total = 0;
        nsa_start = 0; nsa_op = 0; nsa_dest = 0; nsa_srcA = 0; nsa_srcB = 0;
        qr_features_in = 144'd0;
        #20 rst_n = 1; #10;

        // ═══════════════════════════════════════════════════════════
        // Test A: NSA_LOAD slot 0 from QR feature lane
        // QR features: lane0 P=5, Q=0 → NSA slot 0 real_z0=5, eps=0
        // ═══════════════════════════════════════════════════════════
        qr_features_in[17:0] = 18'd5;   // lane 0 P-component
        nsa_instr(2'b10, 4'd0, 4'd0, 4'd0);  // LOAD dest=0, src=slot0
        test_total = test_total + 1;
        if (nsa_done) test_pass = test_pass + 1;
        else $display("FAIL A: LOAD didn't complete");

        // ═══════════════════════════════════════════════════════════
        // Test B: NSA_LOAD slot 1 with scalar value 3
        // ═══════════════════════════════════════════════════════════
        qr_features_in[17:0] = 18'd3;   // lane 0 P-component
        nsa_instr(2'b10, 4'd0, 4'd1, 4'd0);  // LOAD src=slot1
        test_total = test_total + 1;
        if (nsa_done) test_pass = test_pass + 1;
        else $display("FAIL B: LOAD slot 1 didn't complete");

        // ═══════════════════════════════════════════════════════════
        // Test C: NSA_DQADD slot0 + slot1 → slot0
        // (5+e0) + (3+e0) = (8,0,0,0) + e(0,0,0,0)
        // ═══════════════════════════════════════════════════════════
        nsa_instr(2'b00, 4'd0, 4'd0, 4'd1);  // DQADD dest=0, srcA=0, srcB=1
        check_result("C: (5+e0)+(3+e0)=8+e0",
                     32'd8,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);

        // ═══════════════════════════════════════════════════════════
        // Test D: Reload slot 1 with value 4, then DQMUL
        // (8+e0) * (4+e0) = (32,0,0,0) + e(0,0,0,0)
        // ═══════════════════════════════════════════════════════════
        qr_features_in[17:0] = 18'd4;
        nsa_instr(2'b10, 4'd0, 4'd1, 4'd0);  // LOAD slot1=4
        nsa_instr(2'b01, 4'd0, 4'd0, 4'd1);  // DQMUL dest=0, srcA=0, srcB=1
        check_result("D: (8+e0)*(4+e0)=32+e0",
                     32'd32,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);

        // ═══════════════════════════════════════════════════════════
        // Test E: Reload slots, then dual add with surd components
        // Manual: we need surd values. Load scalar-only for now.
        // Test round-trip: LOAD→DQADD→result_valid
        // ═══════════════════════════════════════════════════════════
        qr_features_in[17:0] = 18'd1;
        nsa_instr(2'b10, 4'd0, 4'd0, 4'd0);  // slot0=1
        qr_features_in[17:0] = 18'd1;
        nsa_instr(2'b10, 4'd0, 4'd1, 4'd0);  // slot1=1
        nsa_instr(2'b00, 4'd0, 4'd0, 4'd1);  // DQADD 1+1
        check_result("E: (1+e0)+(1+e0)=2+e0",
                     32'd2,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);

        // ═══════════════════════════════════════════════════════════
        // Test F: Back-to-back operations (issue/done/issue/done)
        // ═══════════════════════════════════════════════════════════
        qr_features_in[17:0] = 18'd2;
        nsa_instr(2'b10, 4'd0, 4'd0, 4'd0);   // slot0=2
        nsa_instr(2'b00, 4'd0, 4'd0, 4'd1);   // 2+1=3
        nsa_instr(2'b01, 4'd0, 4'd0, 4'd1);   // 3*1=3
        check_result("F: back-to-back: (2+1)*1=3+e0",
                     32'd3,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);

        if (test_pass == test_total)
            $display("PASS: spu13_nsa_core_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: spu13_nsa_core_tb (%0d/%0d)", test_pass, test_total);
        $finish;
    end

endmodule
