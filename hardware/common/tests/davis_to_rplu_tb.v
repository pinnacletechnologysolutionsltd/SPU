`timescale 1ns/1ps
module davis_to_rplu_tb;
    reg clk = 0; always #1 clk = ~clk;
    reg rst_n = 0; initial begin #5 rst_n = 1; end

    reg start;
    reg [63:0] q_vector;
    reg material_id;
    // runtime config interface (no-op by default)
    reg cfg_wr_en = 1'b0;
    reg [2:0] cfg_wr_sel = 3'd0;
    reg cfg_wr_material = 1'b0;
    reg [9:0] cfg_wr_addr = 10'd0;
    reg [63:0] cfg_wr_data = 64'd0;
    wire signed [31:0] v_q16;
    wire dissoc;
    wire done;

    davis_to_rplu uut(.clk(clk), .rst_n(rst_n), .start(start), .q_vector(q_vector), .material_id(material_id), .cfg_wr_en(cfg_wr_en), .cfg_wr_sel(cfg_wr_sel), .cfg_wr_material(cfg_wr_material), .cfg_wr_addr(cfg_wr_addr), .cfg_wr_data(cfg_wr_data), .v_q16(v_q16), .dissoc(dissoc), .done(done));

    integer i;
    initial begin
        material_id = 0;
        // wait for reset
        @(posedge rst_n);
        // example q_vector: A=100, B=100, C=100, D=100 (packed 4x16)
        q_vector = {16'd100,16'd100,16'd100,16'd100};
        start = 1; @(posedge clk); start = 0;
        $display("TB: fired start for davis_to_rplu at time=%0t", $time);
        // wait for done
        wait (done) @(posedge clk);
        $display("davis_to_rplu_tb: v_q16=%0d dissoc=%b done=%b", v_q16, dissoc, done);
        $finish;
    end
endmodule
