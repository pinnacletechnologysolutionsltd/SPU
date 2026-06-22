// Tang Primer 25K RP2350 southbridge electrical/clock smoke probe.
// Keeps the production southbridge pinout while excluding the SPU datapath.
module spu13_tang25k_southbridge_smoke_top (
    input  wire       sys_clk,
    input  wire       spi_cs_n,
    input  wire       spi_sck,
    input  wire       spi_mosi,
    output wire       spi_miso
);
    reg [25:0] heartbeat = 0;
    always @(posedge sys_clk) begin
        heartbeat <= heartbeat + 1'b1;
    end

    reg [7:0] rst_count = 0;
    always @(posedge sys_clk) begin
        if (rst_count != 8'hff)
            rst_count <= rst_count + 1'b1;
    end
    wire rst_n = (rst_count == 8'hff);

    wire        rplu_cfg_wr_en;
    wire [2:0]  rplu_cfg_sel;
    wire [7:0]  rplu_cfg_material;
    wire [9:0]  rplu_cfg_addr;
    wire [63:0] rplu_cfg_data;
    wire        inst_valid;
    wire [63:0] inst_word;
    wire        spi_miso_internal;

    reg cs_seen = 0;
    reg sck_seen = 0;
    reg mosi_seen = 0;
    reg spi_sck_last = 0;
    always @(posedge sys_clk) begin
        spi_sck_last <= spi_sck;
        if (!spi_cs_n) begin
            cs_seen <= 1'b1;
            if (spi_sck != spi_sck_last)
                sck_seen <= 1'b1;
            if (spi_mosi)
                mosi_seen <= 1'b1;
        end
    end

    assign spi_miso = spi_miso_internal;

    spu_spi_slave u_spi (
        .clk(sys_clk),
        .rst_n(rst_n),
        .spi_cs_n(spi_cs_n),
        .spi_sck(spi_sck),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso_internal),
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
        .rplu_ratio_res(3'sd0),
        .rplu_ratio_valid(1'b0),
        .rplu_cfg_wr_en(rplu_cfg_wr_en),
        .rplu_cfg_sel(rplu_cfg_sel),
        .rplu_cfg_material(rplu_cfg_material),
        .rplu_cfg_addr(rplu_cfg_addr),
        .rplu_cfg_data(rplu_cfg_data),
        .inst_valid(inst_valid),
        .inst_word(inst_word),
        .fifo_full(1'b0),
        .laminar_index(16'h25a5),
        .turbulence(1'b0),
        .rplu_mode(1'b0),
        .sentinel_telemetry(512'd0)
    );
endmodule
