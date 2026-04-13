`timescale 1ns/1ps
module rplu_tb;
    reg clk = 0;
    always #1 clk = ~clk;

    reg rst_n = 0;
    initial begin
        #5 rst_n = 1;
    end

    reg start;
    reg [9:0] addr;
    reg material_id;
    // runtime config interface (no-op by default)
    reg cfg_wr_en = 1'b0;
    reg [2:0] cfg_wr_sel = 3'd0;
    reg cfg_wr_material = 1'b0;
    reg [9:0] cfg_wr_addr = 10'd0;
    reg [63:0] cfg_wr_data = 64'd0;
    wire signed [31:0] p_out;
    wire signed [31:0] q_out;
    wire dissoc;
    wire done;

    rplu_skel uut (.clk(clk), .rst_n(rst_n), .start(start), .addr(addr), .material_id(material_id), .cfg_wr_en(cfg_wr_en), .cfg_wr_sel(cfg_wr_sel), .cfg_wr_material(cfg_wr_material), .cfg_wr_addr(cfg_wr_addr), .cfg_wr_data(cfg_wr_data), .p_out(p_out), .q_out(q_out), .dissoc(dissoc), .done(done));

    // load expected ROMs for verification
    reg [63:0] exp_carbon [0:1023];
    reg [63:0] exp_iron   [0:1023];
    reg [0:0]  exp_diss_c [0:1023];
    reg [0:0]  exp_diss_i [0:1023];
    initial begin
        $readmemh("hardware/common/rtl/gpu/rplu_rom_carbon.mem", exp_carbon);
        $readmemh("hardware/common/rtl/gpu/rplu_rom_iron.mem",   exp_iron);
        $readmemh("hardware/common/rtl/gpu/rplu_dissoc_carbon.mem", exp_diss_c);
        $readmemh("hardware/common/rtl/gpu/rplu_dissoc_iron.mem",   exp_diss_i);
    end

    integer i;
    integer errors = 0;

    initial begin
        start = 0; addr = 0; material_id = 0;
        #20;
        // test carbon
        material_id = 0;
        for (i = 0; i < 1024; i = i + 1) begin
            addr = i; start = 1; #2 start = 0; #2;
            // read expected
            if (p_out !== $signed(exp_carbon[i][63:32]) || q_out !== $signed(exp_carbon[i][31:0]) || dissoc !== exp_diss_c[i]) begin
                $display("ERROR carbon[%0d]: got p=%0d q=%0d diss=%0d expected p=%0d q=%0d diss=%0d", i, p_out, q_out, dissoc, $signed(exp_carbon[i][63:32]), $signed(exp_carbon[i][31:0]), exp_diss_c[i]);
                errors = errors + 1;
            end
        end
        // test iron
        material_id = 1;
        for (i = 0; i < 1024; i = i + 1) begin
            addr = i; start = 1; #2 start = 0; #2;
            if (p_out !== $signed(exp_iron[i][63:32]) || q_out !== $signed(exp_iron[i][31:0]) || dissoc !== exp_diss_i[i]) begin
                $display("ERROR iron[%0d]: got p=%0d q=%0d diss=%0d expected p=%0d q=%0d diss=%0d", i, p_out, q_out, dissoc, $signed(exp_iron[i][63:32]), $signed(exp_iron[i][31:0]), exp_diss_i[i]);
                errors = errors + 1;
            end
        end
        if (errors == 0) $display("PASS"); else $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
