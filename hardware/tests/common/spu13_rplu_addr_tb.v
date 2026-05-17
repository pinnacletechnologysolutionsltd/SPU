`timescale 1ns/1ps
`include "spu_arch_defines.vh"

module spu13_rplu_addr_tb;
    reg clk = 0;
    always #5 clk = ~clk;

    reg rst_n = 0;
    reg phi_8 = 0;
    reg phi_13 = 0;
    reg phi_21 = 0;

    wire mem_burst_rd;
    wire mem_burst_wr;
    wire [23:0] mem_addr;
    wire [831:0] mem_wr_manifold;
    wire [9:0] rplu_addr;

    spu13_core #(
        .DEVICE("SIM"),
        .ENABLE_RPLU(1),
        .ENABLE_LATTICE(0),
        .ENABLE_MATH(0)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .phi_8(phi_8),
        .phi_13(phi_13),
        .phi_21(phi_21),
        .dec_fast_cfg_wr_en(1'b0),
        .dec_fast_cfg_sel(3'd0),
        .dec_fast_cfg_material(8'd0),
        .dec_fast_cfg_addr(10'd0),
        .dec_fast_cfg_data(64'd0),
        .phinary_cfg(16'h0001),
        .prime_data(24'd0),
        .prime_addr(4'd0),
        .prime_we(1'b0),
        .boot_done(1'b1),
        .pell_data(32'd0),
        .pell_addr(3'd0),
        .pell_we(1'b0),
        .manual_rotor_en(1'b0),
        .manual_rotor_data(64'd0),
        .mem_ready(1'b1),
        .mem_burst_rd(mem_burst_rd),
        .mem_burst_wr(mem_burst_wr),
        .mem_addr(mem_addr),
        .mem_rd_manifold(832'd0),
        .mem_wr_manifold(mem_wr_manifold),
        .mem_burst_done(1'b1),
        .artery_wr_en(),
        .artery_wr_data(),
        .current_axis_ptr(),
        .current_axis_data(),
        .inst_valid(1'b0),
        .inst_word(64'd0),
        .ratio_cmp_res(),
        .ratio_cmp_valid(),
        .manifold_out(),
        .bloom_complete(),
        .scale_table_out(),
        .scale_overflow_out(),
        .is_janus_point(),
        .audio_mode(),
        .gasket_sum_out(),
        .quadrance_out(),
        .cycle_wrap(),
        .rplu_dissoc_out(),
        .rplu_dissoc_mask_out(),
        .rplu_addr_out(rplu_addr)
    );

    task pulse_phi8;
        begin
            @(negedge clk); phi_8 = 1'b1;
            @(negedge clk); phi_8 = 1'b0;
        end
    endtask

    task pulse_phi21;
        begin
            @(negedge clk); phi_21 = 1'b1;
            @(negedge clk); phi_21 = 1'b0;
        end
    endtask

    integer i;
    integer errors = 0;

    initial begin
        repeat (3) @(negedge clk);
        rst_n = 1'b1;
        pulse_phi8();

        for (i = 0; i < 13; i = i + 1) begin
            pulse_phi21();
            @(posedge clk);
            $display("axis=%0d rplu_addr=%0d", i, rplu_addr);
        end

        if (rplu_addr !== 10'd1023) begin
            $display("FAIL: final RPLU address got %0d expected 1023", rplu_addr);
            errors = errors + 1;
        end

        if (errors == 0) $display("PASS"); else $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
