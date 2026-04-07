`timescale 1ns/1ps
module rplu_exp_tb;
    reg clk = 0;
    always #1 clk = ~clk;

    reg rst_n = 0;
    initial begin #5 rst_n = 1; end

    reg start;
    reg [9:0] addr;
    reg material_id;
    reg signed [31:0] r_q16;
    wire signed [31:0] v_q16;
    wire dissoc;
    wire done;

    rplu_exp uut(.clk(clk), .rst_n(rst_n), .start(start), .addr(addr), .material_id(material_id), .r_q16(r_q16), .v_q16(v_q16), .dissoc(dissoc), .done(done));

    reg [31:0] vnorm_exp [0:1023];
    reg [0:0]    vnorm_diss [0:1023];
    reg [31:0] r_rom [0:1023];

    initial begin
        $readmemh("hardware/common/rtl/gpu/vnorm_carbon.mem", vnorm_exp);
        $readmemh("hardware/common/rtl/gpu/vnorm_dissoc_carbon.mem", vnorm_diss);
        $readmemh("hardware/common/rtl/gpu/r_rom_carbon.mem", r_rom);
    end

    integer i;
    integer errors = 0;

    initial begin
        // test carbon
        material_id = 0;
        for (i = 0; i < 16; i = i + 1) begin
            addr = i; r_q16 = $signed(r_rom[i]); start = 1; @(posedge clk); start = 0; repeat(4) @(posedge clk); // wait for pipeline done
            // compare v_q16 to expected within tolerance (2 LSB)
            if ( (v_q16 - $signed(vnorm_exp[i])) > 2 || ($signed(vnorm_exp[i]) - v_q16) > 2 ) begin
                $display("ERROR v[%0d]: got %0d expected %0d", i, v_q16, $signed(vnorm_exp[i]));
                errors = errors + 1;
            end
            if (dissoc !== vnorm_diss[i]) begin
                $display("ERROR diss[%0d]: got %0d expected %0d", i, dissoc, vnorm_diss[i]);
                errors = errors + 1;
            end
        end
        if (errors == 0) $display("PASS"); else $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
