// SPU-13 Fractal Compressor (v1.0)
// Target: iCE40UP5K (Big Brother Cortex)
// Objective: Recursive memory management via Phi-Sampling and Evaporation.
// Method: Natural forgetting of noise to preserve Macro-Attractors.

module spu_fractal_compressor (
    input  wire         clk,
    input  wire         reset,
    input  wire [15:0]  current_tension,
    input  wire         is_idle,         // High when K is low
    output reg          log_req,         // Pulse to Dream Log
    output reg  [15:0]  fractal_data,    // Compressed state to store
    
    // Background Metabolism (Evaporation)
    output reg          evap_we,
    output reg  [15:0]  evap_addr,
    input  wire [15:0]  evap_data_in,
    output wire [15:0]  evap_data_out
);

    // --- 1. Phi-Sampling (Fibonacci Timer) ---
    // We approximate the golden ratio pulse by shifting the sampling rate
    reg [23:0] timer;
    reg [4:0]  phi_step;
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            timer <= 0;
            phi_step <= 5'd1;
        end else begin
            timer <= timer + 1;
            // Sampling interval expands/contracts according to phi_step
            if (timer[phi_step +: 1]) begin
                timer <= 0;
                phi_step <= (phi_step == 5'd20) ? 5'd8 : phi_step + 1;
            end
        end
    end

    // --- 2. Attractor Detection ---
    reg [15:0] last_attractor;
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            last_attractor <= 0;
            log_req <= 0;
            fractal_data <= 0;
        end else begin
            log_req <= 0;
            // Only log if change exceeds the 'Laminar Threshold'
            if (current_tension > (last_attractor + 16'h0100) || 
                current_tension < (last_attractor - 16'h0100)) begin
                log_req <= 1;
                fractal_data <= current_tension;
                last_attractor <= current_tension;
            end
        end
    end

    // --- 3. Natural Evaporation (Background Metabolism) ---
    // When idle, we slowly 'decay' the values in SPRAM
    reg [15:0] scan_ptr;
    assign evap_data_out = evap_data_in - (evap_data_in >>> 6); // 1.5% evaporation

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            scan_ptr <= 0;
            evap_we <= 0;
            evap_addr <= 0;
        end else if (is_idle) begin
            // Slow scan through memory to reduce tension peaks
            evap_addr <= scan_ptr;
            evap_we <= timer[10]; // Very slow evaporation rate
            if (timer[10]) scan_ptr <= scan_ptr + 1;
        end else begin
            evap_we <= 0;
        end
    end

endmodule
