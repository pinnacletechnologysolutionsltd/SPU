// SB_HFOSC simulation stub (iCE40 internal HF oscillator).
// Outputs a 48 MHz clock with CLKHF_DIV divisor support.
// Only for RTL simulation — not for synthesis.

module SB_HFOSC #(
    parameter CLKHF_DIV = "0b00"  // "0b00"=48M, "0b01"=24M, "0b10"=12M, "0b11"=6M
)(
    input  wire CLKHFEN,
    input  wire CLKHFPU,
    output reg  CLKHF
);
    // Divide selector: default 48 MHz → 10.4 ns half-period (1ns timescale)
    real HALF_PERIOD;
    initial begin
        case (CLKHF_DIV)
            "0b00": HALF_PERIOD = 10.4;
            "0b01": HALF_PERIOD = 20.8;
            "0b10": HALF_PERIOD = 41.7;
            "0b11": HALF_PERIOD = 83.3;
            default: HALF_PERIOD = 41.7; // 12 MHz default
        endcase
        CLKHF = 0;
    end

    always begin
        #(HALF_PERIOD) CLKHF = ~CLKHF;
    end
endmodule
