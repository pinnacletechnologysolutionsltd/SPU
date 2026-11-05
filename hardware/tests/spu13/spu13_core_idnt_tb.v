// spu13_core_idnt_tb.v — IDNT (0x18) canonical execution: QRd <- (1,0,0,0).
// Math core (QR file, REGEN on) vs a no-QR-file build (Gen-1 surd-CPU settings).
// Canonical semantics: spu_vm.py / spu_vm.cpp IDNT, lane = index mod 13.
`timescale 1ns/1ps
module spu13_core_idnt_tb;
    reg clk = 0, rst_n = 0;
    always #5 clk = ~clk;
    reg iv = 0, nv = 0;
    reg [63:0] iw = 0, nw = 0;
    wire idone, ndone, cv, ncv, hexv;
    wire [3:0] cl, ncl;
    wire [63:0] cA, cB, cC, cD;
    wire [15:0] hq, hr, regen_st;
    integer errors = 0, commits, ncommits, dones;
    reg [3:0] last_lane;
    reg [63:0] lA, lB, lC, lD;
    reg [3:0] l0, l1;
    reg [63:0] r0A, r0B, r0C, r0D, r1A;

    spu13_core #(.DEVICE("SIM"), .ENABLE_RPLU(0), .ENABLE_LATTICE(0), .ENABLE_MATH(1),
        .ENABLE_SEQUENCER(0), .ENABLE_CORE_SOM(0), .ENABLE_CORE_RPLU_V2(0),
        .ENABLE_CORE_RPLU_V2_PIPELINE(0), .ENABLE_CORE_RPLU_V2_EXTENSIONS(0),
        .ENABLE_IROTC(0)) uut (
        .clk(clk), .rst_n(rst_n), .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .regen_dphi_cfg(8'd0),
        .qr_commit_valid(cv), .qr_commit_lane(cl),
        .qr_commit_A(cA), .qr_commit_B(cB), .qr_commit_C(cC), .qr_commit_D(cD),
        .dec_fast_cfg_wr_en(1'b0), .dec_fast_cfg_sel(3'd0), .dec_fast_cfg_material(8'd0),
        .dec_fast_cfg_addr(10'd0), .dec_fast_cfg_data(64'd0), .phinary_cfg(16'd0),
        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),
        .boot_done(1'b1), .pell_data(32'd0), .pell_addr(3'd0), .pell_we(1'b0),
        .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
        .mem_ready(1'b1), .mem_rd_manifold(832'd0), .mem_burst_done(1'b0),
        .inst_valid(iv), .inst_word(iw), .inst_done(idone),
        .hex_valid(hexv), .hex_q(hq), .hex_r(hr), .regen_debug_status(regen_st));

    // No QR file: MATH/IROTC/SOM/RPLU2 off, surd CPU on, REGEN off (Gen-1 settings).
    spu13_core #(.DEVICE("SIM"), .ENABLE_SURD_CPU(1), .ENABLE_SEQUENCER(0), .ENABLE_RPLU(0),
        .ENABLE_LATTICE(0), .ENABLE_MATH(0), .ENABLE_CORE_SOM(0), .ENABLE_CORE_RPLU_V2(0),
        .ENABLE_CORE_RPLU_V2_PIPELINE(0), .ENABLE_CORE_RPLU_V2_EXTENSIONS(0),
        .ENABLE_REGEN(0), .ENABLE_IROTC(0), .ENABLE_TORUS(0)) nqr (
        .clk(clk), .rst_n(rst_n), .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .qr_commit_valid(ncv), .qr_commit_lane(ncl),
        .dec_fast_cfg_wr_en(1'b0), .dec_fast_cfg_sel(3'd0), .dec_fast_cfg_material(8'd0),
        .dec_fast_cfg_addr(10'd0), .dec_fast_cfg_data(64'd0), .phinary_cfg(16'd0),
        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),
        .boot_done(1'b1), .pell_data(32'd0), .pell_addr(3'd0), .pell_we(1'b0),
        .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
        .mem_ready(1'b1), .mem_rd_manifold(832'd0), .mem_burst_done(1'b0),
        .inst_valid(nv), .inst_word(nw), .inst_done(ndone));

    function [63:0] idnt(input [7:0] q); idnt = {8'h18, q, 48'd0}; endfunction
    function [63:0] qldi(input [7:0] q, input [7:0] a, b, c, d);
        qldi = {8'h1D, q, 8'd0, a, b, c, d, 8'd0}; endfunction
    function [63:0] qsub(input [7:0] d, a, input [3:0] b);
        qsub = {8'h1B, d, a, 16'd0, 12'd0, b, 8'd0}; endfunction
    function [63:0] hexw(input [7:0] q); hexw = {8'h16, 8'd0, q, 40'd0}; endfunction
    function [63:0] regen(input [15:0] k); regen = {8'h09, 16'd0, k, 24'd0}; endfunction

    // Issue one word to the math core; count commits/done pulses; keep the last commit.
    task issue(input [63:0] w);
        integer g;
        begin
            commits = 0; dones = 0;
            @(posedge clk); iw <= w; iv <= 1;
            @(posedge clk); iv <= 0; iw <= 0;
            for (g = 0; g < 200 && dones == 0; g = g + 1) begin
                @(posedge clk);
                if (cv) begin commits = commits + 1; last_lane = cl;
                    lA = cA; lB = cB; lC = cC; lD = cD;
                    if (cl == 0) begin r0A = cA; r0B = cB; r0C = cC; r0D = cD; end
                    if (cl == 1) r1A = cA; end
                if (idone) dones = dones + 1;
            end
            repeat (4) @(posedge clk) if (cv) commits = commits + 1;
            if (dones == 0) begin $display("FAIL: timeout %h", w); errors = errors + 1; end
        end
    endtask
    task check(input [511:0] label, input cond);
        begin
            if (cond) $display("PASS: %0s", label);
            else begin $display("FAIL: %0s", label); errors = errors + 1; end
        end
    endtask
    // Read lane q through QSUB QR10 = QRq - QR9, with QR9 = 0 (full 64-bit components).
    task readback(input [7:0] q);
        begin issue(qldi(8'd9, 0, 0, 0, 0)); issue(qsub(8'd10, q, 4'd9)); end
    endtask
    function is_unity(input [63:0] a, b, c, d);
        is_unity = (a == {32'd0, 32'd1}) && b == 0 && c == 0 && d == 0; endfunction

    integer g;
    initial begin
        repeat (4) @(posedge clk); rst_n = 1; repeat (40) @(posedge clk);

        // T4 (first, REGEN counter at 0): IDNT counts as eligible and survives K>0 recovery.
        issue(qldi(8'd0, 8'd1, 8'd2, 8'd3, 8'd4));
        issue(qldi(8'd1, 8'd5, 8'd0, 8'd0, 8'd0));
        issue(idnt(8'd0));
        check("T4 REGEN counter = 3 after QLDI, QLDI, IDNT", regen_st[7:2] == 6'd3);
        r0A = 64'hDEAD; r1A = 64'hDEAD;
        issue(regen(16'd3));
        check("T4 REGEN K=3 no fault", regen_st[9] == 1'b0);
        check("T4 recovered QR0 = (1,0,0,0)",
              r0A[31:0] == 1 && r0B[31:0] == 0 && r0C[31:0] == 0 && r0D[31:0] == 0);
        check("T4 recovered QR1.A = 5", r1A[31:0] == 5);
        readback(8'd0); check("T4 QR0 after REGEN = (1,0,0,0)", is_unity(lA, lB, lC, lD));

        // T1 destination write: QR3=(3,5,0,1) then IDNT QR3.
        issue(qldi(8'd3, 8'd3, 8'd5, 8'd0, 8'd1));
        issue(qldi(8'd4, 8'd1, 8'd2, 8'd3, 8'd4));
        readback(8'd3);
        check("T1 precondition QR3 = (3,5,0,1)", lA == 3 && lB == 5 && lC == 0 && lD == 1);
        issue(idnt(8'd3));
        check("T1 IDNT QR3: one commit, lane 3, (1,0,0,0) full width",
              commits == 1 && last_lane == 3 && is_unity(lA, lB, lC, lD));
        readback(8'd3);
        check("T1 QR3 stored value is (1,0,0,0), surd parts 0", is_unity(lA, lB, lC, lD));
        readback(8'd4);
        check("T1 neighbour QR4 unchanged (1,2,3,4)", lA == 1 && lB == 2 && lC == 3 && lD == 4);
        issue(hexw(8'd3));
        check("T1 HEX telemetry order unchanged: (B-D,A-D) = (0,1)", hq == 16'd0 && hr == 16'd1);

        // T2 overwrite and idempotence.
        issue(qldi(8'd3, 8'hFE, 8'd7, 8'd0, 8'd4));
        issue(idnt(8'd3)); issue(idnt(8'd3));
        readback(8'd3);
        check("T2 overwrite (-2,7,0,4) then IDNT twice -> (1,0,0,0)", is_unity(lA, lB, lC, lD));

        // T3 index boundaries: QR0, QR12, QR13 -> lane 0, QR255 -> lane 8 (index mod 13).
        issue(qldi(8'd0, 8'd9, 8'd9, 8'd9, 8'd9)); issue(qldi(8'd11, 8'd6, 8'd6, 8'd6, 8'd6));
        issue(qldi(8'd12, 8'd9, 8'd9, 8'd9, 8'd9)); issue(qldi(8'd8, 8'd9, 8'd9, 8'd9, 8'd9));
        issue(idnt(8'd12));
        check("T3 IDNT QR12 commits lane 12", commits == 1 && last_lane == 12);
        readback(8'd12); check("T3 QR12 = (1,0,0,0)", is_unity(lA, lB, lC, lD));
        readback(8'd11); check("T3 QR11 unchanged (6,6,6,6)", lA == 6 && lB == 6 && lC == 6 && lD == 6);
        issue(idnt(8'd13));
        check("T3 IDNT QR13 wraps to lane 0", commits == 1 && last_lane == 0);
        readback(8'd0); check("T3 QR0 = (1,0,0,0) after QR13", is_unity(lA, lB, lC, lD));
        issue(idnt(8'd255));
        check("T3 IDNT QR255 wraps to lane 8", commits == 1 && last_lane == 8);
        readback(8'd8); check("T3 QR8 = (1,0,0,0)", is_unity(lA, lB, lC, lD));

        // T5 no-QR-file build: IDNT completes once with no commit (unchanged behaviour).
        ncommits = 0; dones = 0;
        @(posedge clk); nw <= idnt(8'd3); nv <= 1;
        @(posedge clk); nv <= 0; nw <= 0;
        for (g = 0; g < 40; g = g + 1) begin
            @(posedge clk); if (ncv) ncommits = ncommits + 1; if (ndone) dones = dones + 1;
        end
        check("T5 no-QR build: IDNT done exactly once, no QR commit", dones == 1 && ncommits == 0);

        if (errors == 0) $display("PASS: spu13_core_idnt_tb all checks");
        else $display("FAIL: spu13_core_idnt_tb %0d error(s)", errors);
        $finish;
    end
endmodule
