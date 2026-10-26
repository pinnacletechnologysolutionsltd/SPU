// spu13_tang25k_spu4_som_edge_debug_probe.v -- bench diagnostic probe, kept
// permanently (2026-08-17) but NOT part of the customer product contract.
// Bypasses spu4_som_edge_wrapper entirely and instantiates
// spu4_som_flash_loader + spu4_som_edge directly (same wiring
// spu4_som_flash_loader_tb.v uses in simulation), reporting node 0's raw
// hydrated weights for feature 0 and feature 3 over UART.
//
// Built same-day to bisect a real bench failure: spu13_tang25k_spu4_som_edge_probe.v
// reported SOM:F N=0 Q=000001A0 (416) instead of the oracle-expected N=1
// Q=00001900 (6400). This file's readback (P0/Q0/P3/Q3 all FFFF) is what
// isolated the actual cause -- the J4 SPI flash chip was never wired to the
// Tang 25K at all, only to the RP2040 programmer -- separating "hydration
// hardware fault" from "quadrance math bug" without touching the product
// wrapper. Kept because that bisection is exactly the failure mode a future
// bench session will hit again: any node-word readback other than
// FFFF-everywhere means the flash link is live; FFFF-everywhere means check
// the physical J4 wiring before suspecting the RTL.
module spu13_tang25k_spu4_som_edge_debug_probe (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx,
    output wire       flash_cs,
    output wire       flash_sck,
    output wire       flash_mosi,
    input  wire       flash_miso
);

    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) begin
        if (!rst_n) rst_cnt <= rst_cnt + 1;
    end

    localparam integer NUM_FEATURES = 4;
    localparam integer WIDTH        = 16;
    localparam integer NODE_W       = NUM_FEATURES * 2 * WIDTH;

    reg  start;
    wire busy, done;
    wire weight_we;
    wire [1:0] weight_node;
    wire [NODE_W-1:0] weight_data;

    spu4_som_flash_loader #(
        .NUM_FEATURES(NUM_FEATURES), .WIDTH(WIDTH)
    ) u_loader (
        .clk(sys_clk), .rst_n(rst_n),
        .start(start), .busy(busy), .done(done),
        .weight_we(weight_we), .weight_node(weight_node), .weight_data(weight_data),
        .flash_sclk(flash_sck), .flash_cs_n(flash_cs),
        .flash_mosi(flash_mosi), .flash_miso(flash_miso)
    );

    // Capture node 0's raw weight word as it lands (weight_we pulses once
    // per node, node-ascending -- node 0 is the first pulse).
    reg [NODE_W-1:0] node0_word;
    reg              node0_captured;
    always @(posedge sys_clk) begin
        if (!rst_n) begin
            node0_word     <= {NODE_W{1'b0}};
            node0_captured <= 1'b0;
        end else if (weight_we && weight_node == 2'd0 && !node0_captured) begin
            node0_word     <= weight_data;
            node0_captured <= 1'b1;
        end
    end

    // feature 0 in the low 32 bits, feature 3 in the high 32 bits -- same
    // convention spu4_som_edge.v itself uses.
    wire [15:0] f0_p = node0_word[31:16];
    wire [15:0] f0_q = node0_word[15:0];
    wire [15:0] f3_p = node0_word[127:112];
    wire [15:0] f3_q = node0_word[111:96];

    always @(posedge sys_clk) begin
        if (!rst_n) start <= 1'b0;
        else if (!busy && !done && !node0_captured) start <= 1'b1;
        else start <= 1'b0;
    end

    // ── UART (same single-owner pattern as the other probes) ──────────
    localparam CLK_FREQ = 50000000, CLKS_PER_BIT = 434;
    localparam START_DELAY = 50000000 / 2, LINE_PERIOD = 50000000 / 5;

    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits = 4'd0;
    reg [15:0] baud_cnt = 16'd0;
    reg        tx_busy = 1'b0;
    reg [7:0]  tx_byte = 8'd0;
    reg        tx_go = 1'b0;
    reg [27:0] line_timer = 28'd0;
    reg [27:0] start_cnt = 28'd0;
    reg        start_ready = 1'b0;
    reg [5:0]  msg_idx = 6'd0;
    reg        line_active = 1'b0;

    assign uart_tx = tx_shift[0];

    function [7:0] h;
        input [3:0] n;
        begin h = (n < 10) ? ("0" + n) : ("A" + n - 10); end
    endfunction

    function [7:0] msg_byte;
        input [5:0] idx;
        begin
            case (idx)
                6'd0:  msg_byte = "D";
                6'd1:  msg_byte = "B";
                6'd2:  msg_byte = "G";
                6'd3:  msg_byte = ":";
                6'd4:  msg_byte = node0_captured ? "C" : ".";
                6'd5:  msg_byte = " ";
                6'd6:  msg_byte = "P";
                6'd7:  msg_byte = "0";
                6'd8:  msg_byte = "=";
                6'd9:  msg_byte = h(f0_p[15:12]);
                6'd10: msg_byte = h(f0_p[11:8]);
                6'd11: msg_byte = h(f0_p[7:4]);
                6'd12: msg_byte = h(f0_p[3:0]);
                6'd13: msg_byte = " ";
                6'd14: msg_byte = "Q";
                6'd15: msg_byte = "0";
                6'd16: msg_byte = "=";
                6'd17: msg_byte = h(f0_q[15:12]);
                6'd18: msg_byte = h(f0_q[11:8]);
                6'd19: msg_byte = h(f0_q[7:4]);
                6'd20: msg_byte = h(f0_q[3:0]);
                6'd21: msg_byte = " ";
                6'd22: msg_byte = "P";
                6'd23: msg_byte = "3";
                6'd24: msg_byte = "=";
                6'd25: msg_byte = h(f3_p[15:12]);
                6'd26: msg_byte = h(f3_p[11:8]);
                6'd27: msg_byte = h(f3_p[7:4]);
                6'd28: msg_byte = h(f3_p[3:0]);
                6'd29: msg_byte = " ";
                6'd30: msg_byte = "Q";
                6'd31: msg_byte = "3";
                6'd32: msg_byte = "=";
                6'd33: msg_byte = h(f3_q[15:12]);
                6'd34: msg_byte = h(f3_q[11:8]);
                6'd35: msg_byte = h(f3_q[7:4]);
                6'd36: msg_byte = h(f3_q[3:0]);
                6'd37: msg_byte = " ";
                6'd38: msg_byte = "L";
                6'd39: msg_byte = "D";
                6'd40: msg_byte = "=";
                6'd41: msg_byte = done ? "1" : "0";
                6'd42: msg_byte = 8'h0D;
                6'd43: msg_byte = 8'h0A;
                default: msg_byte = 8'h20;
            endcase
        end
    endfunction

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            tx_shift <= 10'h3FF; tx_bits <= 4'd0; baud_cnt <= 16'd0;
            tx_busy <= 1'b0; tx_byte <= 8'd0; tx_go <= 1'b0;
            line_timer <= 28'd0; start_cnt <= 28'd0; start_ready <= 1'b0;
            msg_idx <= 6'd0; line_active <= 1'b0;
        end else begin
            if (tx_busy) begin
                if (baud_cnt < CLKS_PER_BIT - 1) begin
                    baud_cnt <= baud_cnt + 1'b1;
                end else begin
                    baud_cnt <= 16'd0;
                    tx_shift <= {1'b1, tx_shift[9:1]};
                    if (tx_bits == 1) begin
                        tx_busy <= 1'b0; tx_bits <= 4'd0;
                    end else begin
                        tx_bits <= tx_bits - 1'b1;
                    end
                end
            end else if (tx_go) begin
                tx_go <= 1'b0;
                tx_shift <= {1'b1, tx_byte, 1'b0};
                tx_bits <= 4'd10;
                tx_busy <= 1'b1;
                baud_cnt <= 16'd0;
            end else if (!start_ready) begin
                if (start_cnt < START_DELAY - 1) start_cnt <= start_cnt + 1'b1;
                else start_ready <= 1'b1;
            end else if (line_active) begin
                tx_byte <= msg_byte(msg_idx);
                tx_go <= 1'b1;
                if (msg_idx == 6'd43) begin
                    msg_idx <= 6'd0;
                    line_active <= 1'b0;
                end else begin
                    msg_idx <= msg_idx + 1'b1;
                end
            end else if (line_timer < LINE_PERIOD - 1) begin
                line_timer <= line_timer + 1'b1;
            end else begin
                line_timer <= 28'd0;
                msg_idx <= 6'd0;
                line_active <= 1'b1;
            end
        end
    end

    reg [24:0] blink;
    always @(posedge sys_clk) blink <= blink + 1;
    assign led[0] = ~blink[24];
    assign led[1] = ~node0_captured;
    assign led[2] = ~done;

endmodule
