// spu_proprioception.v (v1.0 - Cognitive Layer)
// ------------------------------------------------------------------
// Role: Rational Proprioception Monitor
//       watches the "sensors" (Davis Gates) and determines if the 
//       machine is in a stable Phinary state (Laminar Flow).
// ------------------------------------------------------------------

module spu_proprioception (
    input  wire                    clk,
    input  wire                    rst_n,

    // Sensor inputs from a single Davis Gate (TDM stream)
    input  wire [15:0]             gasket_sum,
    input  wire [31:0]             quadrance,
    input  wire                    pulse_commit, // phi_21 (end of current axis calc)
    input  wire                    cycle_wrap,   // axis_ptr wrap (end of manifold)
    input  wire                    rplu_dissoc,  // From RPLU engine

    // Health metrics
    output reg [15:0]              laminar_index,  // 0xFFFF = perfect balance
    output wire                    turbulence_alert // High if math is drifting
);

    // 1. Dissonance Accumulation
    reg [19:0] dissonance_acc; // Room for 13 axes 
    reg [15:0] last_total_dissonance;
    reg        any_dissoc;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dissonance_acc <= 20'h0;
            last_total_dissonance <= 16'h0;
            any_dissoc <= 1'b0;
        end else if (pulse_commit) begin
            // Accumulate absolute gasket sum
            if (gasket_sum[15])
                dissonance_acc <= dissonance_acc + (~gasket_sum + 1);
            else
                dissonance_acc <= dissonance_acc + gasket_sum;
            
            any_dissoc <= any_dissoc | rplu_dissoc;

            // On manifold wrap, latch the total and reset
            if (cycle_wrap) begin
                last_total_dissonance <= (dissonance_acc[19:16] == 0) ? dissonance_acc[15:0] : 16'hFFFF;
                dissonance_acc <= 20'h0;
                any_dissoc <= 1'b0;
            end
        end
    end

    // 2. Laminar Flow Index (LFI)
    reg [23:0] lfi_acc;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            lfi_acc <= 24'hFFFFFF;
            laminar_index <= 16'hFFFF;
        end else if (pulse_commit && cycle_wrap) begin
            // If dissociation occurred, LFI crashes to zero (or near-zero)
            // Otherwise, leak towards (0xFFFF - last_total_dissonance)
            if (any_dissoc)
                lfi_acc <= lfi_acc - (lfi_acc >> 2); // Fast crash
            else
                lfi_acc <= lfi_acc - (lfi_acc >> 4) + ((16'hFFFF - last_total_dissonance) << 4);
            
            laminar_index <= lfi_acc[23:8];
        end
    end

    // 3. Turbulence Alert
    parameter TURBULENCE_THRESHOLD = 16'h0200;
    assign turbulence_alert = (last_total_dissonance > TURBULENCE_THRESHOLD) | any_dissoc;

endmodule
