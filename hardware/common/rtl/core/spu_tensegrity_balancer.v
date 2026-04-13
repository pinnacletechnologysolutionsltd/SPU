// SPU-13 Rational Field Tensegrity Balancer (v2.0)
// Implementation: Parallel reduction tree for 12-neighbor Laplacian relaxation.
// Field: Q(sqrt3), Logic: Algebraic Summation.
// Objective: Absolute equilibrium (Henosis) detection via Rational Field reduction.

module spu_tensegrity_balancer #(
    parameter THRESHOLD = 16'd4 // Threshold Floor
)(
    input  wire         clk,
    input  wire         reset,
    input  wire [3071:0] neighbors, 
    output wire [255:0] scaled_residual,
    output wire         at_equilibrium,
    // runtime config inputs (RPLU)
    input  wire         cfg_wr_en,
    input  wire [2:0]   cfg_wr_sel,
    input  wire         cfg_wr_material,
    input  wire [9:0]   cfg_wr_addr,
    input  wire [63:0]  cfg_wr_data
);

    genvar i;
    // per-lane threshold regs (signed 16-bit)
    reg signed [15:0] threshold_reg [0:7];
    generate
        for (i = 0; i < 8; i = i + 1) begin : lane_logic
            // Localized RationalSurd Summation: (a + b*sqrt3)
            // Each neighbor provides 16-bit 'a' and 'b' coefficients
            reg signed [15:0] a[0:11];
            reg signed [15:0] b[0:11];
            
            // Unpack neighbors
            integer j;
            always @(*) begin
                for (j = 0; j < 12; j = j + 1) begin
                    a[j] = neighbors[j*256 + i*32 +: 16];
                    b[j] = neighbors[j*256 + i*32 + 16 +: 16];
                end
            end
            
            // Exact Polynomial Summation (Parallel reduction tree)
            reg signed [31:0] sum_a, sum_b;
            integer k;
            always @(*) begin
                sum_a = 0; sum_b = 0;
                for (k = 0; k < 12; k = k + 1) begin
                    sum_a = sum_a + a[k];
                    sum_b = sum_b + b[k];
                end
            end
            
            // Boole-Wildberger Thresholding
            wire signed [31:0] th;
            assign th = {{16{threshold_reg[i][15]}}, threshold_reg[i]};
            wire valid;
            assign valid = (sum_a > th) | (sum_a < -th);
            
            assign scaled_residual[i*32 +: 16] = (valid ? sum_a[15:0] : 16'd0);
            assign scaled_residual[i*32 + 16 +: 16] = (valid ? sum_b[15:0] : 16'd0);
        end
    endgenerate

    // threshold register writeback via cfg interface
    integer t;
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            for (t = 0; t < 8; t = t + 1) threshold_reg[t] <= THRESHOLD;
        end else begin
            if (cfg_wr_en && (cfg_wr_sel == 3'd0)) begin
                threshold_reg[cfg_wr_addr[2:0]] <= $signed(cfg_wr_data[15:0]);
            end
        end
    end

    assign at_equilibrium = ~(|scaled_residual);

endmodule
