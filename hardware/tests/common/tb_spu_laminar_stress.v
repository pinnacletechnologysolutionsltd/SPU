// tb_spu_laminar_stress.v (Phase 3 - Validation)
// ------------------------------------------------------------------
// Role: Stress testing the Proprioception and Dynamic Gasket logic.
//       Verifies that the SPU can "feel" a mathematical singularity.
// ------------------------------------------------------------------

`timescale 1ns/1ps
`include "spu_arch_defines.vh"

module tb_spu_laminar_stress;

    reg clk;
    reg rst_n;
    
    // Core timing pulses
    reg phi_8;
    reg phi_13;
    reg phi_21;

    // Manifold inputs (forced for test)
    reg  [63:0] test_axis_data;
    
    // Health Monitor outputs
    wire [15:0] lfi;
    wire        turbulence;
    wire        is_janus;

    // SPU-13 core instance (TDM mode)
    // We'll skip the SDRAM interface and force rotation data
    wire [15:0] gasket_sum;
    wire [31:0] quadrance;
    wire        cycle_wrap;
    wire        rplu_dissoc;

    spu13_core #(.DEVICE("SIM")) dut (
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
        .phinary_cfg(16'd0),
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
        .mem_rd_manifold(832'h0), // default to zero
        .mem_burst_done(1'b0),
        .is_janus_point(is_janus),
        .gasket_sum_out(gasket_sum),
        .quadrance_out(quadrance),
        .cycle_wrap(cycle_wrap),
        .rplu_dissoc_out(rplu_dissoc),
        .rplu_dissoc_mask_out()
    );

    // Rational Proprioception instance
    spu_proprioception u_proprio (
        .clk(clk),
        .rst_n(rst_n),
        .gasket_sum(gasket_sum),
        .quadrance(quadrance),
        .pulse_commit(phi_21),
        .cycle_wrap(cycle_wrap),
        .rplu_dissoc(rplu_dissoc),
        .laminar_index(lfi),
        .turbulence_alert(turbulence)
    );

    // 25 MHz clock
    always #20 clk = ~clk;

    // Sequence pulses (simulating the sovereign cycle)
    integer cycle_cnt = 0;
    always @(posedge clk) begin
        phi_8  <= (cycle_cnt == 0);
        phi_13 <= (cycle_cnt == 5);
        phi_21 <= (cycle_cnt == 10);
        
        if (cycle_cnt == 20) cycle_cnt <= 0;
        else cycle_cnt <= cycle_cnt + 1;
    end

    initial begin
        $display("--- SPU LAMINAR STRESS TEST START ---");
        clk = 0;
        rst_n = 0;
        #200;
        rst_n = 1;

        // --- Test 1: Cold Boot Stability ---
        // Manifold is zero. RPLU should be stable (Janus point).
        repeat(50) @(posedge cycle_wrap);
        $display("Boot LFI: 0x%h, Turbulence: %b", lfi, turbulence);
        if (lfi < 16'hF000) $display("FAIL: Unstable on cold boot");
        else $display("PASS: Stable cold boot");

        // --- Test 2: Turbulence Injection ---
        // We inject a "Singularity" value (A=Large, B=0, C=0, D=0)
        // This should cause high quadrance and RPLU dissociation
        $display("Injecting Mathematical Singularity...");
        force dut.manifold_lane[0] = {32'hFFFF_0000, 32'h0000_0000};

        repeat(20) @(posedge cycle_wrap);
        $display("Turbulence LFI: 0x%h, Turbulence: %b, Dissoc: %b", lfi, turbulence, rplu_dissoc);
        if (turbulence == 1'b1 && lfi < 16'h8000) $display("PASS: Turbulence detected");
        else $display("FAIL: Missed turbulence detection");

        // --- Test 3: Recovery (The Symmetry Breath) ---
        // Inject a known stable seed (A=1, B=1, C=1, D=1)
        $display("Injecting Symmetry Breath...");
        release dut.manifold_lane[0]; // stop forcing bad value
        force dut.manifold_lane[0] = {32'h0001_0001, 32'h0001_0001};
        
        repeat(50) @(posedge cycle_wrap);
        $display("Recovery LFI: 0x%h, Turbulence: %b", lfi, turbulence);
        if (lfi > 16'hF000 && turbulence == 0) $display("PASS: Manifold recovered");
        else $display("FAIL: Manifold failed to stabilize");

        $display("--- SPU LAMINAR STRESS TEST COMPLETE ---");
        $finish;
    end

endmodule
