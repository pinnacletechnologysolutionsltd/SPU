// spu_ddr3_bridge_gowin.v — SPU to Gowin DDR3 Interface Bridge
// Objective: Efficiently stream SPU manifolds into 128MB DDR3.

`include "spu_arch_defines.vh"

module spu_ddr3_bridge_gowin (
    input  wire        clk,        // System clk (e.g., 100MHz)
    input  wire        rst_n,

    // SPU Sovereign Bus Interface
    `MANIFOLD_SIGS,

    // Interface to Gowin DDR3 IP (Native Interface Port)
    output reg         ddr_wr_en,
    output reg         ddr_rd_en,
    output reg  [24:0] ddr_addr,   // Word address for 128MB
    output reg  [31:0] ddr_wr_data,
    input  wire [31:0] ddr_rd_data,
    input  wire        ddr_ready,
    input  wire        ddr_rd_valid
);

    // --- State Machine ---
    localparam IDLE     = 3'd0;
    localparam FETCH    = 3'd1;
    localparam STORE    = 3'd2;
    localparam WAIT     = 3'd3;

    reg [2:0] state;
    reg [3:0] chord_ptr; // 0 to 12 (13 axes)

    // Bridge Logic: A single 832-bit manifold burst is 26 words of 32-bits.
    // Address mapping: Manifold 0 = 0x0, Manifold 1 = 0x20, etc.

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            chord_ptr <= 0;
            mem_ready <= 1'b0;
            mem_burst_done <= 1'b0;
            ddr_wr_en <= 1'b0;
            ddr_rd_en <= 1'b0;
        end else begin
            mem_ready <= ddr_ready;
            mem_burst_done <= 1'b0;

            case (state)
                IDLE: begin
                    chord_ptr <= 0;
                    if (mem_burst_rd) begin
                        state <= FETCH;
                        ddr_rd_en <= 1'b1;
                        ddr_addr <= {mem_addr, 5'b0}; // Start of manifold
                    end else if (mem_burst_wr) begin
                        state <= STORE;
                        ddr_wr_en <= 1'b1;
                        ddr_addr <= {mem_addr, 5'b0};
                    end
                end

                FETCH: begin
                    // TODO: Implement multi-word burst logic for Gowin DDR3
                    if (ddr_rd_valid) begin
                        // Load chords into mem_rd_manifold
                        if (chord_ptr == 25) begin // 26 words total
                            state <= WAIT;
                            mem_burst_done <= 1'b1;
                        end else begin
                            chord_ptr <= chord_ptr + 1;
                        end
                    end
                end

                STORE: begin
                    if (ddr_ready) begin
                        if (chord_ptr == 25) begin
                            state <= WAIT;
                            mem_burst_done <= 1'b1;
                        end else begin
                            chord_ptr <= chord_ptr + 1;
                        end
                    end
                end

                WAIT: begin
                    ddr_wr_en <= 1'b0;
                    ddr_rd_en <= 1'b1;
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule
