`timescale 1ns/1ps

module rplu_cfg_cdc_tb;
    reg clk_src = 0;
    reg clk_dst = 0;
    reg rst_n_src = 0;
    reg rst_n_dst = 0;

    always #3 clk_src = ~clk_src;
    always #5 clk_dst = ~clk_dst;

    reg wr_src = 0;
    reg [2:0] sel_src = 0;
    reg [7:0] material_src = 0;
    reg [9:0] addr_src = 0;
    reg [63:0] data_src = 0;

    wire wr_dst;
    wire [2:0] sel_dst;
    wire [7:0] material_dst;
    wire [9:0] addr_dst;
    wire [63:0] data_dst;

    rplu_cfg_cdc dut (
        .clk_src(clk_src),
        .rst_n_src(rst_n_src),
        .wr_src(wr_src),
        .sel_src(sel_src),
        .material_src(material_src),
        .addr_src(addr_src),
        .data_src(data_src),
        .clk_dst(clk_dst),
        .rst_n_dst(rst_n_dst),
        .wr_dst(wr_dst),
        .sel_dst(sel_dst),
        .material_dst(material_dst),
        .addr_dst(addr_dst),
        .data_dst(data_dst)
    );

    integer errors = 0;
    integer timeout = 0;
    reg seen_wr = 0;
    reg [2:0] seen_sel = 0;
    reg [7:0] seen_material = 0;
    reg [9:0] seen_addr = 0;
    reg [63:0] seen_data = 0;

    always @(posedge clk_dst) begin
        if (!rst_n_dst) begin
            seen_wr <= 1'b0;
            seen_sel <= 3'd0;
            seen_material <= 8'd0;
            seen_addr <= 10'd0;
            seen_data <= 64'd0;
        end else if (wr_dst) begin
            seen_wr <= 1'b1;
            seen_sel <= sel_dst;
            seen_material <= material_dst;
            seen_addr <= addr_dst;
            seen_data <= data_dst;
        end
    end

    initial begin
        $dumpfile("build/rplu_cfg_cdc_tb.vcd");
        $dumpvars(0, rplu_cfg_cdc_tb);

        #20;
        rst_n_src = 1;
        rst_n_dst = 1;
        #20;

        sel_src = 3'd5;
        material_src = 8'd7;
        addr_src = 10'h123;
        data_src = 64'h1122_3344_5566_7788;
        @(posedge clk_src);
        wr_src <= 1'b1;
        @(posedge clk_src);
        wr_src <= 1'b0;

        while (!seen_wr && timeout < 100) begin
            @(posedge clk_dst);
            timeout = timeout + 1;
        end

        #1;
        if (!seen_wr) begin
            $display("FAIL: timed out waiting for wr_dst");
            errors = errors + 1;
        end
        if (seen_sel !== 3'd5) begin
            $display("FAIL: sel_dst=%0d", seen_sel);
            errors = errors + 1;
        end
        if (seen_material !== 8'd7) begin
            $display("FAIL: material_dst=%0d", seen_material);
            errors = errors + 1;
        end
        if (seen_addr !== 10'h123) begin
            $display("FAIL: addr_dst=%h", seen_addr);
            errors = errors + 1;
        end
        if (seen_data !== 64'h1122_3344_5566_7788) begin
            $display("FAIL: data_dst=%h", seen_data);
            errors = errors + 1;
        end

        if (errors == 0) $display("PASS");
        else $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
