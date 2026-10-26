`timescale 1ns / 1ps

// spu13_nsa_core.v — NSA Dual-Number Compute Block for RPLU v2 Pipeline
//
// Dedicated NSA arithmetic unit instantiated inside the ENABLE_CORE_RPLU_V2
// generate block. Contains:
//   - 2-slot NSA register bank (each slot = 1 dual number = real + eps, 8 × 32-bit)
//   - NSA dual ALU (add + multiply over A_SPU = A31[epsilon]/(epsilon^2))
//   - Own M31 multiplier instance
//   - Load/store/compute control FSM
//
// Opcodes:
// External ISA opcodes:
//   NSA_DQADD (0x4C): R[dest] = R[srcA] + R[srcB]  — dual addition
//   NSA_DQMUL (0x4D): R[dest] = R[srcA] * R[srcB]  — dual multiplication
//
// Internal nsa_op modes 2'b10 and 2'b11 are load/store micro-ops for local
// tests and future decode glue; they are not assigned external ISA opcodes.
//
// Register layout (2 dual-number slots, 16 × 32-bit registers):
//   Slot 0 real: reg[0..3], Slot 0 eps: reg[4..7]
//   Slot 1 real: reg[8..11], Slot 1 eps: reg[12..15]

module spu13_nsa_core #(
    parameter NUM_NSA_SLOTS = 2  // 2 dual numbers = 16 × 32-bit registers
) (
    input  wire         clk,
    input  wire         rst_n,

    // ── ISA interface ───────────────────────────────────────────────
    input  wire         nsa_start,          // Opcode trigger from decoder
    input  wire [1:0]   nsa_op,             // 00=DQADD, 01=DQMUL, 10=LOAD, 11=STORE
    input  wire [3:0]   nsa_dest,           // Destination slot (0-1) or QR addr
    input  wire [3:0]   nsa_srcA,           // Source A slot (0-1)
    input  wire [3:0]   nsa_srcB,           // Source B slot (0-1)
    output wire         nsa_done,           // Operation complete
    output wire         nsa_busy,           // Operation in progress

    // ── QR regfile interface (for NSA_LOAD/NSA_STORE) ───────────────
    // NSA_LOAD: read from QR regfile lane → NSA bank slot
    // NSA_STORE: write NSA bank slot → QR regfile lane
    input  wire [143:0] qr_features_in,     // 4 × 36-bit RationalSurd from QR regfile
    output reg  [143:0] nsa_features_out,   // NSA result → QR regfile writeback
    output reg          nsa_wr_en,           // Writeback strobe
    output reg  [3:0]   nsa_wr_addr,        // QR regfile write address

    // ── NSA dual ALU output (for downstream pipeline consumption) ───
    output wire [31:0]  nsa_real_z0, nsa_real_z1, nsa_real_z2, nsa_real_z3,
    output wire [31:0]  nsa_eps_z0,  nsa_eps_z1,  nsa_eps_z2,  nsa_eps_z3,
    output wire         nsa_result_valid     // Pulsed when result is ready
);

    localparam P = 32'h7FFFFFFF;

    // ── NSA Register Bank (2 slots × 8 × 32-bit = 16 registers) ─────
    reg [31:0] nsa_regs [0:15];
    integer i;

    // ── NSA dual ALU interface ───────────────────────────────────────
    reg         alu_start;
    reg         alu_op_mul;
    reg  [31:0] alu_a_real_z0, alu_a_real_z1, alu_a_real_z2, alu_a_real_z3;
    reg  [31:0] alu_a_eps_z0,  alu_a_eps_z1,  alu_a_eps_z2,  alu_a_eps_z3;
    reg  [31:0] alu_b_real_z0, alu_b_real_z1, alu_b_real_z2, alu_b_real_z3;
    reg  [31:0] alu_b_eps_z0,  alu_b_eps_z1,  alu_b_eps_z2,  alu_b_eps_z3;
    wire [31:0] alu_r_real_z0, alu_r_real_z1, alu_r_real_z2, alu_r_real_z3;
    wire [31:0] alu_r_eps_z0,  alu_r_eps_z1,  alu_r_eps_z2,  alu_r_eps_z3;
    wire        alu_done, alu_busy;

    // M31 multiplier interface
    wire        mult_start;
    wire [31:0] mult_a0, mult_a1, mult_a2, mult_a3;
    wire [31:0] mult_b0, mult_b1, mult_b2, mult_b3;
    wire [31:0] mult_r0, mult_r1, mult_r2, mult_r3;
    wire        mult_done, mult_busy;

    spu13_nsa_dual_alu u_alu (
        .clk(clk), .rst_n(rst_n), .start(alu_start), .op_mul(alu_op_mul),
        .a_real_z0(alu_a_real_z0), .a_real_z1(alu_a_real_z1),
        .a_real_z2(alu_a_real_z2), .a_real_z3(alu_a_real_z3),
        .a_eps_z0(alu_a_eps_z0),   .a_eps_z1(alu_a_eps_z1),
        .a_eps_z2(alu_a_eps_z2),   .a_eps_z3(alu_a_eps_z3),
        .b_real_z0(alu_b_real_z0), .b_real_z1(alu_b_real_z1),
        .b_real_z2(alu_b_real_z2), .b_real_z3(alu_b_real_z3),
        .b_eps_z0(alu_b_eps_z0),   .b_eps_z1(alu_b_eps_z1),
        .b_eps_z2(alu_b_eps_z2),   .b_eps_z3(alu_b_eps_z3),
        .r_real_z0(alu_r_real_z0), .r_real_z1(alu_r_real_z1),
        .r_real_z2(alu_r_real_z2), .r_real_z3(alu_r_real_z3),
        .r_eps_z0(alu_r_eps_z0),   .r_eps_z1(alu_r_eps_z1),
        .r_eps_z2(alu_r_eps_z2),   .r_eps_z3(alu_r_eps_z3),
        .done(alu_done), .busy(alu_busy),
        .mult_start(mult_start),
        .mult_a0(mult_a0), .mult_a1(mult_a1), .mult_a2(mult_a2), .mult_a3(mult_a3),
        .mult_b0(mult_b0), .mult_b1(mult_b1), .mult_b2(mult_b2), .mult_b3(mult_b3),
        .mult_r0(mult_r0), .mult_r1(mult_r1), .mult_r2(mult_r2), .mult_r3(mult_r3),
        .mult_done(mult_done), .mult_busy(mult_busy)
    );

    spu13_m31_multiplier u_mult (
        .clk(clk), .rst_n(rst_n), .start(mult_start),
        .a0(mult_a0), .a1(mult_a1), .a2(mult_a2), .a3(mult_a3),
        .b0(mult_b0), .b1(mult_b1), .b2(mult_b2), .b3(mult_b3),
        .r0(mult_r0), .r1(mult_r1), .r2(mult_r2), .r3(mult_r3),
        .done(mult_done), .busy(mult_busy)
    );

    // ── Control FSM ──────────────────────────────────────────────────
    localparam NSA_IDLE       = 3'd0;
    localparam NSA_LOAD_SLOT  = 3'd1;   // Load from QR regfile into NSA bank
    localparam NSA_COMPUTE    = 3'd2;   // ALU operation in progress
    localparam NSA_COMPUTE_WAIT = 3'd3; // Wait for ALU done
    localparam NSA_STORE_SLOT = 3'd4;   // Store NSA result to QR regfile
    localparam NSA_DONE_CYCLE = 3'd5;

    reg [2:0] nsa_state;

    // Slot-to-register address mapping: slot n → reg[8n:8n+7]
    wire [3:0] slot_real_base = {nsa_srcA[0], 3'b000};  // slot * 8
    wire [3:0] slot_eps_base  = {nsa_srcA[0], 3'b100};  // slot * 8 + 4
    wire [3:0] dest_real_base = {nsa_dest[0], 3'b000};

    assign nsa_done = (nsa_state == NSA_DONE_CYCLE);
    assign nsa_busy = (nsa_state != NSA_IDLE) && (nsa_state != NSA_DONE_CYCLE);

    // ── NSA result output (live during DONE_CYCLE) ───────────────────
    assign nsa_result_valid = (nsa_state == NSA_DONE_CYCLE);
    assign nsa_real_z0 = nsa_regs[dest_real_base + 4'd0];
    assign nsa_real_z1 = nsa_regs[dest_real_base + 4'd1];
    assign nsa_real_z2 = nsa_regs[dest_real_base + 4'd2];
    assign nsa_real_z3 = nsa_regs[dest_real_base + 4'd3];
    assign nsa_eps_z0  = nsa_regs[dest_real_base + 4'd4];
    assign nsa_eps_z1  = nsa_regs[dest_real_base + 4'd5];
    assign nsa_eps_z2  = nsa_regs[dest_real_base + 4'd6];
    assign nsa_eps_z3  = nsa_regs[dest_real_base + 4'd7];

    // ── Main FSM ─────────────────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 16; i = i + 1)
                nsa_regs[i] <= 32'd0;
            nsa_state      <= NSA_IDLE;
            alu_start      <= 1'b0;
            alu_op_mul     <= 1'b0;
            nsa_wr_en      <= 1'b0;
            nsa_features_out <= 144'd0;
            nsa_wr_addr    <= 4'd0;
        end else begin
            case (nsa_state)
                NSA_IDLE: begin
                    nsa_wr_en <= 1'b0;
                    if (nsa_start) begin
                        case (nsa_op)
                            2'b00, 2'b01: begin  // DQADD or DQMUL
                                // Load operands from NSA register bank into ALU
                                alu_a_real_z0 <= nsa_regs[{nsa_srcA[0], 3'b000} + 4'd0];
                                alu_a_real_z1 <= nsa_regs[{nsa_srcA[0], 3'b000} + 4'd1];
                                alu_a_real_z2 <= nsa_regs[{nsa_srcA[0], 3'b000} + 4'd2];
                                alu_a_real_z3 <= nsa_regs[{nsa_srcA[0], 3'b000} + 4'd3];
                                alu_a_eps_z0  <= nsa_regs[{nsa_srcA[0], 3'b100} + 4'd0];
                                alu_a_eps_z1  <= nsa_regs[{nsa_srcA[0], 3'b100} + 4'd1];
                                alu_a_eps_z2  <= nsa_regs[{nsa_srcA[0], 3'b100} + 4'd2];
                                alu_a_eps_z3  <= nsa_regs[{nsa_srcA[0], 3'b100} + 4'd3];
                                alu_b_real_z0 <= nsa_regs[{nsa_srcB[0], 3'b000} + 4'd0];
                                alu_b_real_z1 <= nsa_regs[{nsa_srcB[0], 3'b000} + 4'd1];
                                alu_b_real_z2 <= nsa_regs[{nsa_srcB[0], 3'b000} + 4'd2];
                                alu_b_real_z3 <= nsa_regs[{nsa_srcB[0], 3'b000} + 4'd3];
                                alu_b_eps_z0  <= nsa_regs[{nsa_srcB[0], 3'b100} + 4'd0];
                                alu_b_eps_z1  <= nsa_regs[{nsa_srcB[0], 3'b100} + 4'd1];
                                alu_b_eps_z2  <= nsa_regs[{nsa_srcB[0], 3'b100} + 4'd2];
                                alu_b_eps_z3  <= nsa_regs[{nsa_srcB[0], 3'b100} + 4'd3];
                                alu_op_mul <= nsa_op[0];  // 01 = mul
                                alu_start <= 1'b1;
                                nsa_state <= NSA_COMPUTE;
                            end
                            2'b10: begin  // LOAD: QR regfile → NSA bank
                                // Map 4 × 36-bit RationalSurd → 8 × 32-bit A31 coefficients
                                // QR format: {P[17:0], Q[17:0]} per lane
                                // For now, load scalar-only (Q=0) into real part, zero eps
                                nsa_regs[{nsa_srcA[0], 3'b000} + 4'd0] <= {14'd0, qr_features_in[17:0]};
                                nsa_regs[{nsa_srcA[0], 3'b000} + 4'd1] <= 32'd0;
                                nsa_regs[{nsa_srcA[0], 3'b000} + 4'd2] <= 32'd0;
                                nsa_regs[{nsa_srcA[0], 3'b000} + 4'd3] <= 32'd0;
                                nsa_regs[{nsa_srcA[0], 3'b100} + 4'd0] <= 32'd0;
                                nsa_regs[{nsa_srcA[0], 3'b100} + 4'd1] <= 32'd0;
                                nsa_regs[{nsa_srcA[0], 3'b100} + 4'd2] <= 32'd0;
                                nsa_regs[{nsa_srcA[0], 3'b100} + 4'd3] <= 32'd0;
                                nsa_state <= NSA_DONE_CYCLE;
                            end
                            2'b11: begin  // STORE: NSA bank → QR regfile
                                nsa_features_out <= {
                                    {18'd0, nsa_regs[{nsa_srcA[0], 3'b000} + 4'd0][17:0]},
                                    {18'd0, nsa_regs[{nsa_srcA[0], 3'b000} + 4'd0][17:0]},
                                    {18'd0, nsa_regs[{nsa_srcA[0], 3'b000} + 4'd0][17:0]},
                                    {18'd0, nsa_regs[{nsa_srcA[0], 3'b000} + 4'd0][17:0]}
                                };
                                nsa_wr_en   <= 1'b1;
                                nsa_wr_addr <= nsa_dest;
                                nsa_state   <= NSA_DONE_CYCLE;
                            end
                        endcase
                    end
                end

                NSA_COMPUTE: begin
                    alu_start <= 1'b0;
                    nsa_state <= NSA_COMPUTE_WAIT;
                end

                NSA_COMPUTE_WAIT: begin
                    if (alu_done) begin
                        // Write ALU result back to NSA bank at dest slot
                        nsa_regs[dest_real_base + 4'd0] <= alu_r_real_z0;
                        nsa_regs[dest_real_base + 4'd1] <= alu_r_real_z1;
                        nsa_regs[dest_real_base + 4'd2] <= alu_r_real_z2;
                        nsa_regs[dest_real_base + 4'd3] <= alu_r_real_z3;
                        nsa_regs[dest_real_base + 4'd4] <= alu_r_eps_z0;
                        nsa_regs[dest_real_base + 4'd5] <= alu_r_eps_z1;
                        nsa_regs[dest_real_base + 4'd6] <= alu_r_eps_z2;
                        nsa_regs[dest_real_base + 4'd7] <= alu_r_eps_z3;
                        nsa_state <= NSA_DONE_CYCLE;
                    end
                end

                NSA_STORE_SLOT: begin
                    nsa_state <= NSA_DONE_CYCLE;
                end

                NSA_DONE_CYCLE: begin
                    // Accept next instruction immediately if start is asserted
                    nsa_wr_en <= 1'b0;
                    if (nsa_start) begin
                        case (nsa_op)
                            2'b00, 2'b01: begin  // DQADD or DQMUL — same as IDLE path
                                alu_a_real_z0 <= nsa_regs[{nsa_srcA[0], 3'b000} + 4'd0];
                                alu_a_real_z1 <= nsa_regs[{nsa_srcA[0], 3'b000} + 4'd1];
                                alu_a_real_z2 <= nsa_regs[{nsa_srcA[0], 3'b000} + 4'd2];
                                alu_a_real_z3 <= nsa_regs[{nsa_srcA[0], 3'b000} + 4'd3];
                                alu_a_eps_z0  <= nsa_regs[{nsa_srcA[0], 3'b100} + 4'd0];
                                alu_a_eps_z1  <= nsa_regs[{nsa_srcA[0], 3'b100} + 4'd1];
                                alu_a_eps_z2  <= nsa_regs[{nsa_srcA[0], 3'b100} + 4'd2];
                                alu_a_eps_z3  <= nsa_regs[{nsa_srcA[0], 3'b100} + 4'd3];
                                alu_b_real_z0 <= nsa_regs[{nsa_srcB[0], 3'b000} + 4'd0];
                                alu_b_real_z1 <= nsa_regs[{nsa_srcB[0], 3'b000} + 4'd1];
                                alu_b_real_z2 <= nsa_regs[{nsa_srcB[0], 3'b000} + 4'd2];
                                alu_b_real_z3 <= nsa_regs[{nsa_srcB[0], 3'b000} + 4'd3];
                                alu_b_eps_z0  <= nsa_regs[{nsa_srcB[0], 3'b100} + 4'd0];
                                alu_b_eps_z1  <= nsa_regs[{nsa_srcB[0], 3'b100} + 4'd1];
                                alu_b_eps_z2  <= nsa_regs[{nsa_srcB[0], 3'b100} + 4'd2];
                                alu_b_eps_z3  <= nsa_regs[{nsa_srcB[0], 3'b100} + 4'd3];
                                alu_op_mul <= nsa_op[0];
                                alu_start <= 1'b1;
                                nsa_state <= NSA_COMPUTE;
                            end
                            2'b10: begin  // LOAD
                                nsa_regs[{nsa_srcA[0], 3'b000} + 4'd0] <= {14'd0, qr_features_in[17:0]};
                                nsa_regs[{nsa_srcA[0], 3'b000} + 4'd1] <= 32'd0;
                                nsa_regs[{nsa_srcA[0], 3'b000} + 4'd2] <= 32'd0;
                                nsa_regs[{nsa_srcA[0], 3'b000} + 4'd3] <= 32'd0;
                                nsa_regs[{nsa_srcA[0], 3'b100} + 4'd0] <= 32'd0;
                                nsa_regs[{nsa_srcA[0], 3'b100} + 4'd1] <= 32'd0;
                                nsa_regs[{nsa_srcA[0], 3'b100} + 4'd2] <= 32'd0;
                                nsa_regs[{nsa_srcA[0], 3'b100} + 4'd3] <= 32'd0;
                                nsa_state <= NSA_DONE_CYCLE;  // stay in DONE_CYCLE
                            end
                            2'b11: begin  // STORE
                                nsa_features_out <= {
                                    {18'd0, nsa_regs[{nsa_srcA[0], 3'b000} + 4'd0][17:0]},
                                    {18'd0, nsa_regs[{nsa_srcA[0], 3'b000} + 4'd0][17:0]},
                                    {18'd0, nsa_regs[{nsa_srcA[0], 3'b000} + 4'd0][17:0]},
                                    {18'd0, nsa_regs[{nsa_srcA[0], 3'b000} + 4'd0][17:0]}
                                };
                                nsa_wr_en   <= 1'b1;
                                nsa_wr_addr <= nsa_dest;
                            end
                        endcase
                    end else begin
                        nsa_state <= NSA_IDLE;
                    end
                end

                default: nsa_state <= NSA_IDLE;
            endcase
        end
    end

endmodule
