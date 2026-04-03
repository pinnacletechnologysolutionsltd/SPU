// SPU-13 Sovereign Core (v1.7 - Strictly Phi-Gated TDM)
// Objective: 13-axis Manifold via Fibonacci-Synchronized Pipeline.
// Architecture: TDM Davis Law Gasket + SQR Rotor Vault + Artery Interface.

`include "spu_arch_defines.vh"

module spu13_core #(
    parameter DEVICE = "GW2A"  // "GW1N" | "GW2A" | "GW5A" | "SIM"
)(
    input  wire         clk,            // Fast Clock (e.g. 12-24MHz)
    input  wire         rst_n,
    
    // Fibonacci Timing Pulses
    input  wire         phi_8,          // Fetch Pulse
    input  wire         phi_13,         // Compute Pulse
    input  wire         phi_21,         // Commit Pulse

    // Sovereign Memory Interface
    `MANIFOLD_SIGS,

    // 13-Axis Manifold Snapshot (for Artery TX)
    output wire [3:0]   current_axis_ptr,
    output wire [63:0]  current_axis_data,
    output reg [`MANIFOLD_WIDTH-1:0] manifold_out,
    output wire                      bloom_complete,
    output reg                       is_janus_point
);

    // 1. Manifold State Buffering
    reg [`MANIFOLD_WIDTH-1:0] manifold_reg;
    initial manifold_reg = 0;

    // 2. TDM Axis Pointer
    reg [3:0] axis_ptr;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) axis_ptr <= 0;
        else if (phi_21) begin
            axis_ptr <= (axis_ptr == 4'd12) ? 4'd0 : axis_ptr + 4'd1;
        end
    end

    assign current_axis_ptr = axis_ptr;
    assign current_axis_data = manifold_reg[axis_ptr*64 +: 64];

    // 3. Stage 1: Rotor & Axis Fetch (Pulse 8)
    wire [31:0] current_rotor;
    spu_rotor_vault u_vault (
        .clk(clk),
        .addr(axis_ptr),
        .rotor_out(current_rotor)
    );

    // Stage 2: The SQR Cross-Product (Pulse 13)
    wire [31:0] q_prime_ab;
    spu_cross_rotor u_rotor (
        .clk(clk),
        .reset(!rst_n),
        .q_axis(current_axis_data[63:32]), // {A, B}
        .r_rotor(current_rotor),
        .q_prime(q_prime_ab)
    );

    // Stage 3: Stability Check & Commit (Pulse 21)
    wire [63:0] rotated_axis = {q_prime_ab, current_axis_data[31:0]};
    wire [31:0] quadrance;
    wire [15:0] gasket_sum;
    
    davis_gate_dsp #(.DEVICE(DEVICE)) u_gate (
        .clk(clk),
        .rst_n(rst_n),
        .q_vector(rotated_axis),
        .q_rotated(),
        .quadrance(quadrance),
        .gasket_sum(gasket_sum)
    );

    wire [31:0] quadrance_err = (quadrance > 32'h0100_0000) ? (quadrance - 32'h0100_0000) : (32'h0100_0000 - quadrance);
    wire axis_stable = (quadrance_err <= 32'h0000_1000);


    reg [12:0] stability_bits;

    // Sovereign Hydration & State Logic
    reg [2:0] hydration_state;
    localparam H_IDLE   = 3'd0;
    localparam H_INHALE = 3'd1;
    localparam H_BLOOM  = 3'd2;
    localparam H_EXHALE = 3'd3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            hydration_state <= H_IDLE;
            mem_burst_rd <= 0; mem_burst_wr <= 0; mem_addr <= 0;
            manifold_out <= 0;
            stability_bits <= 13'h1FFF;
            is_janus_point <= 1'b1;
        end else begin
            case (hydration_state)
                H_IDLE: begin
                    if (phi_8 && mem_ready) begin
                        mem_burst_rd <= 1; mem_addr <= 24'h0;
                        hydration_state <= H_INHALE;
                    end
                end
                H_INHALE: begin
                    if (mem_burst_done) begin
                        mem_burst_rd <= 0;
                        manifold_reg <= mem_rd_manifold;
                        hydration_state <= H_BLOOM;
                    end
                end
                H_BLOOM: begin
                    // Commit current axis on Pulse 21
                    if (phi_21) begin
                        manifold_reg[axis_ptr*64 +: 64] <= rotated_axis;
                        stability_bits[axis_ptr] <= axis_stable;
                        
                        // If we just finished axis 12, move to Exhale
                        if (axis_ptr == 4'd12) begin
                            manifold_out <= manifold_reg;
                            is_janus_point <= &stability_bits;
                            mem_burst_wr <= 1;
                            mem_wr_manifold <= manifold_reg;
                            hydration_state <= H_EXHALE;
                        end
                    end
                end
                H_EXHALE: begin
                    if (mem_burst_done) begin
                        mem_burst_wr <= 0;
                        hydration_state <= H_IDLE;
                    end
                end
            endcase
        end
    end

    assign bloom_complete = (hydration_state == H_IDLE);

endmodule
