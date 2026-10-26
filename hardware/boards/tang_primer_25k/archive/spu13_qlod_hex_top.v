// spu13_qlod_hex_top.v — Proven UART (from blink test) + core + sequencer
module spu13_qlod_hex_top (
    input  wire        sys_clk,
    output reg         uart_tx,
    output wire [2:0]  led
);

    // ── Core clock: 50 MHz → 6.25 MHz ──────────────────────────────
    wire clk_core;
    reg [2:0] clk_div = 0;
    always @(posedge sys_clk) clk_div <= clk_div + 1;
    assign clk_core = clk_div[2];

    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge clk_core) if (rst_cnt != 8'hFF) rst_cnt <= rst_cnt + 1;

    // ── Sequencer ──────────────────────────────────────────────────
    reg        inst_valid;
    reg [63:0] inst_word;
    wire       inst_done;
    reg [2:0]  seq;

    always @(posedge clk_core or negedge rst_n) begin
        if (!rst_n) begin seq <= 0; inst_valid <= 0; inst_word <= 0; end
        else begin
            inst_valid <= 0;
            case (seq)
                0: seq <= 1;
                1: begin inst_valid <= 1; inst_word <= 64'h1d_00_78_56_34_12_00_00; seq <= 2; end
                2: if (inst_done) seq <= 3;
                3: begin inst_valid <= 1; inst_word <= 64'h16_00_00_00_00_00_00_00; seq <= 4; end
                4: if (inst_done) seq <= 5;
                5: ;
            endcase
        end
    end

    // ── Core ────────────────────────────────────────────────────────
    wire        hex_valid;
    wire [15:0] hex_q, hex_r;
    spu13_core #(
        .DEVICE("GW5A"), .ENABLE_RPLU(0), .ENABLE_LATTICE(0),
        .ENABLE_MATH(0), .ENABLE_SEQUENCER(0), .ENABLE_CORE_SOM(0)
    ) u_core (
        .clk(clk_core), .rst_n(rst_n),
        .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .dec_fast_cfg_wr_en(1'b0), .dec_fast_cfg_sel(3'd0),
        .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(10'd0),
        .dec_fast_cfg_data(64'd0), .phinary_cfg(16'h0001),
        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),
        .boot_done(1'b1), .pell_data(32'd0), .pell_addr(3'd0),
        .pell_we(1'b0), .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
        .mem_ready(1'b1), .mem_burst_rd(), .mem_burst_wr(),
        .mem_addr(), .mem_rd_manifold(832'd0), .mem_wr_manifold(),
        .mem_burst_done(1'b0),
        .artery_wr_en(), .artery_wr_data(),
        .current_axis_ptr(), .current_axis_data(),
        .inst_valid(inst_valid), .inst_word(inst_word), .inst_done(inst_done),
        .ratio_cmp_res(), .ratio_cmp_valid(),
        .manifold_out(), .bloom_complete(), .scale_table_out(),
        .scale_overflow_out(), .is_janus_point(),
        .audio_mode(), .gasket_sum_out(), .quadrance_out(), .cycle_wrap(),
        .rplu_dissoc_out(), .rplu_dissoc_mask_out(), .rplu_addr_out(),
        .i2s_bclk(), .i2s_lrclk(), .i2s_dout(),
        .laminar_flow_index_out(), .thermal_pressure_out(),
        .hex_valid(hex_valid), .hex_q(hex_q), .hex_r(hex_r),
        .audio_p_out(), .audio_q_out(),
        .axiomatic_fault(), .fault_type(), .fault_count()
    );

    // ── hex_rise CDC with latch ─────────────────────────────────────
    reg  hex_tog;
    reg  hex_s0, hex_s1, hex_p;
    wire hex_rise;
    reg  hex_pending;  // latched: 1 = hex data available to send
    reg [15:0] hex_q_latched;

    always @(posedge clk_core) if (hex_valid) hex_tog <= ~hex_tog;
    always @(posedge sys_clk) begin hex_s0 <= hex_tog; hex_s1 <= hex_s0; hex_p <= hex_s1; end
    assign hex_rise = (hex_s1 != hex_p);

    always @(posedge sys_clk) begin
        if (hex_rise) begin
            hex_pending <= 1'b1;
            hex_q_latched <= hex_q;
        end else if (!tx_busy && hex_pending) begin
            hex_pending <= 1'b0;
        end
    end

    // ── UART TX — EXACT same pattern as working blink test ──────────
    localparam CLKS_PER_BIT = 50000000 / 115200;
    localparam MSG_PERIOD   = 50000000;

    // ── Power-on reset for UART domain (50 MHz) ────────────────────
    reg [15:0] uart_rst_cnt = 0;
    wire uart_rst_n = (uart_rst_cnt == 16'hFFFF);
    always @(posedge sys_clk) if (!uart_rst_n) uart_rst_cnt <= uart_rst_cnt + 1;

    reg [31:0] msg_timer;
    reg [7:0]  tx_byte;
    reg        tx_busy;
    reg [15:0] baud_cnt;
    reg [3:0]  bit_cnt;
    reg [3:0]  char_idx;
    reg [3:0]  msg_sel;

    function [7:0] hxd;
        input [3:0] v;
        begin hxd = (v < 10) ? (8'h30 + v) : (8'h41 + v - 10); end
    endfunction

    always @(posedge sys_clk) begin
        if (!uart_rst_n) begin
            msg_timer <= 0;
            tx_busy <= 0;
            baud_cnt <= 0;
            bit_cnt <= 0;
            char_idx <= 0;
            msg_sel <= 0;
            uart_tx <= 1'b1;
        end else begin
            msg_timer <= msg_timer + 1;
            if (msg_timer == 49999999) msg_timer <= 0;
            if (tx_busy) begin
                baud_cnt <= baud_cnt + 1;
                if (baud_cnt == 16'd433) begin  // 50M/115200 - 1
                    baud_cnt <= 0;
                    bit_cnt <= bit_cnt + 1;
                    if (bit_cnt < 8)
                        uart_tx <= tx_byte[bit_cnt];
                    else if (bit_cnt == 8)
                        uart_tx <= 1'b1;  // stop bit
                    else
                        tx_busy <= 0;
                end
            end else if (msg_timer == 49999999 && msg_sel == 0) begin
            // Banner: "QH\r\n"
            case (char_idx)
                0: tx_byte <= "Q";
                1: tx_byte <= "H";
                2: tx_byte <= 8'h0D;
                3: tx_byte <= 8'h0A;
                default: tx_byte <= " ";
            endcase
            uart_tx <= 1'b0;
            tx_busy <= 1;
            baud_cnt <= 0;
            bit_cnt <= 0;
            if (char_idx < 3) char_idx <= char_idx + 1;
            else begin
                char_idx <= 0;
                msg_sel <= 1;  // banner done, switch to hex
            end
        end else if (!tx_busy && hex_pending && msg_sel == 1) begin
            // Send hex_q_latched digits
            case (char_idx)
                0: tx_byte <= hxd(hex_q_latched[15:12]);
                1: tx_byte <= hxd(hex_q_latched[11:8]);
                2: tx_byte <= hxd(hex_q_latched[7:4]);
                3: tx_byte <= hxd(hex_q_latched[3:0]);
                4: tx_byte <= 8'h0D;
                5: tx_byte <= 8'h0A;
                default: tx_byte <= " ";
            endcase
            uart_tx <= 1'b0;
            tx_busy <= 1;
            baud_cnt <= 0;
            bit_cnt <= 0;
            if (char_idx < 5) char_idx <= char_idx + 1;
            end
        end
    end

    reg [24:0] blink;
    always @(posedge sys_clk) blink <= blink + 1;
    assign led[0] = ~blink[24];
    assign led[1] = ~hex_rise;
    assign led[2] = ~tx_busy;
endmodule
