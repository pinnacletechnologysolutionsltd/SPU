// Injection Gate (skeleton)
// Maps PCM samples -> r_q16 targets and provides a smooth/handshaked output
// Notes: placeholder Padé smoothing implemented as simple averaging here.
module injection_gate(
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,           // start processing sample
    input  wire signed [15:0] pcm_in,    // signed 16-bit PCM sample
    input  wire         material_id,
    input  wire [9:0]   sector_addr,
    output reg  signed [31:0] r_q16_out, // Q16.16 representation (signed)
    output reg          valid_out       // asserted when r_q16_out is stable
);

    // Equilibrium (re) per material (read-only small ROM could be used)
    localparam signed [31:0] RE_STEEL = 32'sd65536; // 1.0 in Q16
    localparam signed [31:0] RE_AIR   = 32'sd65536; // placeholder

    // internal registers
    reg signed [31:0] target_r;   // stage capture
    reg signed [31:0] smooth_r;   // smoothing stage
    reg [1:0] state;

    // Simple rational normalizer: map signed 16-bit PCM -> small Q16 displacement
    // NOTE: replace scaling/normalization with proper mapping when material params known
    wire signed [31:0] pcm_q16 = { {16{pcm_in[15]}}, pcm_in }; // sign-extend to 32 bits (treat as Q16 for now)

    // Pade evaluator instance signals
    reg pade_start;
    wire pade_done;
    reg signed [63:0] pade_x; // Q32 input
    wire signed [31:0] pade_y; // Q16 output

    pade_eval_2_2 pade_u(.clk(clk), .rst_n(rst_n), .start(pade_start), .x_q32(pade_x), .y_q16(pade_y), .done(pade_done));

    // ROM-fallback: small per-material vnorm ROMs indexed by sector_addr (10-bit)
    parameter USE_ROM_FALLBACK = 1;
    reg signed [31:0] vnorm_carbon [0:1023];
    reg signed [31:0] vnorm_iron   [0:1023];
    initial begin
        // best-effort read; if files missing then contents stay zero and code falls back to pade
        $readmemh("hardware/common/rtl/gpu/vnorm_carbon.mem", vnorm_carbon);
        $readmemh("hardware/common/rtl/gpu/vnorm_iron.mem", vnorm_iron);
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            r_q16_out <= 0;
            target_r <= 0;
            smooth_r <= 0;
            valid_out <= 1'b0;
            state <= 2'b00;
            pade_start <= 1'b0;
            pade_x <= 0;
        end else begin
            valid_out <= 1'b0;
            pade_start <= 1'b0;
            case (state)
                2'b00: begin
                    if (start) begin
                        // capture and map PCM to target r (r = re + pcm_scaled)
                        if (material_id == 1'b0) target_r <= RE_STEEL + pcm_q16; else target_r <= RE_AIR + pcm_q16;
                        state <= 2'b01;
                    end
                end
                2'b01: begin
                    if (USE_ROM_FALLBACK) begin
                        // Use sector_addr to index precomputed normalized V for chosen material.
                        if (material_id == 1'b0) begin
                            smooth_r <= vnorm_carbon[sector_addr];
                        end else begin
                            smooth_r <= vnorm_iron[sector_addr];
                        end
                        $display("INJ: ROM fallback read time=%0t sector=%0d val=%0d", $time, sector_addr, smooth_r);
                        state <= 2'b11; // skip pade
                    end else begin
                        // start Padé smoothing: pass delta or target as Q32 input
                        // scale target_r (Q16) to Q32 for evaluator
                        pade_x <= {target_r, 16'd0}; // promote Q16->Q32 by shifting left 16
                        pade_start <= 1'b1;
                        $display("INJ: start pade time=%0t target_r=%0d", $time, target_r);
                        state <= 2'b10;
                    end
                end
                2'b10: begin
                    // wait for pade to complete
                    if (pade_done) begin
                        $display("INJ: pade_done time=%0t y=%0d", $time, pade_y);
                        // accept pade output as next smooth value
                        smooth_r <= pade_y;
                        state <= 2'b11;
                    end
                end
                2'b11: begin
                    // output stage
                    r_q16_out <= smooth_r;
                    valid_out <= 1'b1;
                    $display("INJ: output time=%0t r_q16_out=%0d", $time, smooth_r);
                    state <= 2'b00;
                end
            endcase
        end
    end
endmodule
