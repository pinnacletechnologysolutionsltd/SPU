// SPU-13 Dream Log (v1.1 Fractal Edition)
// Target: iCE40UP5K (Big Brother Cortex)
// Objective: Long-term Sanity History via Fractal Compression.
// Logic: Integrated Evaporation and Phi-Sampling.

module spu_dream_log (
    input  wire         clk,
    input  wire         reset,
    input  wire [15:0]  current_tension, 
    input  wire         is_idle,
    output reg  [31:0]  learned_tau_q,   
    output wire [15:0]  history_data,    
    input  wire [15:0]  playback_addr
);

    // --- 1. The Fractal Compressor ---
    wire log_req;
    wire [15:0] fractal_data;
    wire evap_we;
    wire [15:0] evap_addr;
    wire [15:0] evap_data_out;
    wire [15:0] spram_data_out;

    spu_fractal_compressor u_compressor (
        .clk(clk), .reset(reset),
        .current_tension(current_tension),
        .is_idle(is_idle),
        .log_req(log_req),
        .fractal_data(fractal_data),
        .evap_we(evap_we),
        .evap_addr(evap_addr),
        .evap_data_in(spram_data_out),
        .evap_data_out(evap_data_out)
    );

    // --- 2. The Standing Wave Buffer (128KB SPRAM) ---
    reg [15:0] write_ptr;
    
    // Mux for Write Port: Logging vs Evaporation
    wire ram_we = log_req | evap_we;
    wire [15:0] ram_addr = log_req ? write_ptr : (evap_we ? evap_addr : playback_addr);
    wire [15:0] ram_din  = log_req ? fractal_data : evap_data_out;

    spu_gram_controller u_spram (
        .clk(clk), .reset(reset),
        .addr(ram_addr),
        .data_in(ram_din),
        .write_en(ram_we),
        .data_out(spram_data_out),
        .ready()
    );
    assign history_data = spram_data_out;

    // --- 3. Adaptive Sanity Logic ---
    reg [23:0] tension_sum;
    reg [7:0]  trend_cnt;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            write_ptr <= 0;
            tension_sum <= 0;
            trend_cnt <= 0;
            learned_tau_q <= 32'h04000000;
        end else if (log_req) begin
            write_ptr <= write_ptr + 1;
            tension_sum <= tension_sum + fractal_data;
            trend_cnt <= trend_cnt + 1;
            
            if (trend_cnt == 255) begin
                if (tension_sum[23:8] > 16'h4000) 
                    learned_tau_q <= learned_tau_q + 32'h00100000;
                else if (learned_tau_q > 32'h01000000)
                    learned_tau_q <= learned_tau_q - 32'h00100000;
                tension_sum <= 0;
                trend_cnt <= 0;
            end
        end
    end

endmodule
