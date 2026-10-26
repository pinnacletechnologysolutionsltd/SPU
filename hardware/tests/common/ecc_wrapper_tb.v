`timescale 1ns / 1ps
module ecc_wrapper_tb;
    reg clk = 0, rst_n = 0;
    reg [3:0] rd_lane;
    wire [63:0] rd_A, rd_B, rd_C, rd_D;
    reg wr_en, init_en;
    reg [3:0] wr_lane = 0, init_lane = 0;
    reg [63:0] wr_A, wr_B, wr_C, wr_D;
    reg [63:0] init_A, init_B, init_C, init_D;
    wire [63:0] dbg_A, dbg_B, dbg_C, dbg_D;
    wire ecc_single_err, ecc_double_err;
    integer errors = 0;

    spu_quadray_regfile_ecc uut (
        .clk(clk), .rst_n(rst_n),
        .rd_lane(rd_lane), .rd_A(rd_A), .rd_B(rd_B), .rd_C(rd_C), .rd_D(rd_D),
        .wr_en(wr_en), .wr_lane(wr_lane),
        .wr_A(wr_A), .wr_B(wr_B), .wr_C(wr_C), .wr_D(wr_D),
        .init_en(init_en), .init_lane(init_lane),
        .init_A(init_A), .init_B(init_B), .init_C(init_C), .init_D(init_D),
        .dbg_A(dbg_A), .dbg_B(dbg_B), .dbg_C(dbg_C), .dbg_D(dbg_D),
        .ecc_single_err(ecc_single_err), .ecc_double_err(ecc_double_err)
    );

    always #5 clk = ~clk;

    task check;
        input [3:0] lane;
        input [63:0] ea, eb, ec, ed;
        begin
            rd_lane = lane;
            #1;
            if (rd_A !== ea || rd_B !== eb || rd_C !== ec || rd_D !== ed) begin
                $display("FAIL lane %0d: A=%h exp=%h B=%h exp=%h", lane, rd_A, ea, rd_B, eb);
                errors = errors + 1;
            end else begin
                $display("PASS lane %0d", lane);
            end
        end
    endtask

    initial begin
        $display("=== ECC Wrapper Test ===");
        #12 rst_n = 1; #10;
        check(0, 64'h0000_0001_0000_0000, 64'd0, 64'd0, 64'd0);
        @(posedge clk); wr_en=1; wr_lane=0; wr_A=64'd1; wr_B=64'd2; wr_C=64'd3; wr_D=64'd4;
        @(posedge clk); wr_en=0;
        @(posedge clk); check(0, 64'd1, 64'd2, 64'd3, 64'd4);
        @(posedge clk); wr_en=1; wr_lane=1; wr_A=64'd5; wr_B=64'd6; wr_C=64'd7; wr_D=64'd8;
        @(posedge clk); wr_en=0;
        @(posedge clk); check(0, 64'd1, 64'd2, 64'd3, 64'd4);
        @(posedge clk); check(1, 64'd5, 64'd6, 64'd7, 64'd8);
        @(posedge clk); init_en=1; init_lane=3; init_A=64'hA; init_B=64'hB; init_C=64'hC; init_D=64'hD;
        @(posedge clk); init_en=0;
        @(posedge clk); check(3, 64'hA, 64'hB, 64'hC, 64'hD);
        if (ecc_single_err) $display("ERROR: unexpected single_err");
        if (ecc_double_err) $display("ERROR: unexpected double_err");
        if (errors == 0) $display("PASS"); else $display("FAIL errors=%0d", errors);
        $finish;
    end
endmodule
