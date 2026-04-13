// SPU-13 Metabolic Sense (v3.3.99)
// Implementation: Real-time Power Monitoring via Shunt ADC.
// Objective: Measure the 'Sip' metabolic rate at the uW level.
// Result: Self-aware power signature for frequency regulation.

module spu_metabolic_sense (
    input  wire        clk,
    input  wire        reset,
    input  wire [11:0] adc_raw,      // Raw data from Shunt Resistor
    output reg  [15:0] microwatts,   // Calculated Power (uW)
    output wire        sip_active    // High if power < threshold
);

    // Metabolic Calculation: Power = Voltage * Current
    // Assumes 1.2V VCCINT. P = 1.2 * (I_shunt).
    // Scaling: (adc_raw << 1) + (adc_raw >> 1) provides a rational approximation 
    // of the 1.2x voltage multiplier in bit-locked arithmetic.
    
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            microwatts <= 16'h0;
        end else begin
            microwatts <= (adc_raw << 1) + (adc_raw >> 1);
        end
    end

    // The 'Sip' threshold: Certified Laminar if < 100uW
    assign sip_active = (microwatts < 16'd100);

endmodule
