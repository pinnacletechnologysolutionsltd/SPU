`timescale 1ns / 1ps

module spu13_btu_core_top (
    input wire clk,
    input wire rst_n,
    input wire [63:0] neuron_activation_lines,        // Output To Phase-Lock and Multiplier Core (Phi3 Ingestion)
    output wire [31:0] btu_lane_c0, // Rational part
    output wire [31:0] btu_lane_c1, // sqrt(3) coefficient
    output wire [31:0] btu_lane_c2, // sqrt(5) coefficient
    output wire [31:0] btu_lane_c3, // sqrt(15) coefficient
    output wire        pipeline_stall,
    output wire        data_valid);

    wire [5:0] internal_k;
    wire       internal_valid;

    // --- Instantiate Stage 2 Priority Collision Resolver ---
    spu_btu_collision_resolver btu_hazard_unit (
        .clk(clk),
        .rst_n(rst_n),
        .neuron_activation_lines(neuron_activation_lines),
        .pipeline_stall(pipeline_stall),
        .selected_row_k(internal_k),
        .bus_valid(internal_valid)
    );

    // --- Instantiate Dual-Port BRAM Storage Grid (Hardwired F_p^4 Constants) ---
    // We break the 4 lanes out across unified block structures
    // Data paths utilize direct 32-bit register widths
    // Lane 0 ROM: Rational c0
    spu_bram_32x64_array lane0_rom (
        .clk(clk),
        .addr(internal_k),
        .data_out(btu_lane_c0)
    );

    // Lane 1 ROM: Radical c1 (sqrt(3))
    spu_bram_32x64_array lane1_rom (
        .clk(clk),
        .addr(internal_k),
        .data_out(btu_lane_c1)
    );

    // Lane 2 ROM: Radical c2 (sqrt(5))
    spu_bram_32x64_array lane2_rom (
        .clk(clk),
        .addr(internal_k),
        .data_out(btu_lane_c2)
    );

    // Lane 3 ROM: Radical c3 (sqrt(15))
    spu_bram_32x64_array lane3_rom (
        .clk(clk),
        .addr(internal_k),
        .data_out(btu_lane_c3)
    );

    // Pass valid indicator downstream to Phase-Lock Latch
    assign data_valid = internal_valid;

endmodule
