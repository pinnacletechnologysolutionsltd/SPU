`timescale 1ns/1ps

module spu13_polystep_integration_tb;
    reg clk = 0;
    always #5 clk = ~clk; // 100 MHz-ish

    reg rst_n = 0;
    initial begin #20 rst_n = 1; end

    // Minimal memory stubs (not used by this test)
    wire mem_ready = 1'b1;
    wire mem_burst_rd;
    wire mem_burst_wr;
    wire [23:0] mem_addr;
    wire [831:0] mem_rd_manifold = 832'd0;
    wire [831:0] mem_wr_manifold;
    reg mem_burst_done = 1'b0;

    // dec_fast cfg inputs (unused here)
    wire dec_fast_cfg_wr_en = 1'b0;
    wire [2:0] dec_fast_cfg_sel = 3'd0;
    wire dec_fast_cfg_material = 1'b0;
    wire [9:0] dec_fast_cfg_addr = 10'd0;
    wire [63:0] dec_fast_cfg_data = 64'd0;

    // Instruction interface to core
    reg inst_valid = 1'b0;
    reg [63:0] inst_word = 64'd0;

    // Core outputs (artery)
    wire artery_wr_en;
    wire [63:0] artery_wr_data;

    // Instantiate SPU-13 core (DEVICE="SIM")
    spu13_core #(.DEVICE("SIM")) uut (
        .clk(clk), .rst_n(rst_n),
        .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .mem_ready(mem_ready),
        .mem_burst_rd(mem_burst_rd), .mem_burst_wr(mem_burst_wr),
        .mem_addr(mem_addr), .mem_rd_manifold(mem_rd_manifold), .mem_wr_manifold(mem_wr_manifold),
        .mem_burst_done(mem_burst_done),
        .dec_fast_cfg_wr_en(dec_fast_cfg_wr_en), .dec_fast_cfg_sel(dec_fast_cfg_sel), .dec_fast_cfg_material(dec_fast_cfg_material), .dec_fast_cfg_addr(dec_fast_cfg_addr), .dec_fast_cfg_data(dec_fast_cfg_data),
        .artery_wr_en(artery_wr_en), .artery_wr_data(artery_wr_data),
        .current_axis_ptr(), .current_axis_data(),
        .manifold_out(), .bloom_complete(), .is_janus_point(),
        .inst_valid(inst_valid), .inst_word(inst_word)
    );

    // Small decoder that converts core artery header into rplu_exp CFG write (test harness)
    reg cfg_wr_en = 1'b0;
    reg [2:0] cfg_wr_sel = 3'd0;
    reg cfg_wr_material = 1'b0;
    reg [9:0] cfg_wr_addr = 10'd0;
    reg [63:0] cfg_wr_data = 64'd0;
    reg [63:0] lat_header = 64'd0;

    always @(posedge clk) begin
        // sample any arterial header one cycle after it's emitted (simple sync)
        lat_header <= artery_wr_data;
        if (artery_wr_en) begin
            // one-cycle later will apply the CFG write (this emulates CDC/decoder latency)
            // leave fields in lat_header and TB may choose to pulse cfg_wr_en
        end
        if (lat_header[63:56] == 8'hA5) begin
            // build cfg write from sampled header (TB must pulse cfg_wr_en if desired)
            cfg_wr_sel <= lat_header[50:48];
            cfg_wr_material <= lat_header[47];
            cfg_wr_addr <= lat_header[46:37];
            cfg_wr_data <= 64'd0; // no DATA chord in this simple test
            // clear lat_header so we don't replay
            lat_header <= 64'd0;
        end
    end

    // Instantiate RPLU EXP and connect to our synthetic CFG writes
    wire signed [31:0] v_q16;
    wire dissoc;
    wire done;
    wire signed [2:0] ratio_cmp_res;

    rplu_exp rplu_u (
        .clk(clk), .rst_n(rst_n), .start(1'b0), .addr(10'd0), .material_id(1'b0), .r_q16(32'd0), .wake(1'b0), .wake_addr(10'd0),
        .cfg_wr_en(cfg_wr_en), .cfg_wr_sel(cfg_wr_sel), .cfg_wr_material(cfg_wr_material), .cfg_wr_addr(cfg_wr_addr), .cfg_wr_data(cfg_wr_data),
        .v_q16(v_q16), .dissoc(dissoc), .done(done), .laminar_irq(), .ratio_cmp_res(ratio_cmp_res)
    );

    integer errors = 0;
    integer i;
    reg found_header;

    initial begin
        $dumpfile("spu13_polystep_integration_tb.vcd");
        $dumpvars(0, spu13_polystep_integration_tb);

        // wait for reset
        @(posedge rst_n);
        $display("[TB] reset released at time=%0t", $time);

        // 1) Test: emit instruction POLY_STEP (opcode 0xE0) and check core produced an artery header
        // Build inst_word: [63:56]=0xE0, put address 3 into p1_a so inst_word[33:24]=3
        inst_word = (64'hE0 << 56) | (64'd3 << 24);
        // hold inst_valid for several cycles and sample outputs to detect the arterial header
        found_header = 1'b0;
        inst_valid = 1'b1;
        i = 0;
        while (i < 6 && !found_header) begin
            @(posedge clk);
            if (artery_wr_data[63:56] == 8'hA5) begin
                found_header = 1'b1;
                $display("[DBG TB - within pulse] artery_wr_data=%h uut.artery_wr_data=%h artery_wr_en=%b uut.artery_wr_en=%b", artery_wr_data, uut.artery_wr_data, artery_wr_en, uut.artery_wr_en);
            end
            i = i + 1;
        end
        inst_valid = 1'b0;
        // If header found, check fields
        if (found_header) begin
            $display("[TB] core emitted artery header: %h", artery_wr_data);
            if (artery_wr_data[55:48] != 8'd7) begin
                $display("[FAIL] Header mismatch: sel wrong"); errors = errors + 1;
            end else $display("[OK] POLY_STEP header detected by TB");
        end else begin
            $display("[FAIL] core did not emit valid artery header (artery_wr_data=%h)", artery_wr_data); errors = errors + 1;
        end

        // 2) Test RATIO_CMP: program acc values then issue RATIO_CMP cfg write (sel=7, material=1)
        // Directly poke internal accumulator registers for test convenience
        // (hierarchical access allowed in testbench)
        #10;
        rplu_u.acc_num_reg = 128'sd100; // p1
        rplu_u.acc_den_reg = 128'sd50;  // q1

        // prepare cfg data: {p2, q2} where p2=200, q2=50
        cfg_wr_data = {32'sd200, 32'sd50};
        // issue RATIO_CMP: sel=7, material=1
        cfg_wr_sel = 3'd7;
        cfg_wr_material = 1'b1;
        cfg_wr_addr = 10'd0;
        $display("[TB] Issuing RATIO_CMP cfg_wr_sel=%0d material=%b data=%h at time=%0t", cfg_wr_sel, cfg_wr_material, cfg_wr_data, $time);
        cfg_wr_en = 1'b1; #1; @(posedge clk); cfg_wr_en = 1'b0;
        $display("[TB] RATIO_CMP pulse complete at time=%0t", $time);
        @(posedge clk);

        // expect: compare p1/q1 = 100/50 = 2.0  vs p2/q2 = 200/50 = 4.0  => result = -1
        if (ratio_cmp_res !== -3'sd1) begin
            $display("[FAIL] RATIO_CMP returned %0d, expected -1", ratio_cmp_res); errors = errors + 1;
        end else begin
            $display("[OK] RATIO_CMP result = %0d as expected", ratio_cmp_res);
        end

        if (errors == 0) $display("[TB] POLY_STEP integration test: PASS"); else $display("[TB] POLY_STEP integration test: FAIL (%0d errors)", errors);
        $finish;
    end

endmodule
