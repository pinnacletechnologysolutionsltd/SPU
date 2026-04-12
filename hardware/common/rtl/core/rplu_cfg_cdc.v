// rplu_cfg_cdc.v
// Simple single-word CDC (toggle-handshake) for RPLU config writes.
// Transfers a single 78-bit payload: {sel[2:0], material[0], addr[9:0], data[63:0]}
// from src clock domain into dst clock domain. Provides a single-cycle wr_dst
// pulse in the destination domain and toggles an ack back to the source.

module rplu_cfg_cdc(
    input  wire        clk_src,
    input  wire        rst_n_src,
    input  wire        wr_src,
    input  wire [2:0]  sel_src,
    input  wire        material_src,
    input  wire [9:0]  addr_src,
    input  wire [63:0] data_src,

    input  wire        clk_dst,
    input  wire        rst_n_dst,
    output reg         wr_dst,
    output reg  [2:0]  sel_dst,
    output reg         material_dst,
    output reg  [9:0]  addr_dst,
    output reg  [63:0] data_dst
);

    localparam integer WPAY = 78; // 3 + 1 + 10 + 64

    // --- Source side ---
    reg req_toggle_src;                 // toggled on new write
    reg [WPAY-1:0] payload_q_src;      // captured payload in src domain
    reg ack_sync0_src, ack_sync1_src;  // synchroniser for ack toggle from dst
    reg last_ack_sync;                  // remembers last ack state seen
    reg pending_src;

    // ack_toggle_dst is driven in the destination domain (see below)
    // We declare it here so the source-side can sample it via synchronisers.
    reg ack_toggle_dst; // driven by dst always-block

    always @(posedge clk_src or negedge rst_n_src) begin
        if (!rst_n_src) begin
            req_toggle_src  <= 1'b0;
            payload_q_src   <= {WPAY{1'b0}};
            ack_sync0_src   <= 1'b0;
            ack_sync1_src   <= 1'b0;
            last_ack_sync   <= 1'b0;
            pending_src     <= 1'b0;
        end else begin
            // sync ack back from destination
            ack_sync0_src <= ack_toggle_dst;
            ack_sync1_src <= ack_sync0_src;

            if (wr_src && !pending_src) begin
                // capture payload and toggle request
                payload_q_src <= {sel_src, material_src, addr_src, data_src};
                req_toggle_src <= ~req_toggle_src;
                pending_src <= 1'b1;
            end

            // if ack changed (toggle seen), clear pending
            if (ack_sync1_src != last_ack_sync) begin
                pending_src   <= 1'b0;
                last_ack_sync <= ack_sync1_src;
            end
        end
    end

    // --- Destination side ---
    reg req_sync0_dst, req_sync1_dst;   // synchroniser for req toggle from src
    reg req_sync_prev;                  // previous stable value
    reg [WPAY-1:0] sampler0, sampler1;  // two-stage sampler for wide payload

    localparam DST_IDLE  = 2'd0;
    localparam DST_WAIT1 = 2'd1;
    localparam DST_WAIT2 = 2'd2;
    localparam DST_ACK   = 2'd3;
    reg [1:0] dst_state;

    // ack_toggle_dst toggled here to acknowledge transfer (synchronised back)
    always @(posedge clk_dst or negedge rst_n_dst) begin
        if (!rst_n_dst) begin
            req_sync0_dst <= 1'b0;
            req_sync1_dst <= 1'b0;
            req_sync_prev <= 1'b0;
            sampler0      <= {WPAY{1'b0}};
            sampler1      <= {WPAY{1'b0}};
            ack_toggle_dst<= 1'b0;
            wr_dst        <= 1'b0;
            sel_dst       <= 3'd0;
            material_dst  <= 1'b0;
            addr_dst      <= 10'd0;
            data_dst      <= 64'd0;
            dst_state     <= DST_IDLE;
        end else begin
            // sample the request toggle (from src domain)
            req_sync0_dst <= req_toggle_src;
            req_sync1_dst <= req_sync0_dst;

            case (dst_state)
                DST_IDLE: begin
                    wr_dst <= 1'b0;
                    if (req_sync1_dst != req_sync_prev) begin
                        // new request observed — begin capture
                        sampler0 <= payload_q_src; // sample wide payload asynchronously
                        dst_state <= DST_WAIT1;
                    end
                end

                DST_WAIT1: begin
                    // let first-stage settle into second-stage
                    sampler1 <= sampler0;
                    dst_state <= DST_WAIT2;
                end

                DST_WAIT2: begin
                    // now sampler1 is stable copy of payload_q_src
                    // extract fields and present them in destination domain
                    sel_dst      <= sampler1[WPAY-1:WPAY-3];          // bits [77:75]
                    material_dst <= sampler1[WPAY-4];               // bit 74
                    addr_dst     <= sampler1[WPAY-5:WPAY-14];       // bits [73:64]
                    data_dst     <= sampler1[63:0];                 // bits [63:0]

                    // one-cycle write pulse
                    wr_dst <= 1'b1;

                    // toggle ack back to source
                    ack_toggle_dst <= ~ack_toggle_dst;

                    // remember this req value so we don't re-trigger on same toggle
                    req_sync_prev <= req_sync1_dst;

                    dst_state <= DST_ACK;
                end

                DST_ACK: begin
                    // clear pulse and return to idle
                    wr_dst <= 1'b0;
                    dst_state <= DST_IDLE;
                end

                default: dst_state <= DST_IDLE;
            endcase
        end
    end

endmodule
