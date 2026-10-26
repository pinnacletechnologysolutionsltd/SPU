`timescale 1ns / 1ps
module toroidal_regfile_ecc_tb;
    reg clk = 0, rst_n = 0;
    reg wr_en, rd_en;
    reg [2:0] wr_addr, rd_addr;
    reg [831:0] wr_data;
    wire [831:0] rd_data;
    reg rotate_start, rotate_dir, method_sel;
    reg [31:0] rotate_amount;
    reg [2:0] rotate_idx;
    wire rotate_done, integrity_error;
    integer errors = 0;

    toroidal_regfile_ecc uut (
        .clk(clk), .rst_n(rst_n),
        .wr_en(wr_en), .wr_addr(wr_addr), .wr_data(wr_data),
        .rd_en(rd_en), .rd_addr(rd_addr), .rd_data(rd_data),
        .rotate_start(rotate_start), .rotate_amount(rotate_amount),
        .rotate_idx(rotate_idx), .rotate_dir(rotate_dir),
        .method_sel(method_sel), .rotate_done(rotate_done),
        .integrity_error(integrity_error)
    );

    always #5 clk = ~clk;

    task write;
        input [2:0] a;
        input [831:0] d;
        begin
            @(posedge clk);
            wr_en = 1; wr_addr = a; wr_data = d;
            @(posedge clk);
            wr_en = 0;
        end
    endtask

	    task read;
	        input [2:0] a;
	        begin
	            @(posedge clk);
	            rd_en = 1; rd_addr = a;
	            @(posedge clk);
	            #1;
	            if (integrity_error) $display("  integrity_error on lane %0d", a);
	            rd_en = 0;
	        end
	    endtask

	    initial begin
	        $display("=== Toroidal Integrity Test ===");
	        wr_en = 0; rd_en = 0;
	        wr_addr = 0; rd_addr = 0;
	        wr_data = {832{1'b0}};
	        rotate_start = 0; rotate_dir = 0; method_sel = 0;
	        rotate_amount = 32'd0; rotate_idx = 3'd0;
	        #12 rst_n = 1; #10;

        write(0, {832{1'b0}});
        read(0);
        if (rd_data !== {832{1'b0}}) begin
            $display("FAIL: zero write back"); errors = errors + 1;
        end else $display("PASS: zero write back");

        write(1, {13{64'hA5A5_A5A5_5A5A_5A5A}});
        read(1);
        if (rd_data !== {13{64'hA5A5_A5A5_5A5A_5A5A}}) begin
            $display("FAIL: pattern write back"); errors = errors + 1;
        end else $display("PASS: pattern write back");

        write(2, {832{1'b1}});
        read(2);
        if (rd_data !== {832{1'b1}}) begin
            $display("FAIL: all-ones write back"); errors = errors + 1;
        end else $display("PASS: all-ones write back");

        read(0);
        if (rd_data !== {832{1'b0}}) begin
            $display("FAIL: entry 0 preserved"); errors = errors + 1;
        end else $display("PASS: entry 0 preserved");
        read(1);
        if (rd_data !== {13{64'hA5A5_A5A5_5A5A_5A5A}}) begin
            $display("FAIL: entry 1 preserved"); errors = errors + 1;
        end else $display("PASS: entry 1 preserved");

        if (integrity_error) $display("ERROR: unexpected integrity error at end");

        if (errors == 0) $display("PASS"); else $display("FAIL errors=%0d", errors);
        $finish;
    end
endmodule
