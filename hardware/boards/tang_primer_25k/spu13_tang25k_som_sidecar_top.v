// spu13_tang25k_som_sidecar_top.v — Standalone SOM edge classifier
//
// Direct SPI-to-SOM BMU bridge. No processor core.
// Protocol (0xA5 writes):
//   sel=4  weight <node> <feat> <hex16>     — write one SOM weight feature
//   sel=5  feat <feat> <hex16>              — write one feature surd
//   sel=6  classify                          — run BMU, output UART result
//   sel=7  label <node> <label16>            — write semantic node label
// Read command 0x01 preserves the compact result nibble. Read command 0x02
// returns the versioned 52-byte SOM1 decision-evidence frame.
//
// UART at 115200 baud on uart_tx (C3 → dock USB-CDC).  The same stream is
// retained on uart_tx_telemetry (B11 → internal FPGA/BL616 link) for
// compatibility with the southbridge constraint set.
//
// Named distinctly from hardware/rtl/core/spu13/spu_som_sidecar_top.v (an
// unrelated, unreferenced cfg-bus/QR-commit variant) -- both used to share
// the name "spu_som_sidecar_top", which run_all_tests.py's source scan
// silently resolved to whichever file it saw first in scan_dirs order,
// so a naive testbench for this module would have silently compiled
// against the wrong one instead of erroring.

