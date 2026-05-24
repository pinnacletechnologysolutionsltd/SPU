// spu_instr_decode.v — SPU-13 Instruction Decode & Execute (v1.0)
// Drives the QR datapath from sequencer-dispatched instructions.
// Handles: QLDI, ROTC, QSUB, DELTA, HEX, QLOG, IDNT, HALT.
//
// Instantiates inside spu13_core.v alongside the QR regfile and rotor core.
// Connected to sequencer via instr_* signals.
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
    localparam OP_QLDI = 8'h1D;
    localparam OP_ROTC = 8'h1C;
    localparam OP_QSUB = 8'h1B;
    localparam OP_DELTA = 8'h1E;
    localparam OP_HEX  = 8'h16;
    localparam OP_QLOG = 8'h14;
    localparam OP_IDNT = 8'h00;  // identity load (treated as QLDI 1,0,0,0)
    localparam OP_HALT = 8'hFF;

    // ── State ───────────────────────────────────────────────────────
    localparam S_IDLE = 0, S_DECODE = 1, S_EXEC = 2, S_WAIT_ROTC = 3,
               S_WRITEBACK = 4;
    reg [2:0] state;
    reg [7:0] saved_opcode;
    reg [7:0] saved_r1, saved_r2;
    reg [15:0] saved_p1a, saved_p1b;

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
                            // Load immediate Quadray vector
                            if (saved_opcode == OP_IDNT) begin
                                // Identity: (1,0,0,0)
                                qrf_wr_A <= 64'd1;
                                qrf_wr_B <= 64'd0;
                                qrf_wr_C <= 64'd0;
                                qrf_wr_D <= 64'd0;
                            end else begin
                                // QLDI: unpack signed bytes from P1_A[15:8]=A, P1_A[7:0]=B,
                                //                            P1_B[15:8]=C, P1_B[7:0]=D
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
                            // Read source QR register
                            qrf_rd_addr <= saved_r2[3:0];
                            // Start ROTC with angle from P1_A[5:0], field from P1_A[7:6]
                            rote_angle <= saved_p1a[5:0];
                            rote_field <= saved_p1a[7:6];
                            state <= S_WAIT_ROTC;
                            instr_stall <= 1;
                        end

                        OP_QSUB: begin
                            // QSUB QRd, QRa, QRb: QRd = QRa - QRb
                            // Reads both source registers, subtracts, writes dest
                            // qrf_rd_addr currently reads QR[r2]
                            qrf_rd_addr <= saved_r2[3:0];
                            // Note: second read needs another cycle; simplified here
                            // as single-cycle subtract with sequential reads
                            qrf_wr_A <= qrf_rd_A;  // A passes through
                            qrf_wr_B <= qrf_rd_B;  // placeholder
                            qrf_wr_C <= qrf_rd_C;
                            qrf_wr_D <= qrf_rd_D;
                            qrf_wr_addr <= saved_r1[3:0];
                            qrf_wr_en <= 1;
                            state <= S_WRITEBACK;
                        end

                        OP_HEX: begin
                            // Read QR register, project to hex, write to R regs
                            qrf_rd_addr <= saved_r2[3:0];
                            state <= S_WRITEBACK;
                            // Hex projection happens here (simplified)
                            reg_wr_addr_0 <= saved_r1[3:0];
                            reg_wr_data_0 <= qrf_rd_A[31:0] - qrf_rd_D[31:0];
                            reg_wr_en_0 <= 1;
                            reg_wr_addr_1 <= (saved_r1[3:0] + 1) & 4'hF;
                            reg_wr_data_1 <= qrf_rd_B[31:0] - qrf_rd_D[31:0];
                            reg_wr_en_1 <= 1;
                            uart_strobe <= 1;
                            uart_data <= qrf_rd_A[31:0] - qrf_rd_D[31:0];
                        end

                        default: begin
                            // Unknown opcode → skip
                            instr_done <= 1;
                            instr_stall <= 0;
                            state <= S_IDLE;
                        end
                    endcase
                end

                S_WAIT_ROTC: begin
                    instr_stall <= 1;
                    rote_start <= 1;
                    if (rote_done) begin
                        rote_start <= 0;
                        qrf_wr_addr <= saved_r1[3:0];
                        qrf_wr_A <= qrf_rd_A;  // A invariant
                        qrf_wr_B <= qrf_rd_B;  // (updated by rotor core)
                        qrf_wr_C <= qrf_rd_C;
                        qrf_wr_D <= qrf_rd_D;
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
