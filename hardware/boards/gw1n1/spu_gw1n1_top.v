// spu_gw1n1_top.v (v1.0 - Whisper Beacon)
// Target: GW1N-1 / GW1NZ-1 (Tang Nano 1K — 1,152 LUT4, 0 DSP, 72KB BSRAM)
//
// Tier 1 Micro deployment. No PSRAM — seeds from 256-word BSRAM.
// Core: spu_4_euclidean_alu (bit-serial multiply, 0 DSPs, ~499 LUT).
// Output: Artery Whisper TX on GPIO as a pure resonance beacon.
//
// Total budget: ~601 LUT — 52% of GW1N-1.

`include "spu_arch_defines.vh"
`include "sqr_params.vh"

module spu_gw1n1_top (
    input  wire clk,                // 27 MHz onboard oscillator

    // Onboard LEDs (active-low on Tang Nano 1K)
    output wire LED_R,
    output wire LED_G,
    output wire LED_B,

    // UART TX — Whisper telemetry via USB-UART bridge
    output wire uart_tx,

    // Artery nerve output (PMOD / GPIO) for RP2040 inhalation
    output wire NERVE_MOSI
);

    // --- 1. Phi-Gated Clock ---
    wire phi_8, phi_13, phi_21, phi_heart;
    spu_sierpinski_clk u_phi (
        .clk(clk),
        .rst_n(1'b1),
        .phi_8(phi_8),
        .phi_13(phi_13),
        .phi_21(phi_21),
        .heartbeat(phi_heart)
    );

    // --- 2. Seed BRAM (256 × 16-bit, initialised from spu_init.mem) ---
    // Addresses [0..3] = initial Quadray (A, B, C, D).
    // Addresses [4..6] = rotor coefficients (F, G, H) for 60° IVM rotation.
    reg [15:0] seed_rom [0:7];
    initial $readmemh("spu_init.mem", seed_rom, 0, 7);

    // Fixed IVM 60° SQR rotor coefficients
    wire signed [15:0] F = `SQR_60_F;
    wire signed [15:0] G = `SQR_60_G;
    wire signed [15:0] H = `SQR_60_H;

    // --- 3. Euclidean ALU (bit-serial, 0 DSPs) ---
    // Runs in autonomous mode — self-iterates from boot.
    wire [15:0] A_out, B_out, C_out, D_out;
    wire        alu_done, henosis_pulse;
    reg         alu_start;
    reg         seeded;

    spu_4_euclidean_alu u_alu (
        .clk(clk),
        .reset(1'b0),
        .start(alu_start),
        .bloom_intensity(8'hFF),      // Full intensity
        .mode_autonomous(seeded),     // Slave on first beat, autonomous after
        .A_in(seed_rom[0]),
        .B_in(seed_rom[1]),
        .C_in(seed_rom[2]),
        .D_in(seed_rom[3]),
        .F(F), .G(G), .H(H),
        .A_out(A_out), .B_out(B_out),
        .C_out(C_out), .D_out(D_out),
        .done(alu_done),
        .henosis_pulse(henosis_pulse)
    );

    // Drive the ALU from the Phi heartbeat; latch seeded after first completion
    always @(posedge clk) begin
        alu_start <= 1'b0;
        if (phi_heart && !alu_start)
            alu_start <= 1'b1;
        if (alu_done && !seeded)
            seeded <= 1'b1;
    end

    // --- 4. Artery TX (Whisper protocol) ---
    spu_artery_tx u_artery (
        .clk(clk),
        .phi_21(phi_21),
        .axis_ptr(4'd0),
        .axis_data({A_out, B_out, C_out, D_out}),
        .tx_out(NERVE_MOSI),
        .tx_active()
    );

    // --- 5. Status LEDs (active-low) ---
    assign LED_B = seeded;          // Blue on  = booting/unseeded
    assign LED_G = !alu_done;       // Green off = ALU running
    assign LED_R = !henosis_pulse;  // Red on   = Henosis drift event

    assign uart_tx = NERVE_MOSI;    // Mirror Whisper on UART for host capture

    // Suppress unused warning on phi signals (used indirectly via artery)
    wire _unused = phi_8 ^ phi_13;

endmodule
