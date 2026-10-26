// Wukong Artix-7 transactional TGR1 sidecar over the shared southbridge SPI.
//
// CMD B2 loads and verifies a complete TGR1 record into the inactive BRAM
// bank. CMD B3 returns the last committed mechanical verdict plus loader
// diagnostics. SPI, table replay, and the exact guard all run at the proven
// 25 MHz cadence; the board oscillator/reset divider remains at 50 MHz.

module spu_a7_tensegrity_link_top #(
    parameter USE_ZPHI_KARATSUBA = 0
) (
    input  wire sys_clk,
    input  wire rst_n,
    input  wire spi_cs_n,
    input  wire spi_sck,
    input  wire spi_mosi,
    output wire spi_miso
);
    reg [1:0] rst_sync = 2'b00;
    reg [7:0] rst_count = 8'd0;
    wire rst_n_int = (rst_count == 8'hff);

    always @(posedge sys_clk) begin
        rst_sync <= {rst_sync[0], rst_n};
        if (!rst_sync[1])
            rst_count <= 8'd0;
        else if (!rst_n_int)
            rst_count <= rst_count + 1'b1;
    end

    reg guard_clk_div = 1'b0;
    wire guard_clk;
    always @(posedge sys_clk) begin
        if (!rst_n_int)
            guard_clk_div <= 1'b0;
        else
            guard_clk_div <= ~guard_clk_div;
    end
`ifdef SYNTHESIS
    BUFG u_guard_clk_buf (.I(guard_clk_div), .O(guard_clk));
`else
    assign guard_clk = guard_clk_div;
`endif

    wire tgr_stream_start, tgr_stream_valid, tgr_stream_commit, tgr_stream_abort;
    wire tgr_status_hold;
    wire [15:0] tgr_stream_length;
    wire [31:0] tgr_stream_vector_id;
    wire [7:0] tgr_stream_data;
    wire [127:0] tgr_transport_status;

    spu_spi_slave #(
        .ENABLE_TENSEGRITY(1),
        .TENSEGRITY_ONLY(1)
    ) u_spi (
        .clk(guard_clk), .rst_n(rst_n_int),
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck),
        .spi_mosi(spi_mosi), .spi_miso(spi_miso),
        .manifold_state(832'd0), .satellite_snaps(4'd0),
        .is_janus_point(1'b0), .dissonance(16'd0),
        .scale_table(52'd0), .scale_overflow(13'd0),
        .qr_commit_valid(1'b0), .qr_commit_lane(4'd0),
        .qr_commit_A(64'd0), .qr_commit_B(64'd0),
        .qr_commit_C(64'd0), .qr_commit_D(64'd0),
        .hex_valid(1'b0), .hex_q(16'd0), .hex_r(16'd0),
        .rplu_ratio_res(3'sd0), .rplu_ratio_valid(1'b0),
        .fifo_full(1'b0), .laminar_index(16'd0),
        .turbulence(1'b0), .rplu_mode(1'b0), .boot_ready(1'b1),
        .sentinel_telemetry(512'd0),
        .tgr_stream_start(tgr_stream_start),
        .tgr_stream_length(tgr_stream_length),
        .tgr_stream_vector_id(tgr_stream_vector_id),
        .tgr_stream_valid(tgr_stream_valid), .tgr_stream_data(tgr_stream_data),
        .tgr_stream_commit(tgr_stream_commit), .tgr_stream_abort(tgr_stream_abort),
        .tgr_status_hold(tgr_status_hold),
        .tgr_transport_status(tgr_transport_status)
    );

    spu13_tensegrity_sidecar #(
        .USE_ZPHI_KARATSUBA(USE_ZPHI_KARATSUBA)
    ) u_sidecar (
        .clk(guard_clk), .rst_n(rst_n_int),
        .stream_start(tgr_stream_start), .stream_length(tgr_stream_length),
        .stream_vector_id(tgr_stream_vector_id),
        .stream_valid(tgr_stream_valid), .stream_data(tgr_stream_data),
        .stream_commit(tgr_stream_commit), .stream_abort(tgr_stream_abort),
        .status_hold(tgr_status_hold),
        .transport_status(tgr_transport_status),
        .active_valid(), .busy(), .loader_error()
    );
endmodule
