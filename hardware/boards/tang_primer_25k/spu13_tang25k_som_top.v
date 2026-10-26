// spu13_tang25k_som_top.v — 25K SOM Probe (50 MHz version)
// Tests SOM_CLASSIFY + SOM_TRAIN with sequencer-driven .sas program.
// UART telemetry at 115200 baud on uart_tx.

module spu13_tang25k_som_top (
    input  wire        sys_clk,     // 50 MHz (Tang 25K crystal)
    output reg         uart_tx,
    output wire [2:0]  led
);

    // ── Clock divider: 50 MHz → ~6.25 MHz core ────────────────────
    wire clk_core;
    reg [2:0] clk_div = 0;
    always @(posedge sys_clk) clk_div <= clk_div + 1;
    assign clk_core = clk_div[2];

    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge clk_core) if (rst_cnt != 8'hFF) rst_cnt <= rst_cnt + 1;

    wire        inst_valid, inst_done;
    wire [63:0] inst_word;
    wire        hex_valid;
    wire [15:0] hex_q, hex_r;

    // ── CDC: hex_valid from clk_core (6.25 MHz) → sys_clk (50 MHz) ──
    reg         hex_valid_core_r;
    reg         hex_valid_sync_0, hex_valid_sync_1;
    wire        hex_valid_rise;

    always @(posedge clk_core or negedge rst_n) begin
        if (!rst_n) hex_valid_core_r <= 0;
        else if (hex_valid) hex_valid_core_r <= ~hex_valid_core_r;  // toggle
    end

    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n) begin
            hex_valid_sync_0 <= 0;
            hex_valid_sync_1 <= 0;
        end else begin
            hex_valid_sync_0 <= hex_valid_core_r;
            hex_valid_sync_1 <= hex_valid_sync_0;
        end
    end

    reg hex_valid_sync_prev = 0;
    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n) hex_valid_sync_prev <= 0;
        else hex_valid_sync_prev <= hex_valid_sync_1;
    end
    assign hex_valid_rise = (hex_valid_sync_1 != hex_valid_sync_prev);

    spu_sequencer #(.IMEM_DEPTH(64)) u_seq (
        .clk(clk_core), .rst_n(rst_n), .boot_done(1'b1),
        .inst_valid(inst_valid), .inst_word(inst_word),
        .inst_done(inst_done), .pc_out(), .halted(), .program_size()
    );

    spu13_core #(
        .DEVICE("GW5A"), .ENABLE_RPLU(0), .ENABLE_LATTICE(0),
        .ENABLE_MATH(0), .ENABLE_SEQUENCER(0), .ENABLE_CORE_SOM(1)
    ) u_core (
        .clk(clk_core), .rst_n(rst_n),
        .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .dec_fast_cfg_wr_en(1'b0), .dec_fast_cfg_sel(3'd0),
        .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(10'd0),
        .dec_fast_cfg_data(64'd0), .phinary_cfg(16'h000C),
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
        .axiomatic_fault(), .fault_type(), .fault_count(),
        .rns_error(),
        .ecc_single_err(),
        .ecc_double_err()
    );

    // Simple UART TX at 115200 baud from 50 MHz
    // 50 MHz / 115200 / 2 ≈ 217
    reg [31:0] uart_data;
    reg        uart_busy;
    reg [15:0] uart_div;
    reg [3:0]  uart_bit;

    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n) begin
            uart_tx   <= 1'b1;
            uart_busy <= 0;
            uart_div  <= 0;
            uart_bit  <= 0;
        end else begin
            if (hex_valid_rise && !uart_busy) begin
                uart_data <= {16'hAAAA, hex_q};
                uart_busy <= 1;
                uart_div  <= 0;
                uart_bit  <= 0;
                uart_tx   <= 1'b0;  // start bit
            end else if (uart_busy) begin
                uart_div <= uart_div + 1;
                if (uart_div == 16'd217) begin  // 50M / 115200 / 2
                    uart_div <= 0;
                    uart_bit <= uart_bit + 1;
                    if (uart_bit < 8)
                        uart_tx <= uart_data[uart_bit];
                    else if (uart_bit == 8)
                        uart_tx <= 1'b1;  // stop bit
                    else
                        uart_busy <= 0;
                end
            end
        end
    end

    // LED: heartbeat
    reg [24:0] blink;
    always @(posedge sys_clk) blink <= blink + 1;
    assign led[0] = ~blink[24];
    assign led[1] = ~(|blink[24:23]);
    assign led[2] = ~blink[23];

endmodule