module spu13_tang25k_som_sidecar_top (
    input  wire        sys_clk,
    input  wire        spi_cs_n,
    input  wire        spi_sck,
    input  wire        spi_mosi,
    output wire        spi_miso,
    output wire        uart_tx,
    output reg         uart_tx_telemetry,
    output wire [2:0]  led
);

    assign uart_tx = uart_tx_telemetry;

    localparam CLK_HZ = 50000000;
    localparam CLKS_PER_BIT = CLK_HZ / 115200;

    // ── Reset (255 cycle delay) ───────────────────────────────────────
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

    // Declared ahead of u_spi's instantiation (not just ahead of use) --
    // iverilog, unlike yosys's frontend, requires nets referenced directly
    // in a port-connection expression to be declared before that
    // instantiation, not just before the enclosing always block.
    wire        bmu_start;
    wire        bmu_done;
    wire [15:0] bmu_best, bmu_label;
    reg         class_pend;
    reg         class_valid;
    wire [415:0] som1_frame;

    spu_spi_cfg u_spi (
        .clk(sys_clk), .rst_n(rst_n),
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck),
        .spi_mosi(spi_mosi), .spi_miso(spi_miso),
        .wr_en(cfg_wr_en),
        .sel(cfg_sel),
        .addr(cfg_addr),
        .data(cfg_data),
        .result({class_valid, class_pend, bmu_label[1:0]}),
        .result_frame(som1_frame)
    );

    // ── Feature register writes (sel=5) ──────────────────────────────
    wire        feat_we = cfg_wr_en && (cfg_sel == 3'd5);
    reg  [143:0] feat_vec;

    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n)
            feat_vec <= 144'd0;
        else if (feat_we) begin
            case (cfg_addr[1:0])
                2'd0: feat_vec[35:0]    <= cfg_data[35:0];
                2'd1: feat_vec[71:36]   <= cfg_data[35:0];
                2'd2: feat_vec[107:72]  <= cfg_data[35:0];
                2'd3: feat_vec[143:108] <= cfg_data[35:0];
            endcase
        end
    end

    // ── Feature weights (uniform for Iris) ────────────────────────────
    wire [143:0] feat_weights = {
        36'h0_0001, 36'h0_0001, 36'h0_0001, 36'h0_0001
    };

    // ── SOM weight writes (sel=4) → BMU training port ────────────────
    wire        som_weight_cmd = cfg_wr_en && (cfg_sel == 3'd4);
    wire [2:0]  som_node      = cfg_addr[4:2];
    wire [1:0]  som_feat      = cfg_addr[1:0];
    wire        som_weight_we = som_weight_cmd &&
                                (cfg_addr[9:5] == 0) && (som_node < 7);
    wire [35:0] som_feat_data = cfg_data[35:0];
    reg  [143:0] som_wdata;
    always @(*) begin
        som_wdata = 144'd0;
        som_wdata[som_feat * 36 +: 36] = som_feat_data;
    end

    // Semantic labels are separate from spu_som_bmu's legacy fixed LUT.  The
    // compact result keeps the legacy label for compatibility; SOM1 uses this
    // writable map-owned label table.
    wire som_label_we = cfg_wr_en && (cfg_sel == 3'd7) &&
                        (cfg_addr[9:3] == 0) && (cfg_addr[2:0] < 7);
    reg [15:0] semantic_label [0:6];
    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n) begin
            semantic_label[0] <= 16'd0;
            semantic_label[1] <= 16'd1;
            semantic_label[2] <= 16'd1;
            semantic_label[3] <= 16'd2;
            semantic_label[4] <= 16'd2;
            semantic_label[5] <= 16'd3;
            semantic_label[6] <= 16'd3;
        end else if (som_label_we) begin
            semantic_label[cfg_addr[2:0]] <= cfg_data[15:0];
        end
    end

    // A built-in map is valid at reset. Once host hydration begins, all 28
    // weights and all 7 semantic labels must be written before a new
    // generation becomes valid. This detects interrupted or partial hydration
    // without changing the legacy classifier behavior.
    reg [34:0] map_write_mask;
    reg        map_valid;
    reg [31:0] map_generation;
    wire       map_write_event = som_weight_we || som_label_we;
    wire [5:0] map_write_index = som_weight_we ? {1'b0, som_node, som_feat} :
                                                (6'd28 + cfg_addr[2:0]);
    wire [34:0] map_write_bit = 35'b1 << map_write_index;

    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n) begin
            map_write_mask <= 35'd0;
            map_valid <= 1'b1;
            map_generation <= 32'd0;
        end else if (map_write_event) begin
            if (map_valid) begin
                map_write_mask <= map_write_bit;
                map_valid <= 1'b0;
            end else if ((map_write_mask | map_write_bit) == {35{1'b1}}) begin
                map_write_mask <= 35'd0;
                map_valid <= 1'b1;
                map_generation <= map_generation + 1'b1;
            end else begin
                map_write_mask <= map_write_mask | map_write_bit;
            end
        end
    end

    // ── BMU instantiation (bmu_start/bmu_done/bmu_best/bmu_label/class_pend
    //    declared earlier, ahead of u_spi) ──────────────────────────────
    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n) begin
            class_pend <= 1'b0;
            class_valid <= 1'b0;
        end else if (cfg_wr_en && cfg_sel == 3'd6) begin
            class_pend <= 1'b1;
            class_valid <= 1'b0;
        end else if (bmu_done) begin
            class_pend <= 1'b0;
            class_valid <= 1'b1;
        end
    end
    assign bmu_start = class_pend && !bmu_done;

    wire [15:0] bmu_second;
    wire [63:0] bmu_best_q;
    wire [63:0] bmu_second_q;
    wire [63:0] bmu_gap;
    wire        bmu_has_second;

    spu_som_bmu #(.NUM_FEATURES(4), .MAX_NODES(7), .WIDTH(18)) u_bmu (
        .clk(sys_clk), .rst_n(rst_n),
        .start(bmu_start), .done(bmu_done),
        .features(feat_vec),
        .feature_weights(feat_weights),
        .bmu_valid(), .best_node_id(bmu_best),
        .second_node_id(bmu_second), .cluster_label(bmu_label),
        .best_q(bmu_best_q), .second_q(bmu_second_q),
        .confidence_gap(bmu_gap), .has_second(bmu_has_second),
        .axiomatic_level(2'b00),
        .axiomatic_fault(), .fault_type(), .fault_count(),
        .train_we(som_weight_we),
        .train_addr(som_node),
        .train_be(4'b0001 << som_feat),
        .train_wdata(som_wdata),
        .train_rdata()
    );

    // ── SOM1 versioned evidence frame ───────────────────────────────
    localparam SOM1_ERR_NONE           = 8'd0;
    localparam SOM1_ERR_MAP_INCOMPLETE = 8'd1;
    localparam SOM1_ERR_NO_SECOND      = 8'd2;

    reg [31:0] result_generation;
    wire som1_ambiguous = bmu_has_second && (bmu_gap == 64'd0);
    wire [15:0] som1_semantic_label = semantic_label[bmu_best[2:0]];
    wire [7:0] som1_error = !map_valid ? SOM1_ERR_MAP_INCOMPLETE :
                             !bmu_has_second ? SOM1_ERR_NO_SECOND :
                             SOM1_ERR_NONE;
    wire som1_frame_ready;
    wire som1_encoder_busy;

    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n)
            result_generation <= 32'd0;
        else if (bmu_done)
            result_generation <= result_generation + 1'b1;
    end

    spu13_som1_frame u_som1_frame (
        .clk(sys_clk), .rst_n(rst_n), .build(bmu_done),
        .result_valid(1'b1), .result_busy(1'b0),
        .has_second(bmu_has_second), .ambiguous(som1_ambiguous),
        .map_valid(map_valid), .error_code(som1_error),
        .map_generation(map_generation),
        .result_generation(result_generation + 1'b1),
        .best_node(bmu_best), .second_node(bmu_second),
        .label(som1_semantic_label), .best_q(bmu_best_q),
        .second_q(bmu_second_q), .confidence_gap(bmu_gap),
        .frame(som1_frame), .frame_ready(som1_frame_ready),
        .encoder_busy(som1_encoder_busy)
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
            // bmu_best is a node id 0-6 (needs 3 bits) -- 2 bits would alias
            // {0,4}, {1,5}, {2,6}; keep the full field, drop padding to 3'd0.
            if (bmu_done && !tx_pending && !tx_sending) begin
                tx_byte <= {3'd0, bmu_label[1:0], bmu_best[2:0]};
                tx_pending <= 1'b1;
            end
        end
    end

    // ── LEDs: heartbeat ──────────────────────────────────────────────
    reg [25:0] blink;
    always @(posedge sys_clk) blink <= blink + 1'b1;
    assign led = {~blink[24], ~bmu_done, ~bmu_start};

endmodule
