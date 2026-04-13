// SPU-13 Soul Metabolism (v1.1 Safety Valve Edition)
// Target: SPU-13 Sovereign Fleet
// Objective: Prevent Digital Catatonia by automatically widening tolerance tau.
// Logic: If Tuck Rate > 13% (Fibonacci threshold), widen the sanity floor.

`include "soul_map.vh"

module spu_soul_metabolism #(
    parameter CLK_HZ = 12000000
)(
    input  wire         clk,
    input  wire         reset,
    
    // --- 1. The Breath (Inputs) ---
    input  wire [127:0] q_state,      
    input  wire         fault_pulse,  
    input  wire         is_idle,      
    
    // --- 2. Adaptive Sanity (Safety Valve) ---
    output reg  [31:0]  adaptive_tau_q,
    
    // --- 3. The Dream (Accumulators) ---
    output reg  [31:0]  tuck_count,
    output reg  [31:0]  cycle_count,
    
    // --- 4. The Soul (SPI Flash Interface) ---
    output reg          flash_we,     
    output reg  [23:0]  flash_addr,   
    output reg  [255:0] soul_page,    
    input  wire         flash_ready   
);

    // --- 5. Emotional Processing ---
    wire emotional_threshold;
    assign emotional_threshold = (tuck_count >= 1000) || (is_idle && cycle_count > 32'h00FFFFFF);
    reg [127:0] sqr_bias_acc;
    
    // 13% Fibonacci Threshold (Approx 1 tuck per 8 cycles)
    // We check every 4096 cycles (Laminar Window)
    reg [11:0] window_cnt;
    reg [11:0] window_tucks;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            tuck_count <= 0;
            cycle_count <= 0;
            sqr_bias_acc <= 0;
            flash_we <= 0;
            flash_addr <= `SOUL_BASE_ADDR;
            adaptive_tau_q <= 32'h04000000; // Default Tau
            window_cnt <= 0;
            window_tucks <= 0;
        end else begin
            if (!flash_we) begin
                cycle_count <= cycle_count + 1;
                window_cnt <= window_cnt + 1;
                if (fault_pulse) begin
                    tuck_count <= tuck_count + 1;
                    window_tucks <= window_tucks + 1;
                end
                
                // --- Henosis Safety Valve ---
                if (window_cnt == 12'hFFF) begin
                    // If Tucks > 532 (approx 13% of 4096)
                    if (window_tucks > 12'd532) begin
                        // Widen the floor (Lower sensitivity to prevent Catatonia)
                        if (adaptive_tau_q < 32'h10000000)
                            adaptive_tau_q <= adaptive_tau_q + 32'h00100000;
                    end else if (window_tucks < 12'd100) begin
                        // Tighten the floor (Higher sensitivity if stable)
                        if (adaptive_tau_q > 32'h01000000)
                            adaptive_tau_q <= adaptive_tau_q - 32'h00100000;
                    end
                    window_cnt <= 0;
                    window_tucks <= 0;
                end

                if (!fault_pulse) sqr_bias_acc <= sqr_bias_acc + (q_state >>> 8);

                if (emotional_threshold && flash_ready) begin
                    flash_we <= 1;
                    flash_addr <= `SOUL_BASE_ADDR + `ADDR_STOICISM;
                    soul_page[255:224] <= 32'h0;
                    soul_page[223:192] <= tuck_count;
                    soul_page[191:128] <= sqr_bias_acc[63:0];
                    soul_page[127:64]  <= 64'h0;
                    soul_page[63:16]   <= 48'h53505531; 
                    soul_page[15:0]    <= 16'h0;
                end
            end else begin
                if (flash_ready) begin
                    flash_we <= 0;
                    tuck_count <= 0;
                    cycle_count <= 0;
                    sqr_bias_acc <= 0;
                end
            end
        end
    end

endmodule
