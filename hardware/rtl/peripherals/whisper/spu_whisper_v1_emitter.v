// spu_whisper_v1_emitter.v — Whisper v1 coherence-plane frame emitter
//
// Emits an 18-byte ASCII frame each period while is_laminar holds.
// Frame: W1 ii ff dd ss xx\n
// ss = som_label (Arlinghaus SOM integration) — no longer an
// auto-incrementing counter; the satellite feeds its edge SOM output.
// XOR checksum covers bytes 0..14 (spaces included).
//
// Per docs/WHISPER_V1_SPEC.md §2–3.  Fail-silent while !is_laminar.
module spu_whisper_v1_emitter #(
    parameter CLK_HZ        = 12000000,
    parameter BAUD          = 115200,
    parameter PERIOD_CYCLES = CLK_HZ / 1
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       is_laminar,
    input  wire [3:0] node_id,
    input  wire [2:0] flags_in,
    input  wire [7:0] dissonance,
    input  wire [7:0] som_label,   // Arlinghaus: edge SOM classification
    output wire       tx,
    output reg        busy
);
    localparam FRAME_LEN = 18;
    localparam IDLE_GAP  = 16;  // idle cycles between bytes (≥1 bit-time margin)

    // ── UART TX ──────────────────────────────────────────────────────
    wire [7:0] tx_data;
    reg        tx_send;
    wire       tx_busy;
    wire       tx_done;

    spu_uart_tx #(.CLK_HZ(CLK_HZ), .BAUD(BAUD)) u_uart (
        .clk(clk), .rst_n(rst_n),
        .data(tx_data), .send(tx_send),
        .tx(tx), .busy(tx_busy), .done(tx_done)
    );

    // ── Period counter ───────────────────────────────────────────────
    reg [31:0] period_cnt;
    wire       period_tick;
    assign period_tick = (period_cnt == PERIOD_CYCLES - 1);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)         period_cnt <= 32'd0;
        else if (period_tick) period_cnt <= 32'd0;
        else                period_cnt <= period_cnt + 32'd1;
    end

    // ── nibble → hex ASCII ───────────────────────────────────────────
    function [7:0] h;
        input [3:0] n;
        begin h = (n < 10) ? (8'h30 + n) : (8'h37 + n); end
    endfunction

    // ── FSM states ───────────────────────────────────────────────────
    localparam IDLE  = 2'd0;
    localparam SEND  = 2'd1;
    localparam GAP   = 2'd2;

    reg [1:0]  state;
    reg [4:0]  byte_idx;
    reg [15:0] gap_cnt;

    // ── Frame bytes (combinational, computed from som_label) ────────
    wire [7:0] fb    = {5'b0, flags_in};
    wire [7:0] check = 8'h57 ^ 8'h31 ^ 8'h20 ^ h(4'd0) ^ h(node_id[3:0])
                     ^ 8'h20 ^ h(fb[7:4]) ^ h(fb[3:0]) ^ 8'h20
                     ^ h(dissonance[7:4]) ^ h(dissonance[3:0]) ^ 8'h20
                     ^ h(som_label[7:4]) ^ h(som_label[3:0]) ^ 8'h20;

    wire [7:0] frm [0:17];
    assign frm[0]  = 8'h57;
    assign frm[1]  = 8'h31;
    assign frm[2]  = 8'h20;
    assign frm[3]  = h(4'd0);          // node_id is 4-bit [3:0]; upper nibble is always 0
    assign frm[4]  = h(node_id[3:0]);
    assign frm[5]  = 8'h20;
    assign frm[6]  = h(fb[7:4]);
    assign frm[7]  = h(fb[3:0]);
    assign frm[8]  = 8'h20;
    assign frm[9]  = h(dissonance[7:4]);
    assign frm[10] = h(dissonance[3:0]);
    assign frm[11] = 8'h20;
    assign frm[12] = h(som_label[7:4]);
    assign frm[13] = h(som_label[3:0]);
    assign frm[14] = 8'h20;
    assign frm[15] = h(check[7:4]);
    assign frm[16] = h(check[3:0]);
    assign frm[17] = 8'h0A;

    assign tx_data = frm[byte_idx];

    // ── Main FSM ─────────────────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= IDLE;
            byte_idx <= 0;
            gap_cnt  <= 0;
            busy     <= 0;
            tx_send  <= 0;
        end else begin
            tx_send <= 0;

            case (state)
                IDLE: begin
                    busy <= 0;
                    if (period_tick && is_laminar) begin
                        byte_idx <= 0;
                        gap_cnt  <= 0;
                        busy     <= 1;
                        state    <= SEND;
                    end
                end

                SEND: begin
                    if (!tx_busy && gap_cnt == 0) begin
                        tx_send  <= 1;
                        gap_cnt  <= IDLE_GAP;
                    end else if (gap_cnt > 0) begin
                        gap_cnt  <= gap_cnt - 16'd1;
                        if (gap_cnt == 1) begin
                            if (byte_idx < FRAME_LEN - 1)
                                byte_idx <= byte_idx + 5'd1;
                            else begin
                                state <= IDLE;
                            end
                        end
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
