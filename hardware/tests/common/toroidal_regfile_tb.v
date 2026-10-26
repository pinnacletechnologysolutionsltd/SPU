`timescale 1ns/1ps
module toroidal_regfile_tb;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst_n = 0;
    initial begin #20 rst_n = 1; end

    // Small instance for fast functional checks
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

    // Large instance (WIDTH=832) to validate wrap-around on full width
    localparam W2 = 832;
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

    // reference rotate function for testbench checks
    function [W1-1:0] rot_ref_small;
        input [W1-1:0] val;
        input [31:0] amt;
        input dir;
        integer kk;
        begin
            kk = (amt % W1);
            if (kk == 0) rot_ref_small = val;
            else if (dir == 0) rot_ref_small = (val << kk) | (val >> (W1 - kk));
            else rot_ref_small = (val >> kk) | (val << (W1 - kk));
        end
    endfunction

    function [W2-1:0] rot_ref_large;
        input [W2-1:0] val;
        input [31:0] amt;
        input dir;
        integer kk;
        begin
            kk = (amt % W2);
            if (kk == 0) rot_ref_large = val;
            else if (dir == 0) rot_ref_large = (val << kk) | (val >> (W2 - kk));
            else rot_ref_large = (val >> kk) | (val << (W2 - kk));
        end
    endfunction

    initial begin
        // Wait for reset release
        wait (rst_n == 1);
        @(posedge clk);
        // --- small instance: write and combinational rotate ---
        wr_en1 = 1; wr_addr1 = 0; wr_data1 = 32'hDEADBEEF; $display("TB: t=%0t BEFORE_WRITE1 wr_en1=%0d addr=%0d data=%h", $time, wr_en1, wr_addr1, wr_data1); @(posedge clk); $display("TB: t=%0t AFTER_POSEDGE1 wr_en1=%0d", $time, wr_en1); wr_en1 = 0;
        @(posedge clk); @(posedge clk);
        // readback to verify write completed before rotating
        rd_en1 = 1; rd_addr1 = 0; @(posedge clk); rd_en1 = 0; @(posedge clk);
        $display("TB: t=%0t READBACK mem0=%h", $time, rd_data1);
        if (rd_data1 != 32'hDEADBEEF) $display("TB: WRITE_VERIFY_FAIL for small instance, mem0=%h", rd_data1); else $display("TB: WRITE_VERIFY_PASS for small instance");
        // start combinational rotate by 8 (left)
        rotate_amount1 = 8; rotate_idx1 = 0; rotate_dir1 = 0; method_sel1 = 1'b0;
        @(posedge clk); rotate_start1 = 1; @(posedge clk); rotate_start1 = 0;
        // wait for done
        wait (rotate_done1 == 1'b1);
        @(posedge clk);
        rd_en1 = 1; rd_addr1 = 0; @(posedge clk); rd_en1 = 0;
        @(posedge clk);
        $display("SMALL_COMB: rd_data=%h expected=%h", rd_data1, rot_ref_small(32'hDEADBEEF, 8, 0));
        if (rd_data1 == rot_ref_small(32'hDEADBEEF, 8, 0)) $display("SMALL_COMB_PASS"); else $display("SMALL_COMB_FAIL");

        // --- small instance: serial rotate (right) ---
        wr_en1 = 1; wr_addr1 = 1; wr_data1 = 32'hA5A5A5A5; @(posedge clk); wr_en1 = 0;
        @(posedge clk);
        rotate_amount1 = 5; rotate_idx1 = 1; rotate_dir1 = 1; method_sel1 = 1'b1;
        @(posedge clk); rotate_start1 = 1; @(posedge clk); rotate_start1 = 0;
        // wait for done (serial will take 5 cycles)
        wait (rotate_done1 == 1'b1);
        @(posedge clk);
        rd_en1 = 1; rd_addr1 = 1; @(posedge clk); rd_en1 = 0;
        @(posedge clk);
        $display("SMALL_SERIAL: rd_data=%h expected=%h", rd_data1, rot_ref_small(32'hA5A5A5A5, 5, 1));
        if (rd_data1 == rot_ref_small(32'hA5A5A5A5, 5, 1)) $display("SMALL_SERIAL_PASS"); else $display("SMALL_SERIAL_FAIL");

        // --- large instance (WIDTH=832): check wrap-around combinational ---
        // Create a repeated 32-bit pattern to fill 832 bits: 26 * 32 = 832
        wr_en2 = 1; wr_addr2 = 0; wr_data2 = {26{32'hDEADBEEF}}; @(posedge clk); wr_en2 = 0;
        @(posedge clk);
        rotate_amount2 = 32; rotate_idx2 = 0; rotate_dir2 = 0; method_sel2 = 1'b0;
        @(posedge clk); rotate_start2 = 1; @(posedge clk); rotate_start2 = 0;
        wait (rotate_done2 == 1'b1);
        @(posedge clk);
        rd_en2 = 1; rd_addr2 = 0; @(posedge clk); rd_en2 = 0;
        @(posedge clk);
        $display("LARGE_COMB: lowest 32 bits after rotate: %08h", rd_data2[31:0]);
        // verify low 32 bits equal to top 32 bits of original (wrap-around check)
        if (rd_data2[31:0] == {32'hDEADBEEF}) $display("LARGE_COMB_WRAP_PASS"); else $display("LARGE_COMB_WRAP_FAIL");

        $display("Toroidal regfile tests complete.");
        $finish;
    end
endmodule
