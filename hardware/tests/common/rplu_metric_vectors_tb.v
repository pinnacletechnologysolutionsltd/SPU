`timescale 1ns/1ps

module rplu_metric_vectors_tb;
    parameter VECTOR_COUNT = 32;

    reg clk = 0;
    always #1 clk = ~clk;

    reg rst_n = 0;
    initial begin #5 rst_n = 1; end

    reg start = 1'b0;
    reg [9:0] addr = 10'd0;
    reg [7:0] material_id = 8'd0;
    reg signed [31:0] r_q16 = 32'sd0;
    reg cfg_wr_en = 1'b0;
    reg [2:0] cfg_wr_sel = 3'd0;
    reg [7:0] cfg_wr_material = 8'd0;
    reg [9:0] cfg_wr_addr = 10'd0;
    reg [63:0] cfg_wr_data = 64'd0;

    wire signed [31:0] v_q16;
    wire dissoc;
    wire done;
    wire signed [2:0] ratio_cmp_res;
    wire ratio_cmp_valid;
    wire laminar_irq;

    rplu_exp uut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .addr(addr),
        .material_id(material_id),
        .r_q16(r_q16),
        .wake(1'b0),
        .wake_addr(10'd0),
        .cfg_wr_en(cfg_wr_en),
        .cfg_wr_sel(cfg_wr_sel),
        .cfg_wr_material(cfg_wr_material),
        .cfg_wr_addr(cfg_wr_addr),
        .cfg_wr_data(cfg_wr_data),
        .v_q16(v_q16),
        .dissoc(dissoc),
        .done(done),
        .laminar_irq(laminar_irq),
        .ratio_cmp_res(ratio_cmp_res),
        .ratio_cmp_valid(ratio_cmp_valid)
    );

    reg [9:0] addr_vec [0:VECTOR_COUNT-1];
    reg [31:0] r_vec [0:VECTOR_COUNT-1];
    reg [31:0] v_vec [0:VECTOR_COUNT-1];
    reg [0:0] d_vec [0:VECTOR_COUNT-1];

    integer i;
    integer errors = 0;
    integer diff;

    initial begin
        $readmemh("build/rplu_metrics/rplu_addr.mem", addr_vec);
        $readmemh("build/rplu_metrics/rplu_r_q16.mem", r_vec);
        $readmemh("build/rplu_metrics/rplu_v_q16.mem", v_vec);
        $readmemh("build/rplu_metrics/rplu_dissoc.mem", d_vec);

        @(posedge rst_n);
        material_id = 8'd0;

        for (i = 0; i < VECTOR_COUNT; i = i + 1) begin
            @(negedge clk);
            addr = addr_vec[i];
            r_q16 = $signed(r_vec[i]);
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;

            while (done) @(posedge clk);
            while (!done) @(posedge clk);
            diff = v_q16 - $signed(v_vec[i]);
            if (diff < 0) diff = -diff;
            if (diff > 1024) begin
                $display(
                    "ERROR vector[%0d] addr=%0d v got=0x%08h expected=0x%08h diff=%0d",
                    i, addr_vec[i], v_q16, v_vec[i], diff
                );
                errors = errors + 1;
            end
            if (dissoc !== d_vec[i]) begin
                $display(
                    "ERROR vector[%0d] addr=%0d dissoc got=%0d expected=%0d",
                    i, addr_vec[i], dissoc, d_vec[i]
                );
                errors = errors + 1;
            end
        end

        if (errors == 0) $display("PASS"); else $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
