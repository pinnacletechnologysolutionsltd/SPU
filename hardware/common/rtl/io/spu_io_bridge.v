// SPU-13 I/O Bridge: Liquid Edition (v3.4.27)
// Implementation: Laminar Frame Protocol (Draft 1.2) with Dielectric Reservoir.
// Objective: Dual-layer I/O with Smoothed Metabolic Telemetry.

module spu_io_bridge #(
    parameter CLK_PHYS_HZ = 12000000
)(
    input  wire         clk_phys,
    input  wire         clk_resonant,
    input  wire         reset,
    
    // SPU Interface
    input  wire [831:0] spu_reg_in,
    input  wire [15:0]  microwatts,
    input  wire [7:0]   laminar_flow_index, 
    input  wire         sip_active,
    output wire [127:0] strike_ripple,
    input  wire         fault_detected,
    input  wire         coherence_lock,
    
    // Physical IO
    output wire [3:0]   led_status,
    output wire [7:0]   pmod_ja_out,
    input  wire [3:0]   sw_control,
    input  wire         serial_rx,
    output wire         serial_tx
);

    // 1. Laminar Buffer (Dielectric Reservoir)
    // Smoothes the metabolic signal to provide a true 'Sip' average.
    wire [15:0] smoothed_uw;
    wire        reservoir_full;
    spu_laminar_buffer u_buffer (
        .clk(clk_phys), .reset(reset),
        .microwatts_in(microwatts),
        .microwatts_out(smoothed_uw),
        .reservoir_full(reservoir_full)
    );

    // 2. The Laminar Frame Assembler (Telemetry)
    wire signed [31:0] a = spu_reg_in[31:0];
    wire signed [31:0] b = spu_reg_in[63:32];
    wire signed [31:0] c = spu_reg_in[95:64];
    wire signed [31:0] d = spu_reg_in[127:96];
    
    wire symmetry_ok = ((a + b + c + d) == 32'sd0);
    wire [31:0] payload = spu_reg_in[31:0];
    wire [6:0] status_flags = {4'b0, reservoir_full, sip_active, coherence_lock};

    // 3. Telemetry Path (TX)
    surd_uart_tx #(
        .CLK_HZ(CLK_PHYS_HZ),
        .BAUD(115200)
    ) u_telemetry (
        .clk(clk_phys),
        .reset(reset),
        .data_in({symmetry_ok, smoothed_uw, laminar_flow_index, status_flags, payload}), 
        .start(|spu_reg_in[31:0]), 
        .tx(serial_tx),
        .ready()
    );

    // 4. Interaction Path (RX)
    wire [7:0] rx_data;
    wire       rx_valid;
    assign rx_valid = !serial_rx; 
    assign rx_data  = 8'h41;      

    spu_harmonic_transducer u_membrane (
        .clk(clk_resonant),
        .reset(reset),
        .ascii_in(rx_data),
        .data_valid(rx_valid),
        .ripple_out(strike_ripple),
        .membrane_lock()
    );

    // 5. Status Reification
    assign led_status[0] = fault_detected;
    assign led_status[1] = (laminar_flow_index < 8'h80); 
    assign led_status[2] = clk_resonant;
    assign led_status[3] = coherence_lock & reservoir_full;  

    assign pmod_ja_out = spu_reg_in[7:0];

endmodule
