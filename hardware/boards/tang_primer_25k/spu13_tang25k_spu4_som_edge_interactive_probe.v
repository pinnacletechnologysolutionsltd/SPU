// spu13_tang25k_spu4_som_edge_interactive_probe.v -- Tang 25K interactive
// bench probe for the SPU-4 edge SOM product, spu4_som_edge_wrapper
// (Track B, plan: knowledge/spu4-edge-node-focus + the interactive-probe
// design pass this file implements).
//
// Unlike spu13_tang25k_spu4_som_edge_probe.v (the fixed self-test probe,
// already silicon-proven, docs/hardware_evidence.md 3.2j.7), which drives
// exactly one hard-coded query forever, this probe lets a host submit an
// ARBITRARY 4-feature vector over UART and get back a live classification
// from the real, unmodified spu4_som_edge_wrapper -- a genuine
// query/response interface for development/demo use, not a networked
// runtime interface for the shipped product (which stays local-pins-only
// per the 2026-08-17 decision spu4_som_edge_wrapper.v's own header cites).
//
// ── What must be flashed before this probe means anything ────────────────
// Same PMOD J4 SPI flash path as the fixed probe. Use `--profile demo`
// (tools/gen_spu4_som_boot_image.py) for Track B work ahead of real
// trained weights, or `--profile oracle_fixture` to sanity-check against
// the same fixture spu4_som_edge_interactive_probe_tb.v and
// spu4_som_edge_full_chain_tb.v both check.
//
// ── Query grammar (host -> probe, ASCII, 34 bytes incl. terminator) ──────
//   Q<f0P><f0Q><f1P><f1Q><f2P><f2Q><f3P><f3Q>\n
// Each field is 4 hex digits, two's-complement 16-bit, upper or lower
// case accepted. Field order matches spu4_som_edge_full_chain_tb.v's
// pack4() argument order -- feature 0 first. A non-hex byte mid-field, or
// anything other than '\n' where the terminator is expected, aborts the
// line and reports 'F' -- no wrapper interaction for a malformed query.
// The RX line-assembler resyncs on the next 'Q' regardless of what came
// before it, so a burst of garbage self-heals without a reset.
//
// ── Result line (probe -> host) -- SAME 40-byte layout as the fixed probe,
// reusing spu13_tang25k_spu4_som_edge_probe.v's msg_byte()/h() verbatim,
// so host-side parsing code (software/lib/spu4_som_probe_parser.py) is
// shared between both probes:
//   SOM:H N=x Q=xxxxxxxx S=xx L=xxx I=xxxx\r\n   -- boot hydration done
//   SOM:D N=x Q=xxxxxxxx S=xx L=xxx I=xxxx\r\n   -- classification done
//   SOM:F N=x Q=xxxxxxxx S=xx L=xxx I=xxxx\r\n   -- malformed query (or,
//                                                   defensively, a
//                                                   classification that
//                                                   never asserted `done`)
// One result line per accepted query -- no periodic repeat, unlike the
// fixed probe, so host-side query/response pairing stays trivial.
//
// ── Known simplification (documented, not a bug) ──────────────────────
// The dispatch FSM only samples the RX line-assembler's line-complete/
// malformed pulses while idle (S_IDLE). A query sent while a previous
// classification is still in flight is silently dropped -- matching this
// probe's "one query, one response" scope. A host should wait for a
// result line before sending the next query.

