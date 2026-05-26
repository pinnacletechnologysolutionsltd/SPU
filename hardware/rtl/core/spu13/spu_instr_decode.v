// spu_instr_decode.v — SPU-13 Instruction Decode & Execute (v1.1)
// Drives the QR datapath from sequencer-dispatched instructions.
// Handles: QLDI, ROTC, QSUB, DELTA, HEX, QLOG, IDNT, HALT.
//
// Refactored for multi-cycle operand fetch (single-port QRF).
//
// CC0 1.0 Universal.

module spu_instr_decode (
    input  wire        clk,
    input  wire        rst_n,

    // Instruction from sequencer
    input  wire        instr_valid,
    input  wire [7:0]  instr_opcode,
    input  wire [7:0]  instr_r1,
    input  wire [7:0]  instr_r2,
    input  wire [15:0] instr_p1_a,
    input  wire [15:0] instr_p1_b,
    output reg         instr_done,
    output reg         instr_stall,

    // QR Regfile interface (read)
    output reg  [3:0]  qrf_rd_addr,
    input  wire [63:0] qrf_rd_A,
    input  wire [63:0] qrf_rd_B,
    input  wire [63:0] qrf_rd_C,
    input  wire [63:0] qrf_rd_D,

    // QR Regfile interface (write)
    output reg         qrf_wr_en,
    output reg  [3:0]  qrf_wr_addr,
    output reg  [63:0] qrf_wr_A,
    output reg  [63:0] qrf_wr_B,
    output reg  [63:0] qrf_wr_C,
    output reg  [63:0] qrf_wr_D,

    // ROTC rotor core control
    output reg         rote_start,
    output reg  [5:0]  rote_angle,
    output reg  [1:0]  rote_field,
    input  wire        rote_done,

    // General register file (R0-R15) for hex output
    output reg  [3:0]  reg_wr_addr_0,
    output reg  [31:0] reg_wr_data_0,
    output reg         reg_wr_en_0,
    output reg  [3:0]  reg_wr_addr_1,
    output reg  [31:0] reg_wr_data_1,
    output reg         reg_wr_en_1,

    // Debug / UART output
    output reg         uart_strobe,
    output reg  [31:0] uart_data,

    // Halt signal
    output reg         core_halted
);

    // ── Opcode constants ────────────────────────────────────────────
    localparam OP_QLDI  = 8'h1D;
    localparam OP_ROTC  = 8'h1C;
    localparam OP_QSUB  = 8'h1B;
    localparam OP_DELTA = 8'h1E;
    localparam OP_HEX   = 8'h16;
    localparam OP_QLOG  = 8'h14;
    localparam OP_IDNT  = 8'h18;  // ISA Ref 3.2 says 0x18
    localparam OP_HALT  = 8'h08;  // ISA Ref 3.2 says 0x08

    // ── State ───────────────────────────────────────────────────────
    localparam S_IDLE       = 0, 
               S_DECODE     = 1, 
               S_FETCH_OP2  = 2, 
               S_EXEC       = 3, 
               S_WAIT_ROTC  = 4,
               S_WRITEBACK  = 5;

    reg [2:0] state;
    reg [7:0] saved_opcode;
    reg [7:0] saved_r1, saved_r2;
    reg [15:0] saved_p1a, saved_p1b;

    // Operand Latches
    reg [63:0] op1_A, op1_B, op1_C, op1_D;
    reg [63:0] op2_A, op2_B, op2_C, op2_D;

    // Helper: RationalSurd Subtraction
    function [63:0] rs_sub;
        input [63:0] left;
        input [63:0] right;
        begin
            rs_sub = {left[63:32] - right[63:32], left[31:0] - right[31:0]};
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            instr_done <= 0;
            instr_stall <= 0;
            qrf_wr_en <= 0;
            qrf_rd_addr <= 0;
            qrf_wr_addr <= 0;
            qrf_wr_A <= 0; qrf_wr_B <= 0; qrf_wr_C <= 0; qrf_wr_D <= 0;
            rote_start <= 0;
            reg_wr_en_0 <= 0; reg_wr_en_1 <= 0;
            uart_strobe <= 0;
            core_halted <= 0;
            saved_opcode <= 0;
            op1_A <= 0; op1_B <= 0; op1_C <= 0; op1_D <= 0;
            op2_A <= 0; op2_B <= 0; op2_C <= 0; op2_D <= 0;
        end else begin
            instr_done <= 0;
            instr_stall <= 0;
            qrf_wr_en <= 0;
            rote_start <= 0;
            reg_wr_en_0 <= 0;
            reg_wr_en_1 <= 0;
            uart_strobe <= 0;

            case (state)
                S_IDLE: begin
                    if (instr_valid) begin
                        saved_opcode <= instr_opcode;
                        saved_r1  <= instr_r1;
                        saved_r2  <= instr_r2;
                        saved_p1a <= instr_p1_a;
                        saved_p1b <= instr_p1_b;
                        state <= S_DECODE;
                        instr_stall <= 1;
                        `ifdef SIM
                        $display("DECODE: captured op=%h r1=%h r2=%h at time=%0t", instr_opcode, instr_r1, instr_r2, $time);
                        `endif
                    end
                end

                S_DECODE: begin
                    instr_stall <= 1;
                    case (saved_opcode)
                        OP_HALT: begin
                            core_halted <= 1;
                            instr_done <= 1;
                            instr_stall <= 0;
                            state <= S_IDLE;
                        end

                        OP_QLDI, OP_IDNT: begin
                            if (saved_opcode == OP_IDNT) begin
                                qrf_wr_A <= {32'd0, 32'd1}; // identity
                                qrf_wr_B <= 64'd0;
                                qrf_wr_C <= 64'd0;
                                qrf_wr_D <= 64'd0;
                            end else begin
                                // QLDI: A,B from p1_a, C,D from p1_b
                                qrf_wr_A <= {{56{saved_p1a[15]}}, saved_p1a[15:8]};
                                qrf_wr_B <= {{56{saved_p1a[7]}},  saved_p1a[7:0]};
                                qrf_wr_C <= {{56{saved_p1b[15]}}, saved_p1b[15:8]};
                                qrf_wr_D <= {{56{saved_p1b[7]}},  saved_p1b[7:0]};
                            end
                            qrf_wr_addr <= saved_r1[3:0];
                            qrf_wr_en <= 1;
                            state <= S_WRITEBACK;
                        end

                        OP_ROTC: begin
                            qrf_rd_addr <= saved_r2[3:0];
                            rote_angle <= saved_p1a[5:0];
                            rote_field <= saved_p1a[7:6];
                            state <= S_WAIT_ROTC;
                        end

                        OP_QSUB: begin
                            // QSUB QRd, QRa, QRb (r1=d, r2=a, p1_a[3:0]=b)
                            qrf_rd_addr <= saved_r2[3:0]; // Fetch QRa
                            state <= S_FETCH_OP2;
                        end

                        OP_DELTA: begin
                            // DELTA QRd, Q1, Q2, steps
                            // p1_a=Q1, p1_b=Q2, r2=steps (if 0, default 4)
                            // Computes (Q1+Q2) and 4*Q1*Q2*(steps-k)/steps
                            // Correcting per VM: q_sum = Q1 + Q2
                            qrf_wr_A <= {32'd0, {16'd0, saved_p1a + saved_p1b}};
                            // rhs_sq = 4 * Q1 * Q2 (for k=0)
                            qrf_wr_B <= {32'd0, 32'd4 * saved_p1a * saved_p1b};
                            // steps: use saved_r2 directly (default 4 if 0)
                            qrf_wr_C <= {32'd0, (saved_r2 > 0 ? {24'd0, saved_r2} : 32'd4)}; 
                            qrf_wr_D <= 64'd0;
                            qrf_wr_addr <= saved_r1[3:0];
                            qrf_wr_en <= 1;
                            state <= S_WRITEBACK;
                        end

                        OP_HEX, OP_QLOG: begin
                            qrf_rd_addr <= saved_r2[3:0];
                            state <= S_EXEC;
                        end

                        default: begin
                            instr_done <= 1;
                            instr_stall <= 0;
                            state <= S_IDLE;
                        end
                    endcase
                end

                S_FETCH_OP2: begin
                    instr_stall <= 1;
                    // Latch Op1 (QRa)
                    op1_A <= qrf_rd_A; op1_B <= qrf_rd_B;
                    op1_C <= qrf_rd_C; op1_D <= qrf_rd_D;
                    // Fetch Op2 (QRb)
                    qrf_rd_addr <= saved_p1a[3:0];
                    state <= S_EXEC;
                end

                S_EXEC: begin
                    instr_stall <= 1;
                    case (saved_opcode)
                        OP_QSUB: begin
                            // Op2 (QRb) available combinationally now
                            qrf_wr_A <= rs_sub(op1_A, qrf_rd_A);
                            qrf_wr_B <= rs_sub(op1_B, qrf_rd_B);
                            qrf_wr_C <= rs_sub(op1_C, qrf_rd_C);
                            qrf_wr_D <= rs_sub(op1_D, qrf_rd_D);
                            qrf_wr_addr <= saved_r1[3:0];
                            qrf_wr_en <= 1;
                            state <= S_WRITEBACK;
                        end
                        OP_HEX: begin
                            reg_wr_addr_0 <= saved_r1[3:0];
                            reg_wr_data_0 <= qrf_rd_B[31:0] - qrf_rd_D[31:0]; // Q = B-D
                            reg_wr_en_0 <= 1;
                            reg_wr_addr_1 <= (saved_r1[3:0] + 1) & 4'hF;
                            reg_wr_data_1 <= qrf_rd_A[31:0] - qrf_rd_D[31:0]; // R = A-D
                            reg_wr_en_1 <= 1;
                            uart_strobe <= 1;
                            uart_data <= qrf_rd_B[31:0] - qrf_rd_D[31:0];
                            state <= S_WRITEBACK;
                        end
                        OP_QLOG: begin
                            // QLOG QRn: Output rational components to UART
                            uart_strobe <= 1;
                            uart_data <= qrf_rd_A[31:0]; // just A for now
                            state <= S_WRITEBACK;
                        end
                        default: state <= S_IDLE;
                    endcase
                end

                S_WAIT_ROTC: begin
                    instr_stall <= 1;
                    rote_start <= 1;
                    if (rote_done) begin
                        rote_start <= 0;
                        qrf_wr_addr <= saved_r1[3:0];
                        // Components updated by rotor core
                        qrf_wr_A <= qrf_rd_A; // A invariant
                        // (B,C,D updated signals would come from rotor_core_tdm outputs
                        // but those are routed in spu13_core.v muxes, not here).
                        // Actually, in SPU-13 core, the writeback data is muxed.
                        // We just need to assert wr_en.
                        qrf_wr_en <= 1;
                        state <= S_WRITEBACK;
                    end
                end

                S_WRITEBACK: begin
                    instr_done <= 1;
                    instr_stall <= 0;
                    state <= S_IDLE;
                end
            endcase
        end
    end

endmodule
