// spu_som_sidecar_top.v — Standalone SOM edge classifier
//
// Direct SPI-to-SOM BMU bridge. No processor core.
// Protocol (0xA5 writes):
//   sel=4  weight <node> <feat> <hex16>     — write one SOM weight feature
//   sel=5  feat <feat> <hex16>              — write one feature surd
//   sel=6  classify                          — run BMU, output UART result
//
// UART at 115200 baud on uart_tx_telemetry (B11 → USB bridge).

module spu_som_sidecar_top (
    input  wire        sys_clk,
    input  wire        spi_cs_n,
    input  wire        spi_sck,
    input  wire        spi_mosi,
    output wire        spi_miso,
    output wire        uart_tx_telemetry,
    output wire [2:0]  led
);

    localparam CLK_HZ = 50000000;
    localparam CLKS_PER_BIT = CLK_HZ / 115200;

    // ── Reset (200 cycle delay) ───────────────────────────────────────
    reg [7:0] rst_cnt = 8'd0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) begin
        if (!rst_n) rst_cnt <= rst_cnt + 1'b1;
    end

    // ── SPI config receiver (minimal, 0xA5 only) ───────────────────
    wire        cfg_wr_en;
    wire [2:0]  cfg_sel;
    wire [9:0]  cfg_addr;
    wire [63:0] cfg_data;

    spu_spi_cfg u_spi (
        .clk(sys_clk), .rst_n(rst_n),
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck),
        .spi_mosi(spi_mosi), .spi_miso(spi_miso),
        .wr_en(cfg_wr_en),
        .sel(cfg_sel),
        .addr(cfg_addr),
        .data(cfg_data),
        .result({bmu_done, class_pend, bmu_label[1:0]})
    );

    // ── Feature register writes (sel=5) ──────────────────────────────
    wire        feat_we = cfg_wr_en && (cfg_sel == 3'd5);
    reg  [143:0] feat_vec;

    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n)
            feat_vec <= 144'd0;
        else if (feat_we) begin
            case (cfg_addr[1:0])
                2'd0: feat_vec[17:0]   <= cfg_data[17:0];
                2'd1: feat_vec[53:36]  <= cfg_data[17:0];
                2'd2: feat_vec[89:72]  <= cfg_data[17:0];
                2'd3: feat_vec[125:108] <= cfg_data[17:0];
            endcase
        end
    end

    // ── Feature weights (uniform for Iris) ────────────────────────────
    wire [143:0] feat_weights = {
        36'h0_0001, 36'h0_0001, 36'h0_0001, 36'h0_0002
    };

    // ── SOM weight writes (sel=4) → BMU training port ────────────────
    wire        som_weight_we = cfg_wr_en && (cfg_sel == 3'd4);
    wire [2:0]  som_node      = cfg_addr[4:2];
    wire [1:0]  som_feat      = cfg_addr[1:0];
    wire [35:0] som_feat_data = cfg_data[35:0];
    wire [143:0] som_wdata;
    always @(*) begin
        som_wdata = 144'd0;
        som_wdata[som_feat * 36 +: 36] = som_feat_data;
    end

    // ── BMU instantiation ────────────────────────────────────────────
    wire        bmu_start;
    wire        bmu_done;
    wire [15:0] bmu_best, bmu_label;

    reg class_pend;
    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n)
            class_pend <= 1'b0;
        else if (cfg_wr_en && cfg_sel == 3'd6)
            class_pend <= 1'b1;
        else if (bmu_done)
            class_pend <= 1'b0;
    end
    assign bmu_start = class_pend && !bmu_done;

    spu_som_bmu #(.NUM_FEATURES(4), .MAX_NODES(7), .WIDTH(18)) u_bmu (
        .clk(sys_clk), .rst_n(rst_n),
        .start(bmu_start), .done(bmu_done),
        .features(feat_vec),
        .feature_weights(feat_weights),
        .bmu_valid(), .best_node_id(bmu_best),
        .second_node_id(), .cluster_label(bmu_label),
        .best_q(), .second_q(), .confidence_gap(), .has_second(),
        .axiomatic_level(2'b00),
        .axiomatic_fault(), .fault_type(), .fault_count(),
        .train_we(som_weight_we),
        .train_addr(som_node),
        .train_be(4'b0001 << som_feat),
        .train_wdata(som_wdata),
        .train_rdata()
    );

    // ── UART TX (bit-banged, proven in SOM BMU probe) ────────────────
    reg [9:0]  tx_shift;
    reg [15:0] tx_count;
    reg [7:0]  tx_byte;
    reg        tx_sending;
    reg        tx_pending;

    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_shift <= 10'h3FF;
            tx_count <= 0;
            tx_sending <= 1'b0;
            tx_pending <= 1'b0;
            uart_tx_telemetry <= 1'b1;
        end else begin
            if (!tx_sending) begin
                uart_tx_telemetry <= 1'b1;
                if (tx_pending && tx_count == 0) begin
                    tx_shift <= {1'b1, tx_byte, 1'b0};
                    tx_count <= CLKS_PER_BIT * 10;
                    tx_sending <= 1'b1;
                    tx_pending <= 1'b0;
                end
            end else begin
                if (tx_count == 1) begin
                    tx_sending <= 1'b0;
                    uart_tx_telemetry <= 1'b1;
                end else begin
                    uart_tx_telemetry <= tx_shift[0];
                    if (tx_count % CLKS_PER_BIT == 1)
                        tx_shift <= {1'b1, tx_shift[9:1]};
                end
                tx_count <= tx_count - 1;
            end

            // On BMU done, send result byte
            if (bmu_done && !tx_pending && !tx_sending) begin
                tx_byte <= {4'd0, bmu_label[1:0], bmu_best[1:0]};
                tx_pending <= 1'b1;
            end
        end
    end

    // ── LEDs: heartbeat ──────────────────────────────────────────────
    reg [25:0] blink;
    always @(posedge sys_clk) blink <= blink + 1'b1;
    assign led = {~blink[24], ~bmu_done, ~bmu_start};

endmodule
