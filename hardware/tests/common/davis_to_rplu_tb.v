`timescale 1ns/1ps
module davis_to_rplu_tb;
    reg clk = 0; always #1 clk = ~clk;
    reg rst_n = 0; initial begin #5 rst_n = 1; end

    reg start;
    reg [63:0] q_vector;
    reg [7:0] material_id;
    // runtime config interface (no-op by default)
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
    wire [9:0] r_addr_dbg;
    wire signed [31:0] r_q16_dbg;

    davis_to_rplu uut(.clk(clk), .rst_n(rst_n), .start(start), .q_vector(q_vector), .material_id(material_id), .cfg_wr_en(cfg_wr_en), .cfg_wr_sel(cfg_wr_sel), .cfg_wr_material(cfg_wr_material), .cfg_wr_addr(cfg_wr_addr), .cfg_wr_data(cfg_wr_data), .v_q16(v_q16), .dissoc(dissoc), .done(done), .ratio_cmp_res(ratio_cmp_res), .ratio_cmp_valid(ratio_cmp_valid), .r_addr_dbg(r_addr_dbg), .r_q16_dbg(r_q16_dbg));

    integer i;
    integer errors = 0;
    initial begin
        start = 1'b0;
        q_vector = 64'd0;
        material_id = 8'd0;
        // wait for reset
        @(posedge rst_n);
        // example q_vector: A=100, B=100, C=100, D=100 (packed 4x16)
        q_vector = {16'd100,16'd100,16'd100,16'd100};
        @(negedge clk); start = 1; @(negedge clk); start = 0;
        $display("TB: fired start for davis_to_rplu at time=%0t", $time);
        // wait for done
        wait (done) @(posedge clk);
        $display("davis_to_rplu_tb: v_q16=%0d dissoc=%b done=%b", v_q16, dissoc, done);

        // Large Q12 axis regression: shifting before clamping would wrap this
        // radius back to zero and select address 0. It must clamp to the high
        // end of the Morse table.
        q_vector = {32'h1000_0000, 32'd0};
        #1;
        if (uut.r_q16 !== 32'sh0002_4f5c) begin
            $display("ERROR large-axis r_q16: got 0x%08h expected 0x00024f5c", uut.r_q16);
            errors = errors + 1;
        end
        if (uut.r_addr !== 10'd1023) begin
            $display("ERROR large-axis r_addr: got %0d expected 1023", uut.r_addr);
            errors = errors + 1;
        end

        @(negedge clk); start = 1; @(negedge clk); start = 0;
        q_vector = 64'd0;
        wait (done) @(posedge clk);
        if (r_addr_dbg !== 10'd1023) begin
            $display("ERROR latched large-axis r_addr: got %0d expected 1023", r_addr_dbg);
            errors = errors + 1;
        end
        if (uut.u_rplu.addr_reg !== 10'd1023) begin
            $display("ERROR rplu captured addr: got %0d expected 1023", uut.u_rplu.addr_reg);
            errors = errors + 1;
        end
        $display("davis_to_rplu_tb: large-axis v_q16=%0d dissoc=%b r_addr=%0d", v_q16, dissoc, r_addr_dbg);

        if (errors == 0) $display("PASS"); else $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
