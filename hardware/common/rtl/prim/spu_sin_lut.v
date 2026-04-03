// SPU-13 Rational Sine LUT (v1.0)
// Objective: Standard 256-entry quadrant LUT for 60-degree resonance.
// Range: 0 to 255 (0 to 360 degrees), Result shifted to 12-bit signed.

module spu_sin_lut (
    input  wire [7:0]  phase,
    output reg  signed [11:0] sin_out
);
    // 64-entry quadrant (0 to 90 degrees)
    // Values scaled to 2047 (max 12-bit signed positive)
    reg [10:0] lut [0:63];
    initial begin
        lut[0] = 0;    lut[1] = 50;   lut[2] = 100;  lut[3] = 150;
        lut[4] = 200;  lut[5] = 250;  lut[6] = 300;  lut[7] = 349;
        lut[8] = 399;  lut[9] = 448;  lut[10] = 497; lut[11] = 546;
        lut[12] = 595; lut[13] = 643; lut[14] = 690; lut[15] = 738;
        lut[16] = 784; lut[17] = 831; lut[18] = 877; lut[19] = 922;
        lut[20] = 967; lut[21] = 1012; lut[22] = 1056; lut[23] = 1099;
        lut[24] = 1142; lut[25] = 1184; lut[26] = 1226; lut[27] = 1267;
        lut[28] = 1307; lut[29] = 1347; lut[30] = 1386; lut[31] = 1425;
        lut[32] = 1463; lut[33] = 1500; lut[34] = 1536; lut[35] = 1572;
        lut[36] = 1607; lut[37] = 1641; lut[38] = 1675; lut[39] = 1708;
        lut[40] = 1740; lut[41] = 1772; lut[42] = 1802; lut[43] = 1832;
        lut[44] = 1861; lut[45] = 1889; lut[46] = 1916; lut[47] = 1942;
        lut[48] = 1968; lut[49] = 1993; lut[50] = 1017; lut[51] = 2039;
        lut[52] = 2061; lut[53] = 2082; lut[54] = 2102; lut[55] = 2120;
        lut[56] = 2138; lut[57] = 2154; lut[58] = 2170; lut[59] = 2184;
        lut[60] = 2197; lut[61] = 2209; lut[62] = 2220; lut[63] = 2230;
    end

    wire [5:0] index = phase[5:0];
    wire [1:0] quadrant = phase[7:6];

    always @(*) begin
        case (quadrant)
            2'b00: sin_out = $signed({1'b0, lut[index]});             // 0-90
            2'b01: sin_out = $signed({1'b0, lut[63-index]});          // 90-180
            2'b10: sin_out = -$signed({1'b0, lut[index]});            // 180-270
            2'b11: sin_out = -$signed({1'b0, lut[63-index]});         // 270-360
        endcase
    end
endmodule
