// southbridge_spi_top.v — SPI slave + counter, no core, full CST ports
module spu13_tang25k_southbridge_top (
    input  wire        sys_clk,
    output wire [2:0]  led,
    input  wire        spi_cs_n, spi_sck, spi_mosi,
    output wire        spi_miso,
    output wire        uart_tx, uart_tx_telemetry,
    input  wire        uart_rx_telemetry, periph_rx,
    output wire        sdram_clk, sdram_cs_n, sdram_ras_n, sdram_cas_n, sdram_we_n,
    output wire [1:0]  sdram_ba,
    output wire        sdram_a0, sdram_a1, sdram_a2, sdram_a3,
    output wire        sdram_a4, sdram_a5, sdram_a6, sdram_a7,
    output wire        sdram_a8, sdram_a9, sdram_a10, sdram_a11, sdram_a12,
    inout  wire [15:0] sdram_dq,
    output wire [1:0]  sdram_dm
);
    assign uart_tx = 1'b1;
    assign uart_tx_telemetry = 1'b1;
    assign sdram_clk = 1'b0;
    assign sdram_cs_n = 1'b1;
    assign sdram_ras_n = 1'b1;
    assign sdram_cas_n = 1'b1;
    assign sdram_we_n = 1'b1;
    assign sdram_ba = 2'b00;
    assign sdram_a0 = 0; assign sdram_a1 = 0; assign sdram_a2 = 0; assign sdram_a3 = 0;
    assign sdram_a4 = 0; assign sdram_a5 = 0; assign sdram_a6 = 0; assign sdram_a7 = 0;
    assign sdram_a8 = 0; assign sdram_a9 = 0; assign sdram_a10 = 0; assign sdram_a11 = 0; assign sdram_a12 = 0;
    assign sdram_dq = 16'hZZZZ;
    assign sdram_dm = 2'b00;

    wire clk_50m;
    BUFG u_bufg (.I(sys_clk), .O(clk_50m));

    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge clk_50m) if (rst_cnt != 8'hFF) rst_cnt <= rst_cnt + 1;

    wire        rplu_cfg_wr_en;
    wire [2:0]  rplu_cfg_sel;
    wire [7:0]  rplu_cfg_material;
    wire [9:0]  rplu_cfg_addr;
    wire [63:0] rplu_cfg_data;
    wire        inst_valid;
    wire [63:0] inst_word;

    reg [25:0] cnt = 0;
    reg [19:0] spi_led_stretch = 0;
    always @(posedge clk_50m) begin
        cnt <= cnt + 1;
        if (rplu_cfg_wr_en || inst_valid) begin
            spi_led_stretch <= 20'hFFFFF;
        end else if (|spi_led_stretch) begin
            spi_led_stretch <= spi_led_stretch - 1'b1;
        end
    end
    assign led[0] = ~cnt[24];
    assign led[1] = ~cnt[23];
    assign led[2] = ~(|spi_led_stretch);

    reg [15:0] rplu_cfg_count = 0;
    reg [31:0] rplu_cfg_checksum = 0;
    reg [2:0]  rplu_cfg_sel_last = 0;
    reg [7:0]  rplu_cfg_material_last = 0;
    reg [9:0]  rplu_cfg_addr_last = 0;
    reg [63:0] rplu_cfg_data_last = 0;

    function [31:0] cfg_checksum_next;
        input [31:0] prev;
        input [2:0]  sel;
        input [7:0]  material;
        input [9:0]  addr;
        input [63:0] data;
        reg   [31:0] mixed_header;
        begin
            mixed_header = {8'hA5, 5'd0, sel, material, 6'd0, addr};
            cfg_checksum_next = {prev[30:0], prev[31]} ^
                                mixed_header ^
                                data[63:32] ^
                                data[31:0];
        end
    endfunction

    always @(posedge clk_50m or negedge rst_n) begin
        if (!rst_n) begin
            rplu_cfg_count <= 16'd0;
            rplu_cfg_checksum <= 32'd0;
            rplu_cfg_sel_last <= 3'd0;
            rplu_cfg_material_last <= 8'd0;
            rplu_cfg_addr_last <= 10'd0;
            rplu_cfg_data_last <= 64'd0;
        end else if (rplu_cfg_wr_en) begin
            rplu_cfg_count <= rplu_cfg_count + 16'd1;
            rplu_cfg_checksum <= cfg_checksum_next(rplu_cfg_checksum,
                                                   rplu_cfg_sel,
                                                   rplu_cfg_material,
                                                   rplu_cfg_addr,
                                                   rplu_cfg_data);
            rplu_cfg_sel_last <= rplu_cfg_sel;
            rplu_cfg_material_last <= rplu_cfg_material;
            rplu_cfg_addr_last <= rplu_cfg_addr;
            rplu_cfg_data_last <= rplu_cfg_data;
        end
    end

    wire [511:0] southbridge_telemetry = {
        32'h53505543,                  // "SPUC"
        rplu_cfg_count,
        {5'd0, rplu_cfg_sel_last},
        rplu_cfg_material_last,
        {6'd0, rplu_cfg_addr_last},
        rplu_cfg_data_last[63:16],
        rplu_cfg_data_last[15:0],
        rplu_cfg_checksum,
        16'd0,
        320'd0
    };

    spu_spi_slave u_spi (
        .clk(clk_50m), .rst_n(rst_n),
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck),
        .spi_mosi(spi_mosi), .spi_miso(spi_miso),
        .manifold_state(832'd0),
        .satellite_snaps(4'd0),
        .is_janus_point(1'b0),
        .dissonance(16'd0),
        .scale_table(52'd0),
        .scale_overflow(13'd0),
        .qr_commit_valid(1'b0), .qr_commit_lane(4'd0),
        .qr_commit_A(64'd0), .qr_commit_B(64'd0),
        .qr_commit_C(64'd0), .qr_commit_D(64'd0),
        .hex_valid(1'b0), .hex_q(16'd0), .hex_r(16'd0),
        .rplu_ratio_res(3'sd0), .rplu_ratio_valid(1'b0),
        .rplu_cfg_wr_en(rplu_cfg_wr_en),
        .rplu_cfg_sel(rplu_cfg_sel),
        .rplu_cfg_material(rplu_cfg_material),
        .rplu_cfg_addr(rplu_cfg_addr),
        .rplu_cfg_data(rplu_cfg_data),
        .inst_valid(inst_valid), .inst_word(inst_word),
        .fifo_full(1'b0),
        .laminar_index(16'h25a5),
        .turbulence(1'b0), .rplu_mode(1'b0),
        .boot_ready(1'b1),  // no boot FSM in this top — always ready
        .sentinel_telemetry(southbridge_telemetry)
    );
endmodule

(* blackbox *)
module BUFG (input wire I, output wire O);
endmodule
