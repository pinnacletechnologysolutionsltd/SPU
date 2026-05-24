// spu_mem_bridge_sdram_xsds_tb.v
// Verifies Tang_sdram_xsds-style inverted-CS dual-rank selection.

`timescale 1ns/1ps

module spu_mem_bridge_sdram_xsds_tb;
    reg clk = 0;
    always #10 clk = ~clk;

    integer pass_count = 0;
    integer fail_count = 0;
    integer i;

    task pass; input [511:0] name;
        begin $display("  PASS  %0s", name); pass_count = pass_count + 1; end
    endtask

    task fail; input [511:0] name; input [63:0] got; input [63:0] exp;
        begin
            $display("  FAIL  %0s  got=%h exp=%h", name, got, exp);
            fail_count = fail_count + 1;
        end
    endtask

    localparam [24:0] RANK0_ADDR = 25'h0000000;
    localparam [24:0] RANK1_ADDR = 25'h1000000;

    reg          reset = 1;
    reg          mem_burst_rd = 0;
    reg          mem_burst_wr = 0;
    reg  [24:0]  mem_addr = 25'd0;
    reg  [831:0] mem_wr_manifold = 832'd0;
    wire [831:0] mem_rd_manifold;
    wire         mem_ready;
    wire         mem_burst_done;

    wire         sdram_clk, sdram_cke, sdram_cs_n;
    wire         sdram_ras_n, sdram_cas_n, sdram_we_n;
    wire [1:0]   sdram_ba;
    wire [12:0]  sdram_addr_pin;
    wire [15:0]  sdram_dq;

    spu_mem_bridge_sdram #(
        .T_INIT(8),
        .COL_BITS(9),
        .ROW_BITS(13),
        .RANK_BITS(1),
        .XSDS_INVERTED_RANK_CS(1),
        .T_REFI(2000)
    ) dut (
        .clk(clk),
        .reset(reset),
        .mem_ready(mem_ready),
        .mem_burst_rd(mem_burst_rd),
        .mem_burst_wr(mem_burst_wr),
        .mem_addr(mem_addr),
        .mem_rd_manifold(mem_rd_manifold),
        .mem_wr_manifold(mem_wr_manifold),
        .mem_burst_done(mem_burst_done),
        .sdram_clk(sdram_clk),
        .sdram_cke(sdram_cke),
        .sdram_cs_n(sdram_cs_n),
        .sdram_ras_n(sdram_ras_n),
        .sdram_cas_n(sdram_cas_n),
        .sdram_we_n(sdram_we_n),
        .sdram_ba(sdram_ba),
        .sdram_addr(sdram_addr_pin),
        .sdram_dq(sdram_dq)
    );

    reg [15:0] rank0_mem [0:63];
    reg [15:0] rank1_mem [0:63];

    reg [5:0] cas_col [0:2];
    reg       cas_rank [0:2];
    reg       cas_valid [0:2];

    wire [2:0] sdram_cmd = {sdram_ras_n, sdram_cas_n, sdram_we_n};
    localparam MCMD_READ  = 3'b101;
    localparam MCMD_WRITE = 3'b100;

    reg [15:0] dq_out;
    reg        dq_en;
    assign sdram_dq = dq_en ? dq_out : 16'hzzzz;

    wire selected_rank = sdram_cs_n;

    integer k;
    initial begin
        for (k = 0; k < 3; k = k + 1) begin
            cas_col[k] = 6'd0;
            cas_rank[k] = 1'b0;
            cas_valid[k] = 1'b0;
        end
        for (k = 0; k < 64; k = k + 1) begin
            rank0_mem[k] = 16'd0;
            rank1_mem[k] = 16'd0;
        end
        dq_out = 16'd0;
        dq_en = 1'b0;
    end

    always @(posedge sdram_clk) begin
        cas_col[2]   <= cas_col[1];
        cas_rank[2]  <= cas_rank[1];
        cas_valid[2] <= cas_valid[1];
        cas_col[1]   <= cas_col[0];
        cas_rank[1]  <= cas_rank[0];
        cas_valid[1] <= cas_valid[0];
        cas_col[0]   <= 6'd0;
        cas_rank[0]  <= 1'b0;
        cas_valid[0] <= 1'b0;

        if (sdram_cmd == MCMD_READ) begin
            cas_col[0]   <= sdram_addr_pin[5:0];
            cas_rank[0]  <= selected_rank;
            cas_valid[0] <= 1'b1;
        end

        if (sdram_cmd == MCMD_WRITE) begin
            if (selected_rank) rank1_mem[sdram_addr_pin[5:0]] <= sdram_dq;
            else               rank0_mem[sdram_addr_pin[5:0]] <= sdram_dq;
        end

        dq_en <= cas_valid[2];
        if (cas_valid[2]) begin
            dq_out <= cas_rank[2] ? rank1_mem[cas_col[2]] : rank0_mem[cas_col[2]];
        end else begin
            dq_out <= 16'd0;
        end
    end

    task write_burst;
        input [24:0] addr;
        input [15:0] base;
        begin
            for (i = 0; i < 52; i = i + 1)
                mem_wr_manifold[i*16 +: 16] = base + i[15:0];
            mem_addr = addr;
            @(posedge clk); #1;
            mem_burst_wr = 1'b1;
            @(posedge clk); #1;
            mem_burst_wr = 1'b0;
            wait(mem_burst_done == 1'b1);
            @(posedge clk); #1;
        end
    endtask

    task read_burst;
        input [24:0] addr;
        begin
            mem_addr = addr;
            @(posedge clk); #1;
            mem_burst_rd = 1'b1;
            @(posedge clk); #1;
            mem_burst_rd = 1'b0;
            wait(mem_burst_done == 1'b1);
            @(posedge clk); #1;
        end
    endtask

    initial begin
        $display("============================================================");
        $display("spu_mem_bridge_sdram XSDS dual-rank Testbench");
        $display("============================================================");

        @(posedge clk); @(posedge clk); @(posedge clk);
        reset = 0;

        wait(mem_ready == 1'b1);
        @(posedge clk); #1;
        if (mem_ready === 1'b1) pass("xsds: mem_ready after dual-rank init");
        else                    fail("xsds: mem_ready after dual-rank init", 0, 1);

        write_burst(RANK0_ADDR, 16'hA000);
        write_burst(RANK1_ADDR, 16'hB000);

        if (rank0_mem[0] === 16'hA000) pass("xsds: rank0 write word[0]");
        else                           fail("xsds: rank0 write word[0]", {48'd0, rank0_mem[0]}, 64'hA000);
        if (rank1_mem[0] === 16'hB000) pass("xsds: rank1 write word[0]");
        else                           fail("xsds: rank1 write word[0]", {48'd0, rank1_mem[0]}, 64'hB000);

        read_burst(RANK0_ADDR);
        if (mem_rd_manifold[15:0] === 16'hA000) pass("xsds: rank0 read word[0]");
        else                                    fail("xsds: rank0 read word[0]",
                                                   {48'd0, mem_rd_manifold[15:0]}, 64'hA000);
        if (mem_rd_manifold[831:816] === 16'hA033) pass("xsds: rank0 read word[51]");
        else                                       fail("xsds: rank0 read word[51]",
                                                       {48'd0, mem_rd_manifold[831:816]}, 64'hA033);

        read_burst(RANK1_ADDR);
        if (mem_rd_manifold[15:0] === 16'hB000) pass("xsds: rank1 read word[0]");
        else                                    fail("xsds: rank1 read word[0]",
                                                   {48'd0, mem_rd_manifold[15:0]}, 64'hB000);
        if (mem_rd_manifold[831:816] === 16'hB033) pass("xsds: rank1 read word[51]");
        else                                       fail("xsds: rank1 read word[51]",
                                                       {48'd0, mem_rd_manifold[831:816]}, 64'hB033);

        $display("============================================================");
        $display("Result: %0d/%0d passed %s",
                  pass_count, pass_count+fail_count,
                  (fail_count == 0) ? "PASS" : "FAIL");
        $display("============================================================");
        $finish;
    end

    initial begin
        #800000;
        $display("TIMEOUT");
        $finish;
    end
endmodule