module spu13_tang25k_spu4_som_edge_interactive_probe #(
    parameter CLK_FREQ     = 50000000,
    parameter CLKS_PER_BIT = 434,             // 115200 baud at 50 MHz
    parameter RUN_TIMEOUT  = 32'd10_000_000   // defensive safety net only;
                                               // the ABI's own bounded-latency
                                               // guarantee should never trip it
) (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx,
    input  wire        uart_rx,

    // PMOD J4 SPI flash -- same chip/pins as the fixed probe.
    output wire        flash_cs,
    output wire        flash_sck,
    output wire        flash_mosi,
    input  wire        flash_miso
);

    // ── Reset ────────────────────────────────────────────────────────
    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) begin
        if (!rst_n) rst_cnt <= rst_cnt + 1;
    end

    // ── The module under test: the SOM edge-node customer wrapper ────
    // Unmodified -- v1.0 frozen contract, this probe wraps it, never
    // changes it.
    reg         start;
    reg [127:0] features_reg;
    wire        busy, done;
    wire [1:0]  best_node;
    wire [31:0] best_quadrance;
    wire [7:0]  status;
    wire [15:0] id;

    spu4_som_edge_wrapper #(
        .NUM_FEATURES(4), .WIDTH(16)
    ) u_som (
        .clk(sys_clk), .rst_n(rst_n),
        .start(start), .busy(busy), .done(done),
        .features(features_reg),
        .best_node(best_node), .best_quadrance(best_quadrance),
        .status(status), .id(id),
        .flash_sclk(flash_sck), .flash_cs_n(flash_cs),
        .flash_mosi(flash_mosi), .flash_miso(flash_miso)
    );

    // ── UART RX: bytes in ──────────────────────────────────────────────
    wire       rx_byte_valid;
    wire [7:0] rx_byte;

    spu4_uart_rx_bitsync #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_rx (
        .clk(sys_clk), .rst_n(rst_n), .rx(uart_rx),
        .rx_byte_valid(rx_byte_valid), .rx_byte(rx_byte)
    );

    function is_hex_digit;
        input [7:0] b;
        begin
            is_hex_digit = (b >= "0" && b <= "9") ||
                           (b >= "A" && b <= "F") ||
                           (b >= "a" && b <= "f");
        end
    endfunction

    function [3:0] hex_nibble;
        input [7:0] b;
        begin
            if (b >= "0" && b <= "9")      hex_nibble = b - "0";
            else if (b >= "A" && b <= "F") hex_nibble = b - "A" + 4'd10;
            else                           hex_nibble = b - "a" + 4'd10;
        end
    endfunction

    // ── Line assembler: bytes -> one query line ─────────────────────
    localparam LA_WAIT_Q    = 2'd0;
    localparam LA_FIELD     = 2'd1;
    localparam LA_EXPECT_NL = 2'd2;

    reg [1:0]   la_state;
    reg [2:0]   field_idx;        // 0..7: which field (f0P..f3Q)
    reg [1:0]   nibble_in_field;  // 0..3
    reg [15:0]  field_val;
    reg [127:0] assembled_features;
    reg         line_complete_pulse;
    reg         malformed_pulse;

    wire [15:0] field_val_next = {field_val[11:0], hex_nibble(rx_byte)};

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            la_state            <= LA_WAIT_Q;
            field_idx           <= 3'd0;
            nibble_in_field      <= 2'd0;
            field_val            <= 16'd0;
            assembled_features   <= 128'd0;
            line_complete_pulse  <= 1'b0;
            malformed_pulse      <= 1'b0;
        end else begin
            line_complete_pulse <= 1'b0;   // one-cycle pulses, default low
            malformed_pulse     <= 1'b0;

            if (rx_byte_valid) begin
                case (la_state)
                    LA_WAIT_Q: begin
                        // Any byte that isn't 'Q' is ignored, not an
                        // error -- this is how the assembler resyncs
                        // after a prior abort without needing a reset.
                        if (rx_byte == "Q") begin
                            field_idx       <= 3'd0;
                            nibble_in_field <= 2'd0;
                            la_state        <= LA_FIELD;
                        end
                    end
                    LA_FIELD: begin
                        if (is_hex_digit(rx_byte)) begin
                            field_val <= field_val_next;
                            if (nibble_in_field == 2'd3) begin
                                nibble_in_field <= 2'd0;
                                case (field_idx)
                                    3'd0: assembled_features[31:16]   <= field_val_next; // f0P
                                    3'd1: assembled_features[15:0]    <= field_val_next; // f0Q
                                    3'd2: assembled_features[63:48]   <= field_val_next; // f1P
                                    3'd3: assembled_features[47:32]   <= field_val_next; // f1Q
                                    3'd4: assembled_features[95:80]   <= field_val_next; // f2P
                                    3'd5: assembled_features[79:64]   <= field_val_next; // f2Q
                                    3'd6: assembled_features[127:112] <= field_val_next; // f3P
                                    3'd7: assembled_features[111:96]  <= field_val_next; // f3Q
                                endcase
                                if (field_idx == 3'd7) la_state <= LA_EXPECT_NL;
                                else                    field_idx <= field_idx + 1'b1;
                            end else begin
                                nibble_in_field <= nibble_in_field + 1'b1;
                            end
                        end else begin
                            la_state        <= LA_WAIT_Q;
                            malformed_pulse <= 1'b1;
                        end
                    end
                    LA_EXPECT_NL: begin
                        la_state <= LA_WAIT_Q;
                        if (rx_byte == 8'h0A) line_complete_pulse <= 1'b1;
                        else                  malformed_pulse     <= 1'b1;
                    end
                    default: la_state <= LA_WAIT_Q;
                endcase
            end
        end
    end

    // ── Dispatch FSM: boot wait -> idle -> launch -> run -> emit ────
    localparam S_WAIT_BOOT  = 3'd0;
    localparam S_IDLE       = 3'd1;
    localparam S_LAUNCH     = 3'd2;
    localparam S_RUN        = 3'd3;
    localparam S_EMIT_PULSE = 3'd4;
    localparam S_EMIT_WAIT  = 3'd5;

    reg [2:0]  dispatch_state;
    reg [2:0]  emit_return_state;
    reg [7:0]  line_ch;           // status char for the next/last emitted line
    reg [11:0] latency;           // clocks, saturating at 0xFFF
    reg [31:0] run_timeout_cnt;

    wire emit_line_req = (dispatch_state == S_EMIT_PULSE);

    // TX engine registers, declared here (ahead of the dispatch FSM below
    // that reads line_active/tx_busy/tx_go) so both always blocks can see
    // them regardless of declaration-order sensitivity -- the TX engine
    // itself is defined further down, copy-adapted from
    // spu13_tang25k_spu4_som_edge_probe.v's single-owner engine.
    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits = 4'd0;
    reg [15:0] baud_cnt = 16'd0;
    reg        tx_busy = 1'b0;
    reg [7:0]  tx_byte = 8'd0;
    reg        tx_go = 1'b0;
    reg [5:0]  msg_idx = 6'd0;
    reg        line_active = 1'b0;

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            dispatch_state    <= S_WAIT_BOOT;
            emit_return_state <= S_IDLE;
            start             <= 1'b0;
            features_reg      <= 128'd0;
            line_ch           <= ".";
            latency           <= 12'd0;
            run_timeout_cnt   <= 32'd0;
        end else begin
            start <= 1'b0;   // one-cycle pulse, default low
            case (dispatch_state)
                S_WAIT_BOOT: begin
                    if (!busy) begin
                        line_ch           <= "H";
                        dispatch_state    <= S_EMIT_PULSE;
                        emit_return_state <= S_IDLE;
                    end
                end
                S_IDLE: begin
                    if (line_complete_pulse) begin
                        features_reg   <= assembled_features;
                        latency        <= 12'd0;
                        run_timeout_cnt <= 32'd0;
                        dispatch_state <= S_LAUNCH;
                    end else if (malformed_pulse) begin
                        line_ch           <= "F";
                        dispatch_state    <= S_EMIT_PULSE;
                        emit_return_state <= S_IDLE;
                    end
                end
                S_LAUNCH: begin
                    start          <= 1'b1;   // one-cycle start pulse
                    dispatch_state <= S_RUN;
                end
                S_RUN: begin
                    if (done) begin
                        line_ch           <= "D";
                        dispatch_state    <= S_EMIT_PULSE;
                        emit_return_state <= S_IDLE;
                    end else if (run_timeout_cnt > RUN_TIMEOUT) begin
                        // Defensive only -- see file header. The ABI's own
                        // bounded-latency guarantee should make this dead
                        // code in practice.
                        line_ch           <= "F";
                        dispatch_state    <= S_EMIT_PULSE;
                        emit_return_state <= S_IDLE;
                    end else begin
                        if (latency != 12'hFFF) latency <= latency + 1'b1;
                        run_timeout_cnt <= run_timeout_cnt + 1'b1;
                    end
                end
                S_EMIT_PULSE: begin
                    // emit_line_req is combinational off this state --
                    // exactly one cycle, then unconditionally move on.
                    dispatch_state <= S_EMIT_WAIT;
                end
                S_EMIT_WAIT: begin
                    // Wait for the ENTIRE line (all 40 bytes) to finish
                    // clocking out, not just line_active dropping --
                    // line_active can go low one byte before tx_busy/
                    // tx_go finish draining the final LF, and starting a
                    // new emit before that would corrupt the UART stream.
                    if (!line_active && !tx_busy && !tx_go)
                        dispatch_state <= emit_return_state;
                end
                default: dispatch_state <= S_WAIT_BOOT;
            endcase
        end
    end

    // ── UART TX + status line (copy-adapted from
    // spu13_tang25k_spu4_som_edge_probe.v's single-owner engine: h(),
    // msg_byte()'s case structure, and the baud-rate shift register are
    // reused verbatim; only the line_active trigger changes, from a
    // periodic timer to emit_line_req above; registers declared above,
    // ahead of the dispatch FSM) ───────────────────────────────────────
    assign uart_tx = tx_shift[0];

    function [7:0] h;
        input [3:0] n;
        begin h = (n < 10) ? ("0" + n) : ("A" + n - 10); end
    endfunction

    function [7:0] msg_byte;
        input [5:0] idx;
        begin
            case (idx)
                6'd0:  msg_byte = "S";
                6'd1:  msg_byte = "O";
                6'd2:  msg_byte = "M";
                6'd3:  msg_byte = ":";
                6'd4:  msg_byte = line_ch;
                6'd5:  msg_byte = " ";
                6'd6:  msg_byte = "N";
                6'd7:  msg_byte = "=";
                6'd8:  msg_byte = h({2'b00, best_node});
                6'd9:  msg_byte = " ";
                6'd10: msg_byte = "Q";
                6'd11: msg_byte = "=";
                6'd12: msg_byte = h(best_quadrance[31:28]);
                6'd13: msg_byte = h(best_quadrance[27:24]);
                6'd14: msg_byte = h(best_quadrance[23:20]);
                6'd15: msg_byte = h(best_quadrance[19:16]);
                6'd16: msg_byte = h(best_quadrance[15:12]);
                6'd17: msg_byte = h(best_quadrance[11:8]);
                6'd18: msg_byte = h(best_quadrance[7:4]);
                6'd19: msg_byte = h(best_quadrance[3:0]);
                6'd20: msg_byte = " ";
                6'd21: msg_byte = "S";
                6'd22: msg_byte = "=";
                6'd23: msg_byte = h(status[7:4]);
                6'd24: msg_byte = h(status[3:0]);
                6'd25: msg_byte = " ";
                6'd26: msg_byte = "L";
                6'd27: msg_byte = "=";
                6'd28: msg_byte = h(latency[11:8]);
                6'd29: msg_byte = h(latency[7:4]);
                6'd30: msg_byte = h(latency[3:0]);
                6'd31: msg_byte = " ";
                6'd32: msg_byte = "I";
                6'd33: msg_byte = "=";
                6'd34: msg_byte = h(id[15:12]);
                6'd35: msg_byte = h(id[11:8]);
                6'd36: msg_byte = h(id[7:4]);
                6'd37: msg_byte = h(id[3:0]);
                6'd38: msg_byte = 8'h0D;
                6'd39: msg_byte = 8'h0A;
                default: msg_byte = 8'h20;
            endcase
        end
    endfunction

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            tx_shift <= 10'h3FF; tx_bits <= 4'd0; baud_cnt <= 16'd0;
            tx_busy <= 1'b0; tx_byte <= 8'd0; tx_go <= 1'b0;
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
            end else if (line_active) begin
                tx_byte <= msg_byte(msg_idx);
                tx_go <= 1'b1;
                if (msg_idx == 6'd39) begin
                    msg_idx <= 6'd0;
                    line_active <= 1'b0;
                end else begin
                    msg_idx <= msg_idx + 1'b1;
                end
            end else if (emit_line_req) begin
                msg_idx <= 6'd0;
                line_active <= 1'b1;
            end
        end
    end

    // ── LEDs ─────────────────────────────────────────────────────────
    reg [24:0] blink;
    always @(posedge sys_clk) blink <= blink + 1;
    assign led[0] = ~blink[24];
    assign led[1] = ~(line_ch == "D");
    assign led[2] = ~(line_ch == "F");

endmodule
