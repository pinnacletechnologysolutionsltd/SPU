`timescale 1ns/1ps
module toroidal_regression_tb;
    reg clk = 0; always #5 clk = ~clk;
    reg rst_n = 0;
    initial begin #20 rst_n = 1; end

    // Instance widths: 32, 128, 832
    // --- W=32 instance
    localparam W1 = 32;
    localparam N1 = 4;
    localparam AW1 = 2;

    reg wr_en1 = 0; reg [AW1-1:0] wr_addr1 = 0; reg [W1-1:0] wr_data1 = 0;
    reg rd_en1 = 0; reg [AW1-1:0] rd_addr1 = 0; wire [W1-1:0] rd_data1;
    reg rotate_start1 = 0; reg [31:0] rotate_amount1 = 0; reg [AW1-1:0] rotate_idx1 = 0; reg rotate_dir1 = 0; reg method_sel1 = 0; wire rotate_done1;

    toroidal_regfile #(.WIDTH(W1), .NUM(N1), .ADDR_WIDTH(AW1)) dut1 (
        .clk(clk), .rst_n(rst_n), .wr_en(wr_en1), .wr_addr(wr_addr1), .wr_data(wr_data1),
        .rd_en(rd_en1), .rd_addr(rd_addr1), .rd_data(rd_data1),
        .rotate_start(rotate_start1), .rotate_amount(rotate_amount1), .rotate_idx(rotate_idx1), .rotate_dir(rotate_dir1), .method_sel(method_sel1), .rotate_done(rotate_done1)
    );

    // --- W=128 instance
    localparam W2 = 128;
    localparam N2 = 2;
    localparam AW2 = 1;

    reg wr_en2 = 0; reg [AW2-1:0] wr_addr2 = 0; reg [W2-1:0] wr_data2 = 0;
    reg rd_en2 = 0; reg [AW2-1:0] rd_addr2 = 0; wire [W2-1:0] rd_data2;
    reg rotate_start2 = 0; reg [31:0] rotate_amount2 = 0; reg [AW2-1:0] rotate_idx2 = 0; reg rotate_dir2 = 0; reg method_sel2 = 0; wire rotate_done2;

    toroidal_regfile #(.WIDTH(W2), .NUM(N2), .ADDR_WIDTH(AW2)) dut2 (
        .clk(clk), .rst_n(rst_n), .wr_en(wr_en2), .wr_addr(wr_addr2), .wr_data(wr_data2),
        .rd_en(rd_en2), .rd_addr(rd_addr2), .rd_data(rd_data2),
        .rotate_start(rotate_start2), .rotate_amount(rotate_amount2), .rotate_idx(rotate_idx2), .rotate_dir(rotate_dir2), .method_sel(method_sel2), .rotate_done(rotate_done2)
    );

    // --- W=832 instance
    localparam W3 = 832;
    localparam N3 = 2;
    localparam AW3 = 1;

    reg wr_en3 = 0; reg [AW3-1:0] wr_addr3 = 0; reg [W3-1:0] wr_data3 = 0;
    reg rd_en3 = 0; reg [AW3-1:0] rd_addr3 = 0; wire [W3-1:0] rd_data3;
    reg rotate_start3 = 0; reg [31:0] rotate_amount3 = 0; reg [AW3-1:0] rotate_idx3 = 0; reg rotate_dir3 = 0; reg method_sel3 = 0; wire rotate_done3;

    toroidal_regfile #(.WIDTH(W3), .NUM(N3), .ADDR_WIDTH(AW3)) dut3 (
        .clk(clk), .rst_n(rst_n), .wr_en(wr_en3), .wr_addr(wr_addr3), .wr_data(wr_data3),
        .rd_en(rd_en3), .rd_addr(rd_addr3), .rd_data(rd_data3),
        .rotate_start(rotate_start3), .rotate_amount(rotate_amount3), .rotate_idx(rotate_idx3), .rotate_dir(rotate_dir3), .method_sel(method_sel3), .rotate_done(rotate_done3)
    );

    // reference rotate functions
    function [W1-1:0] rot_ref_w1;
        input [W1-1:0] val; input [31:0] amt; input dir; integer kk;
        begin kk = (amt % W1); if (kk == 0) rot_ref_w1 = val; else if (dir == 0) rot_ref_w1 = (val << kk) | (val >> (W1 - kk)); else rot_ref_w1 = (val >> kk) | (val << (W1 - kk)); end
    endfunction

    function [W2-1:0] rot_ref_w2;
        input [W2-1:0] val; input [31:0] amt; input dir; integer kk;
        begin kk = (amt % W2); if (kk == 0) rot_ref_w2 = val; else if (dir == 0) rot_ref_w2 = (val << kk) | (val >> (W2 - kk)); else rot_ref_w2 = (val >> kk) | (val << (W2 - kk)); end
    endfunction

    function [W3-1:0] rot_ref_w3;
        input [W3-1:0] val; input [31:0] amt; input dir; integer kk;
        begin kk = (amt % W3); if (kk == 0) rot_ref_w3 = val; else if (dir == 0) rot_ref_w3 = (val << kk) | (val >> (W3 - kk)); else rot_ref_w3 = (val >> kk) | (val << (W3 - kk)); end
    endfunction

    integer pass_count = 0;
    integer fail_count = 0;
    integer iwait;

    task test_w1(input [31:0] amt, input dir, input comb);
        begin
            // write pattern
            wr_en1 = 1; wr_addr1 = 0; wr_data1 = 32'hDEADBEEF; @(posedge clk); wr_en1 = 0;
            @(posedge clk); // allow write to take effect
            // verify write visibility (wait up to 8 cycles)
            iwait = 0;
            while (iwait < 8) begin
                rd_en1 = 1; rd_addr1 = 0; @(posedge clk); rd_en1 = 0; @(posedge clk);
                if (rd_data1 == 32'hDEADBEEF) begin $display("W1 WRITE_VERIFY OK"); break; end
                iwait = iwait + 1;
            end
            if (iwait == 8) $display("W1 WRITE_VERIFY_TIMEOUT: rd=%h", rd_data1);
            if (comb) begin
                method_sel1 = 0; rotate_amount1 = amt; rotate_idx1 = 0; rotate_dir1 = dir; @(posedge clk); rotate_start1 = 1; @(posedge clk); rotate_start1 = 0; wait (rotate_done1 == 1'b1);
            end else begin
                method_sel1 = 1; rotate_amount1 = amt; rotate_idx1 = 0; rotate_dir1 = dir; @(posedge clk); rotate_start1 = 1; @(posedge clk); rotate_start1 = 0; wait (rotate_done1 == 1'b1);
            end
            @(posedge clk);
            rd_en1 = 1; rd_addr1 = 0; @(posedge clk); rd_en1 = 0; @(posedge clk);
            if (rd_data1 == rot_ref_w1(32'hDEADBEEF, amt, dir)) begin $display("W1 PASS amt=%0d dir=%0d comb=%0d", amt, dir, comb); pass_count = pass_count + 1; end else begin $display("W1 FAIL amt=%0d dir=%0d comb=%0d got=%h exp=%h", amt, dir, comb, rd_data1, rot_ref_w1(32'hDEADBEEF, amt, dir)); fail_count = fail_count + 1; end
        end
    endtask

    task test_w2(input [31:0] amt, input dir, input comb);
        reg [W2-1:0] pat;
        begin
            pat = {4{32'hCAFEBABE}};
            wr_en2 = 1; wr_addr2 = 0; wr_data2 = pat; @(posedge clk); wr_en2 = 0;
            @(posedge clk);
            // verify write visibility (wait up to 8 cycles)
            iwait = 0;
            while (iwait < 8) begin
                rd_en2 = 1; rd_addr2 = 0; @(posedge clk); rd_en2 = 0; @(posedge clk);
                if (rd_data2 == pat) begin $display("W2 WRITE_VERIFY OK"); break; end
                iwait = iwait + 1;
            end
            if (iwait == 8) $display("W2 WRITE_VERIFY_TIMEOUT: rd=%h", rd_data2);
            if (comb) begin
                method_sel2 = 0; rotate_amount2 = amt; rotate_idx2 = 0; rotate_dir2 = dir; @(posedge clk); rotate_start2 = 1; @(posedge clk); rotate_start2 = 0; wait (rotate_done2 == 1'b1);
            end else begin
                method_sel2 = 1; rotate_amount2 = amt; rotate_idx2 = 0; rotate_dir2 = dir; @(posedge clk); rotate_start2 = 1; @(posedge clk); rotate_start2 = 0; wait (rotate_done2 == 1'b1);
            end
            @(posedge clk);
            rd_en2 = 1; rd_addr2 = 0; @(posedge clk); rd_en2 = 0; @(posedge clk);
            if (rd_data2 == rot_ref_w2(pat, amt, dir)) begin $display("W2 PASS amt=%0d dir=%0d comb=%0d", amt, dir, comb); pass_count = pass_count + 1; end else begin $display("W2 FAIL amt=%0d dir=%0d comb=%0d", amt, dir, comb); fail_count = fail_count + 1; end
        end
    endtask

    task test_w3(input [31:0] amt, input dir, input comb);
        reg [W3-1:0] pat;
        begin
            pat = {26{32'hDEADBEEF}}; // 26*32 = 832
            wr_en3 = 1; wr_addr3 = 0; wr_data3 = pat; @(posedge clk); wr_en3 = 0;
            @(posedge clk);
            // verify write visibility (wait up to 8 cycles)
            iwait = 0;
            while (iwait < 8) begin
                rd_en3 = 1; rd_addr3 = 0; @(posedge clk); rd_en3 = 0; @(posedge clk);
                if (rd_data3 == pat) begin $display("W3 WRITE_VERIFY OK"); break; end
                iwait = iwait + 1;
            end
            if (iwait == 8) $display("W3 WRITE_VERIFY_TIMEOUT: rd=%h", rd_data3);
            if (comb) begin
                method_sel3 = 0; rotate_amount3 = amt; rotate_idx3 = 0; rotate_dir3 = dir; @(posedge clk); rotate_start3 = 1; @(posedge clk); rotate_start3 = 0; wait (rotate_done3 == 1'b1);
            end else begin
                method_sel3 = 1; rotate_amount3 = amt; rotate_idx3 = 0; rotate_dir3 = dir; @(posedge clk); rotate_start3 = 1; @(posedge clk); rotate_start3 = 0; wait (rotate_done3 == 1'b1);
            end
            @(posedge clk);
            rd_en3 = 1; rd_addr3 = 0; @(posedge clk); rd_en3 = 0; @(posedge clk);
            if (rd_data3 == rot_ref_w3(pat, amt, dir)) begin $display("W3 PASS amt=%0d dir=%0d comb=%0d", amt, dir, comb); pass_count = pass_count + 1; end else begin $display("W3 FAIL amt=%0d dir=%0d comb=%0d", amt, dir, comb); fail_count = fail_count + 1; end
        end
    endtask

    initial begin
        wait (rst_n == 1);
        @(posedge clk); @(posedge clk); // settle after reset
        // run test vectors
        test_w1(0,0,1); // zero rotate, comb
        test_w1(1,0,1); // rotate 1 left, comb
        test_w1(31,0,1); // rotate 31 left
        test_w1(33,0,1); // rotate wrap amount > width
        test_w1(5,1,0); // serial rotate right by 5

        test_w2(0,0,1);
        test_w2(1,0,1);
        test_w2(127,0,1);
        test_w2(129,0,1);
        test_w2(3,1,0);

        test_w3(0,0,1);
        test_w3(1,0,1);
        test_w3(831,0,1);
        test_w3(833,0,1);
        test_w3(7,1,0);

        $display("REGRESSION: PASS=%0d FAIL=%0d", pass_count, fail_count);
        if (fail_count == 0) $display("REGRESSION PASS"); else $display("REGRESSION FAIL");
        $finish;
    end
endmodule
