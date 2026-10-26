// spu_twin_regfile.v — Twin-Register File for SPU-13 ISA v1.0
//
// 32 entries × {Offer[63:0], Confirmation[63:0]} = 512 bytes
// Dual-port read: srcA (default .O) and srcB (default .C) in same cycle
// Single-port write: R[dest].O or R[dest].C
// Special registers: R0=ZERO, R1=PC, R2=FLAGS, R5=CHORD_IN, R7=QUAD_OUT
// SPU-4 mode: only banks 0-7 active (others read 0, discard writes)

`include "spu_isa_defines.vh"

module spu_twin_regfile (
    input  wire         clk,
    input  wire         rst_n,

    // Read port A (typically Offer slot)
    input  wire [ 4:0]  raddrA,
    input  wire         rselA_O,       // 1=read .O, 0=read .C
    output wire [63:0]  rdataA,

    // Read port B (typically Confirmation slot)
    input  wire [ 4:0]  raddrB,
    input  wire         rselB_O,       // 1=read .O, 0=read .C
    output wire [63:0]  rdataB,

    // Write port
    input  wire         wren,
    input  wire [ 4:0]  waddr,
    input  wire         wsel_O,        // 1=write .O, 0=write .C
    input  wire [63:0]  wdata,

    // Special register writes (external update)
    input  wire         flags_update,  // strobe: update FLAGS from flags_in
    input  wire [63:0]  flags_in,
    input  wire         chord_in_update,
    input  wire [63:0]  chord_in_data,
    input  wire         quad_out_update,
    input  wire [63:0]  quad_out_data,

    // SPU-4 sentinel mode (enable to reduce power)
    input  wire         spu4_mode
);

    // ── Register array: 32 entries × 2 slots × 64-bit ──
    // Offer slots
    reg [63:0] offer [0:31];
    // Confirmation slots
    reg [63:0] confirm [0:31];

    // ── Special register aliases ──
    // R0 = ZERO: always reads 0, writes discarded
    // R1 = PC: updated by program counter logic
    // R2 = FLAGS: updated by status flags
    // R5 = CHORD_IN: updated by SPI slave
    // R7 = QUAD_OUT: updated by RAU

    integer i;
    initial begin
        for (i = 0; i < 32; i = i + 1) begin
            offer[i]   = 64'd0;
            confirm[i] = 64'd0;
        end
    end

    // ── Read port A ──
    reg [63:0] readA;
    always @(*) begin
        if (raddrA == `SPU_REG_ZERO) begin
            readA = 64'd0;
        end else if (rselA_O) begin
            readA = offer[raddrA];
        end else begin
            readA = confirm[raddrA];
        end
    end
    assign rdataA = readA;

    // ── Read port B ──
    reg [63:0] readB;
    always @(*) begin
        if (raddrB == `SPU_REG_ZERO) begin
            readB = 64'd0;
        end else if (rselB_O) begin
            readB = offer[raddrB];
        end else begin
            readB = confirm[raddrB];
        end
    end
    assign rdataB = readB;

    // ── Write port (synchronous) ──
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1) begin
                offer[i]   <= 64'd0;
                confirm[i] <= 64'd0;
            end
        end else begin
            // External special register updates
            if (flags_update) begin
                offer[`SPU_REG_FLAGS] <= flags_in;
            end
            if (chord_in_update) begin
                offer[`SPU_REG_CHORD_IN] <= chord_in_data;
            end
            if (quad_out_update) begin
                offer[`SPU_REG_QUAD_OUT] <= quad_out_data;
            end

            // Normal register write (suppressed for SPU-4 mode upper banks)
            if (wren && waddr != `SPU_REG_ZERO && !(spu4_mode && waddr > 7)) begin
                if (wsel_O) begin
                    offer[waddr] <= wdata;
                end else begin
                    confirm[waddr] <= wdata;
                end
            end

            // SPU-4 sentinel mode: upper registers stay zero
            // (writes to R8-R31 suppressed above)
        end
    end

endmodule
