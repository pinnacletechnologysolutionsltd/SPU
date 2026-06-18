// spu13_tang25k_som_top.v — 25K Minimal SOM Probe
// Tests SOM_CLASSIFY + SOM_TRAIN with sequencer-driven .sas program.
// UART telemetry at 115200 baud on uart_tx.

module spu13_tang25k_som_top (
    input  wire        sys_clk,     // 27 MHz onboard
    input  wire        rst_n,       // BTN1 (active low)
    output wire        uart_tx,
    output wire [2:0]  led
);

    wire        inst_valid, inst_done;
    wire [63:0] inst_word;
    wire        hex_valid;
    wire [15:0] hex_q, hex_r;

    spu_sequencer #(.IMEM_DEPTH(64)) u_seq (
        .clk(sys_clk), .rst_n(rst_n), .boot_done(1'b1),
        .inst_valid(inst_valid), .inst_word(inst_word),
        .inst_done(inst_done), .pc_out(), .halted(), .program_size()
    );

    spu13_core #(
        .DEVICE("GW5A"), .ENABLE_RPLU(0), .ENABLE_LATTICE(0),
        .ENABLE_MATH(0), .ENABLE_SEQUENCER(0), .ENABLE_CORE_SOM(1)
    ) u_core (
        .clk(sys_clk), .rst_n(rst_n),
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
    );

    // Simple UART TX (same as math probe)
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
            if (hex_valid && !uart_busy) begin
                uart_data <= {16'hAAAA, hex_q};
                uart_busy <= 1;
                uart_div  <= 0;
                uart_bit  <= 0;
                uart_tx   <= 1'b0;  // start bit
            end else if (uart_busy) begin
                uart_div <= uart_div + 1;
                if (uart_div == 16'd117) begin  // 27M / 115200 / 2
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


endmodule
