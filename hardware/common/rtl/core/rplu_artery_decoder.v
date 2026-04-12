// RPLU Artery Decoder
// Listens for multi-chord writes on the Artery FIFO output (piranha/fast domain)
// Protocol (two-chord):
//  - CHORD 0 (HEADER): [63:56]=0xA5 (opcode), [55:48]=sel (8-bit, low 3 bits used), [47]=material, [46:37]=addr (10-bit), rest reserved
//  - CHORD 1 (DATA):   full 64-bit payload (cfg_wr_data)
// When a header is seen, the next inbound chord is delivered as DATA and a single-cycle
// cfg_wr_en is asserted with the collected parameters.

module rplu_artery_decoder(
    input  wire        clk,
    input  wire        rst_n,
    // inhale_valid should be high when inhale_chord is valid (e.g., inhale_rd_en)
    input  wire        inhale_valid,
    input  wire [63:0] inhale_chord,

    // decoded outputs (pulsed for one clk when DATA chord arrives)
    output reg         cfg_wr_en,
    output reg [2:0]   cfg_wr_sel,
    output reg         cfg_wr_material,
    output reg [9:0]   cfg_wr_addr,
    output reg [63:0]  cfg_wr_data
);

    localparam OPCODE_HDR = 8'hA5;

    reg waiting_data;
    reg [2:0] sel_r;
    reg material_r;
    reg [9:0] addr_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            waiting_data    <= 1'b0;
            cfg_wr_en       <= 1'b0;
            cfg_wr_sel      <= 3'd0;
            cfg_wr_material <= 1'b0;
            cfg_wr_addr     <= 10'd0;
            cfg_wr_data     <= 64'd0;
            sel_r           <= 3'd0;
            material_r      <= 1'b0;
            addr_r          <= 10'd0;
        end else begin
            cfg_wr_en <= 1'b0; // default pulse low
            if (inhale_valid) begin
                if (!waiting_data) begin
                    if (inhale_chord[63:56] == OPCODE_HDR) begin
                        // latch header fields
                        // NOTE: fields layout: [63:56]=OP, [55:48]=sel (8-bit), [47]=material, [46:37]=addr
                        sel_r      <= inhale_chord[50:48];  // low 3 bits of sel
                        material_r <= inhale_chord[47];
                        addr_r     <= inhale_chord[46:37];
                        waiting_data <= 1'b1;
                    end
                end else begin
                    // consume DATA chord and emit write pulse
                    cfg_wr_en       <= 1'b1;
                    cfg_wr_sel      <= sel_r;
                    cfg_wr_material <= material_r;
                    cfg_wr_addr     <= addr_r;
                    cfg_wr_data     <= inhale_chord;
                    waiting_data    <= 1'b0;
                end
            end
        end
    end

endmodule
