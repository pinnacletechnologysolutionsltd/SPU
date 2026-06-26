// spu13_tang25k_top.v
// Modern SPU-13 Sovereign Core Top for Sipeed Tang Primer 25K
// Architecture: Phi-Gated TDM Manifold (v1.7)

module spu13_tang25k_top #(
    parameter ENABLE_SDRAM = 1,
    parameter SDRAM_COL_BITS = 9,
    parameter SDRAM_ROW_BITS = 13,
    parameter SDRAM_RANK_BITS = 1,
    parameter SDRAM_XSDS_INVERTED_RANK_CS = 1,
    parameter SDRAM_REFRESH_CYCLES = 49,
    parameter ENABLE_CORE_RPLU = 0,
    parameter ENABLE_CORE_LATTICE = 0,
    parameter ENABLE_CORE_MATH = 0,
    parameter ENABLE_CORE_SOM  = 0,
    parameter ENABLE_CORE_RPLU_V2 = 0,
    parameter ENABLE_RPLU_TELEMETRY = 0,
    parameter ENABLE_SDRAM_SELFTEST = 1,
    parameter ENABLE_CORE_SDRAM_VERIFY = 1,
    parameter SDRAM_READ_CAPTURE_OFFSET = 3,
    parameter SDRAM_INVERT_CLK = 1,
    parameter [15:0] DQ_STUCK_MASK = 16'h0000  // bits forced high on stuck DQ lines (0x0402 = bits 1,10)
) (
    input  wire periph_rx, // Pin B3: Input from RP2350
    input  wire sys_clk,
    output wire [2:0] led,
    output wire uart_tx,
    output wire uart_tx_telemetry,
    input  wire uart_rx_telemetry,

    // PMOD J4 SPI flash used for first-stage bring-up.
    output wire flash_cs,
    output wire flash_sck,
    output wire flash_mosi,
    input  wire flash_miso,

    // Remaining Dedicated SDRAM Interface
    output wire        sdram_clk,
    output wire        sdram_cs_n,
    output wire        sdram_ras_n,
    output wire        sdram_cas_n,
    output wire        sdram_we_n,
    output wire [1:0]  sdram_ba,
    output wire        sdram_a0,  output wire        sdram_a1,  output wire        sdram_a2,
    output wire        sdram_a3,
    output wire        sdram_a4,  output wire        sdram_a5,  output wire        sdram_a6,
    output wire        sdram_a7,  output wire        sdram_a8,  output wire        sdram_a9,
    output wire        sdram_a10, output wire        sdram_a11, output wire        sdram_a12,
    inout  wire [15:0] sdram_dq,
    output wire [1:0]  sdram_dm
);

    // 1. Clock & Reset Logic
    wire clk_50m;
    BUFG u_bufg_50m (.I(sys_clk), .O(clk_50m));

    reg [5:0] clk_div = 0;
    always @(posedge clk_50m) clk_div <= clk_div + 1;

    wire clk_core_raw = clk_div[2]; // 6.25 MHz (50MHz / 8)
    wire clk_core;
    BUFG u_bufg_core (.I(clk_core_raw), .O(clk_core));

    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge clk_core) if (rst_cnt != 8'hFF) rst_cnt <= rst_cnt + 1;

    // UART is split across two domains:
    // - Host RX stays in the divided core domain.
    // - Telemetry TX runs from the raw 50 MHz crystal to remove baud ambiguity.
    localparam integer HOST_CLK_FREQ         = 6250000;
    localparam integer HOST_BAUD_RATE        = 115200;
    localparam integer HOST_CLKS_PER_BIT     = HOST_CLK_FREQ / HOST_BAUD_RATE;
    localparam integer UART_TX_CLK_FREQ      = 50000000;
    localparam integer UART_TX_BAUD_RATE     = 115200;
    localparam integer UART_TX_CLKS_PER_BIT  = 434;
    localparam integer UART_TX_MSG_PERIOD    = UART_TX_CLK_FREQ / 10;
    localparam integer UART_TX_BOOT_PERIOD   = UART_TX_CLK_FREQ;
    localparam integer UART_TX_START_DELAY   = UART_TX_CLK_FREQ / 2;

    // --- Telemetry UART for debug output (on sys_clk domain) ---
    reg [7:0]  telemetry_data = 8'h00;
    reg        telemetry_tx_start = 1'b0;
    reg [23:0] telemetry_timer = 0;
    localparam integer TELEMETRY_INTERVAL = 500000; // ~10ms at 50MHz

    always @(posedge clk_50m or negedge rst_n) begin
        if (!rst_n) begin
            telemetry_data <= 8'h00;
            telemetry_tx_start <= 1'b0;
            telemetry_timer <= 0;
        end else begin
            telemetry_tx_start <= 1'b0; // Pulse for one cycle
            if (telemetry_timer >= TELEMETRY_INTERVAL) begin
                telemetry_timer <= 0;
                telemetry_data <= telemetry_data + 8'h01;
                telemetry_tx_start <= 1'b1;
            end else begin
                telemetry_timer <= telemetry_timer + 1;
            end
        end
    end

    surd_uart_tx #(.CLK_HZ(UART_TX_CLK_FREQ), .BAUD(UART_TX_BAUD_RATE)) u_telemetry_uart (
        .clk(clk_50m),
        .reset(!rst_n),
        .data_in({56'd0, telemetry_data}),
        .start(telemetry_tx_start),
        .tx(uart_tx_telemetry),
        .ready()
    );

    // 2. Fibonacci Timing Sequencer (Phi 8, 13, 21)
    // SPU-13 core requires specific pulses to drive its pipeline stages.
    reg [8:0] phi_cnt = 0; // Increased width for 273-cycle burst
    wire pulse_p_trigger;
    always @(posedge clk_core) begin
        if (!rst_n) phi_cnt <= 273; // Idle at end
        else if (pulse_p_trigger) phi_cnt <= 0; // Start 13-axis burst
        else if (phi_cnt < 273) phi_cnt <= phi_cnt + 1; // Run burst
    end
    // Fibonacci pulses occur every 21 cycles within the burst
    wire [4:0] phi_sub = (phi_cnt < 273) ? (phi_cnt % 21) : 5'd0;
    wire phi_8  = (phi_sub == 5'd7);
    wire phi_13 = (phi_sub == 5'd12);
    wire phi_21 = (phi_sub == 5'd20);

    // 3. The Soul: SPI Bootloader
    wire [23:0] prime_data;
    wire [3:0]  prime_addr;
    wire        prime_we;
    wire [31:0] pell_data;
    wire [2:0]  pell_addr;
    wire        pell_we;
    wire        boot_done;
    wire [23:0] boot_jedec_id;

    // 4. Host Input Receiver (RP2350 Bridge) - Flattened into Top
    reg [7:0] host_input;
    reg       host_rx_valid;
    reg [15:0] host_clk_cnt;
    reg [3:0]  host_bit_idx;
    reg [1:0]  host_state;
    reg [7:0]  host_shift;

    // Combined RX: Idle is High (1). Any Low (0) start bit triggers the receiver.
    wire host_rx_combined = periph_rx & uart_rx_telemetry;

    always @(posedge clk_core or negedge rst_n) begin
        if (!rst_n) begin
            host_state <= 0;
            host_rx_valid <= 0;
            host_clk_cnt <= 0;
            host_bit_idx <= 0;
            host_input <= 0;
        end else begin
            host_rx_valid <= 0;
            case (host_state)
                0: begin // Idle
                    if (!host_rx_combined) begin
                        if (host_clk_cnt < (HOST_CLKS_PER_BIT / 2)) host_clk_cnt <= host_clk_cnt + 1;
                        else begin host_clk_cnt <= 0; host_state <= 1; end
                    end else host_clk_cnt <= 0;
                end
                1: begin // Data
                    if (host_clk_cnt < HOST_CLKS_PER_BIT - 1) host_clk_cnt <= host_clk_cnt + 1;
                    else begin
                        host_clk_cnt <= 0;
                        host_shift[host_bit_idx] <= host_rx_combined;
                        if (host_bit_idx < 7) host_bit_idx <= host_bit_idx + 1;
                        else begin host_bit_idx <= 0; host_state <= 2; end
                    end
                end
                2: begin // Stop
                    if (host_clk_cnt < HOST_CLKS_PER_BIT - 1) host_clk_cnt <= host_clk_cnt + 1;
                    else begin
                        host_clk_cnt <= 0;
                        host_rx_valid <= 1;
                        host_input <= host_shift;
                        host_state <= 0;
                    end
                end
            endcase
        end
    end

    // 5. Interactive Rotor Control (Virtual Hand)
    reg [31:0] rotor_p_reg;
    reg [31:0] rotor_q_reg;
    reg        manual_en;

    always @(posedge clk_core or negedge rst_n) begin
        if (!rst_n) begin
            rotor_p_reg <= 32'h0000_1000; // Identity P (Q12: 1.0)
            rotor_q_reg <= 32'h0000_0000; // Identity Q (Q12: 0.0)
            manual_en   <= 1'b0;
        end else if (host_rx_valid) begin
            manual_en <= 1'b1; // First press activates manual mode
            case (host_input)
                8'h77: rotor_p_reg <= rotor_p_reg + 32'h0000_0040; // 'w' -> +P (fine grain)
                8'h73: rotor_p_reg <= rotor_p_reg - 32'h0000_0040; // 's' -> -P
                8'h61: rotor_q_reg <= rotor_q_reg + 32'h0000_0040; // 'a' -> +Q
                8'h64: rotor_q_reg <= rotor_q_reg - 32'h0000_0040; // 'd' -> -Q
                8'h20: begin // SPACE -> Reset to Identity
                    rotor_p_reg <= 32'h0000_1000;
                    rotor_q_reg <= 32'h0000_0000;
                    manual_en   <= 1'b0; // Hand back to vault
                end
            endcase
        end
    end

    // SDRAM Inhaler signals from Boot Unit
    wire        boot_mem_wr;
    wire [24:0] boot_mem_addr;
    wire [831:0] boot_mem_data;
    wire        boot_rplu_cfg_wr_en;
    wire [2:0]  boot_rplu_cfg_sel;
    wire [7:0]  boot_rplu_cfg_material;
    wire [9:0]  boot_rplu_cfg_addr;
    wire [63:0] boot_rplu_cfg_data;
    wire [15:0] boot_rplu_cfg_loaded;
    wire [31:0] boot_rplu_cfg_checksum;
    wire [5:0]  boot_state;
    wire        sdram_burst_done;

    spu_laminar_boot #(
        .ENABLE_RPLU_BOOT(ENABLE_CORE_RPLU),
        .RPLU_CFG_RECORDS(16'd2051),
        .SPI_SCK_HALF_CYCLES(2)
    ) boot_unit (
        .clk(clk_core),
        .rst_n(rst_n),
        .flash_cs(flash_cs),
        .flash_sck(flash_sck),
        .flash_miso(flash_miso),
        .flash_mosi(flash_mosi),
        .jedec_id(boot_jedec_id),
        .bram_data(prime_data),
        .bram_addr(prime_addr),
        .bram_we(prime_we),
        .pell_data(pell_data),
        .pell_addr(pell_addr),
        .pell_we(pell_we),
        .mem_burst_wr(boot_mem_wr),
        .mem_addr(boot_mem_addr),
        .mem_wr_manifold(boot_mem_data),
        .mem_burst_done(sdram_burst_done),
        .rplu_cfg_wr_en(boot_rplu_cfg_wr_en),
        .rplu_cfg_sel(boot_rplu_cfg_sel),
        .rplu_cfg_material(boot_rplu_cfg_material),
        .rplu_cfg_addr(boot_rplu_cfg_addr),
        .rplu_cfg_data(boot_rplu_cfg_data),
        .rplu_cfg_loaded(boot_rplu_cfg_loaded),
        .rplu_cfg_checksum(boot_rplu_cfg_checksum),
        .boot_done(boot_done),
        .boot_state(boot_state)
    );

    // 4. The Memory: SDRAM Bridge
    wire        sdram_ready;
    wire        sdram_burst_rd;
    wire        sdram_burst_wr;
    wire [24:0] sdram_mem_addr;
    wire [831:0] sdram_rd_manifold;
    wire [831:0] sdram_wr_manifold;

    // Mask stuck DQ bits in every 16-bit word of the read manifold.
    // Word i gets: rd_manifold[i*16 +: 16] | DQ_STUCK_MASK
    wire [831:0] sdram_rd_manifold_masked;
    genvar gen_mask_i;
    generate
        for (gen_mask_i = 0; gen_mask_i < 52; gen_mask_i = gen_mask_i + 1) begin : gen_dq_mask
            assign sdram_rd_manifold_masked[gen_mask_i*16 +: 16] =
                sdram_rd_manifold[gen_mask_i*16 +: 16] | DQ_STUCK_MASK;
        end
    endgenerate

    wire [12:0] sdram_addr_bus;
    wire [SDRAM_COL_BITS+SDRAM_ROW_BITS+SDRAM_RANK_BITS+1:0] sdram_bridge_mem_addr =
        sdram_mem_addr[SDRAM_COL_BITS+SDRAM_ROW_BITS+SDRAM_RANK_BITS+1:0];
    localparam integer SDRAM_RANK_SELECT_BIT = SDRAM_COL_BITS + SDRAM_ROW_BITS + 2;
    localparam [24:0] SDRAM_SELFTEST_ADDR =
        (SDRAM_RANK_BITS != 0) ? (25'h000A040 | (25'd1 << SDRAM_RANK_SELECT_BIT))
                               : 25'h01A040;
    localparam [11:0] SDRAM_SELFTEST_TIMEOUT = 12'hFFF;
    localparam SDRAM_SELFTEST_REQUIRED = ENABLE_SDRAM && ENABLE_SDRAM_SELFTEST;
    localparam CORE_SDRAM_VERIFY_REQUIRED = ENABLE_SDRAM && ENABLE_CORE_SDRAM_VERIFY;

    reg         sdram_selftest_burst_rd;
    reg         sdram_selftest_burst_wr;
    wire [831:0] sdram_selftest_wr_manifold;
    reg [2:0]   sdram_selftest_state;
    reg [11:0]  sdram_selftest_wait;
    reg [3:0]   sdram_selftest_retries;
    reg         sdram_selftest_done;
    reg         sdram_selftest_pass;
    reg         sdram_selftest_fail;
    reg         sdram_selftest_wr_done;
    reg         sdram_selftest_rd_done;
    reg [5:0]   sdram_selftest_mismatch_count;
    reg [15:0]  sdram_selftest_first_word;
    reg [15:0]  sdram_selftest_last_word;
    reg [31:0]  sdram_selftest_checksum;
    reg [15:0]  sdram_selftest_exp0_obs1_mask;
    reg [15:0]  sdram_selftest_exp1_obs0_mask;

    localparam SDRAM_ST_IDLE       = 3'd0;
    localparam SDRAM_ST_WRITE      = 3'd1;
    localparam SDRAM_ST_WAIT_WRITE = 3'd2;
    localparam SDRAM_ST_READ       = 3'd3;
    localparam SDRAM_ST_WAIT_READ  = 3'd4;
    localparam SDRAM_ST_DONE       = 3'd5;

    function [15:0] sdram_selftest_pattern;
        input [5:0] idx;
        begin
            sdram_selftest_pattern = 16'hA55A ^ {idx, ~idx, idx[3:0]};
        end
    endfunction

    genvar gen_selftest_pattern_i;
    generate
        for (gen_selftest_pattern_i = 0; gen_selftest_pattern_i < 52; gen_selftest_pattern_i = gen_selftest_pattern_i + 1) begin : gen_sdram_selftest_pattern
            assign sdram_selftest_wr_manifold[gen_selftest_pattern_i*16 +: 16] =
                sdram_selftest_pattern(gen_selftest_pattern_i[5:0]);
        end
    endgenerate

    reg        sdram_selftest_match_calc;
    reg [5:0]  sdram_selftest_mismatch_calc;
    reg [31:0] sdram_selftest_checksum_calc;
    reg [15:0] sdram_selftest_exp0_obs1_mask_calc;
    reg [15:0] sdram_selftest_exp1_obs0_mask_calc;
    integer sdram_check_i;
    always @(*) begin
        sdram_selftest_match_calc = 1'b1;
        sdram_selftest_mismatch_calc = 6'd0;
        sdram_selftest_checksum_calc = 32'd0;
        sdram_selftest_exp0_obs1_mask_calc = 16'd0;
        sdram_selftest_exp1_obs0_mask_calc = 16'd0;
        for (sdram_check_i = 0; sdram_check_i < 52; sdram_check_i = sdram_check_i + 1) begin
            sdram_selftest_checksum_calc = sdram_selftest_checksum_calc
                                         + {16'd0, sdram_rd_manifold_masked[sdram_check_i*16 +: 16]};
            sdram_selftest_exp0_obs1_mask_calc = sdram_selftest_exp0_obs1_mask_calc
                                               | ((~sdram_selftest_pattern(sdram_check_i[5:0]) & ~DQ_STUCK_MASK)
                                                  & (sdram_rd_manifold_masked[sdram_check_i*16 +: 16] & ~DQ_STUCK_MASK));
            sdram_selftest_exp1_obs0_mask_calc = sdram_selftest_exp1_obs0_mask_calc
                                               | ((sdram_selftest_pattern(sdram_check_i[5:0]) & ~DQ_STUCK_MASK)
                                                  & (~sdram_rd_manifold_masked[sdram_check_i*16 +: 16] & ~DQ_STUCK_MASK));
            if (sdram_rd_manifold_masked[sdram_check_i*16 +: 16] !=
                    (sdram_selftest_pattern(sdram_check_i[5:0]) | DQ_STUCK_MASK)) begin
                sdram_selftest_match_calc = 1'b0;
                if (sdram_selftest_mismatch_calc != 6'h3F) begin
                    sdram_selftest_mismatch_calc = sdram_selftest_mismatch_calc + 1'b1;
                end
            end
        end
    end

    always @(posedge clk_core or negedge rst_n) begin
        if (!rst_n) begin
            sdram_selftest_burst_rd <= 1'b0;
            sdram_selftest_burst_wr <= 1'b0;
            sdram_selftest_state <= SDRAM_ST_IDLE;
            sdram_selftest_wait <= 12'd0;
            sdram_selftest_retries <= 4'd0;
            sdram_selftest_done <= 1'b0;
            sdram_selftest_pass <= 1'b0;
            sdram_selftest_fail <= 1'b0;
            sdram_selftest_wr_done <= 1'b0;
            sdram_selftest_rd_done <= 1'b0;
            sdram_selftest_mismatch_count <= 6'd0;
            sdram_selftest_first_word <= 16'd0;
            sdram_selftest_last_word <= 16'd0;
            sdram_selftest_checksum <= 32'd0;
            sdram_selftest_exp0_obs1_mask <= 16'd0;
            sdram_selftest_exp1_obs0_mask <= 16'd0;
        end else begin
            sdram_selftest_burst_rd <= 1'b0;
            sdram_selftest_burst_wr <= 1'b0;

            if (!SDRAM_SELFTEST_REQUIRED) begin
                sdram_selftest_state <= SDRAM_ST_DONE;
                sdram_selftest_done <= 1'b1;
                sdram_selftest_pass <= 1'b1;
            end else begin
                case (sdram_selftest_state)
                    SDRAM_ST_IDLE: begin
                        sdram_selftest_done <= 1'b0;
                        sdram_selftest_pass <= 1'b0;
                        sdram_selftest_fail <= 1'b0;
                        sdram_selftest_wr_done <= 1'b0;
                        sdram_selftest_rd_done <= 1'b0;
                        sdram_selftest_mismatch_count <= 6'd0;
                        sdram_selftest_exp0_obs1_mask <= 16'd0;
                        sdram_selftest_exp1_obs0_mask <= 16'd0;
                        sdram_selftest_wait <= 12'd0;
                        sdram_selftest_retries <= 4'd0;
                        if (boot_done && sdram_ready) begin
                            sdram_selftest_state <= SDRAM_ST_WRITE;
                        end
                    end

                    SDRAM_ST_WRITE: begin
                        sdram_selftest_burst_wr <= 1'b1;
                        sdram_selftest_wait <= 12'd0;
                        sdram_selftest_state <= SDRAM_ST_WAIT_WRITE;
                    end

                    SDRAM_ST_WAIT_WRITE: begin
                        if (sdram_burst_done) begin
                            sdram_selftest_wr_done <= 1'b1;
                            sdram_selftest_retries <= 4'd0;
                            sdram_selftest_wait <= 12'd0;
                            sdram_selftest_state <= SDRAM_ST_READ;
                        end else if (sdram_selftest_wait == SDRAM_SELFTEST_TIMEOUT) begin
                            if (sdram_selftest_retries == 4'hF) begin
                                sdram_selftest_done <= 1'b1;
                                sdram_selftest_fail <= 1'b1;
                                sdram_selftest_state <= SDRAM_ST_DONE;
                            end else begin
                                sdram_selftest_retries <= sdram_selftest_retries + 1'b1;
                                sdram_selftest_state <= SDRAM_ST_WRITE;
                            end
                        end else begin
                            sdram_selftest_wait <= sdram_selftest_wait + 1'b1;
                        end
                    end

                    SDRAM_ST_READ: begin
                        sdram_selftest_burst_rd <= 1'b1;
                        sdram_selftest_wait <= 12'd0;
                        sdram_selftest_state <= SDRAM_ST_WAIT_READ;
                    end

                    SDRAM_ST_WAIT_READ: begin
                        if (sdram_burst_done) begin
                            sdram_selftest_rd_done <= 1'b1;
                            sdram_selftest_done <= 1'b1;
                            sdram_selftest_pass <= sdram_selftest_match_calc;
                            sdram_selftest_fail <= !sdram_selftest_match_calc;
                            sdram_selftest_mismatch_count <= sdram_selftest_mismatch_calc;
                            sdram_selftest_first_word <= sdram_rd_manifold_masked[15:0];
                            sdram_selftest_last_word <= sdram_rd_manifold_masked[831:816];
                            sdram_selftest_checksum <= sdram_selftest_checksum_calc;
                            sdram_selftest_exp0_obs1_mask <= sdram_selftest_exp0_obs1_mask_calc;
                            sdram_selftest_exp1_obs0_mask <= sdram_selftest_exp1_obs0_mask_calc;
                            sdram_selftest_state <= SDRAM_ST_DONE;
                        end else if (sdram_selftest_wait == SDRAM_SELFTEST_TIMEOUT) begin
                            if (sdram_selftest_retries == 4'hF) begin
                                sdram_selftest_done <= 1'b1;
                                sdram_selftest_fail <= 1'b1;
                                sdram_selftest_state <= SDRAM_ST_DONE;
                            end else begin
                                sdram_selftest_retries <= sdram_selftest_retries + 1'b1;
                                sdram_selftest_state <= SDRAM_ST_READ;
                            end
                        end else begin
                            sdram_selftest_wait <= sdram_selftest_wait + 1'b1;
                        end
                    end

                    default: begin
                        sdram_selftest_state <= SDRAM_ST_DONE;
                    end
                endcase
            end
        end
    end

    wire sdram_selftest_complete = !SDRAM_SELFTEST_REQUIRED || sdram_selftest_done;
    wire sdram_selftest_owns_bus = SDRAM_SELFTEST_REQUIRED && boot_done && !sdram_selftest_done;
    wire [31:0] sdram_selftest_status_word = {
        8'h5D, 8'hA5,
        sdram_selftest_done,
        sdram_selftest_pass,
        sdram_selftest_fail,
        sdram_selftest_wr_done,
        sdram_selftest_rd_done,
        sdram_selftest_state,
        2'b00,
        sdram_selftest_mismatch_count
    };
    wire [31:0] sdram_selftest_endpoints_word = {sdram_selftest_first_word, sdram_selftest_last_word};
    wire [31:0] sdram_selftest_error_mask_word = {
        sdram_selftest_exp1_obs0_mask,
        sdram_selftest_exp0_obs1_mask
    };

    wire        core_mem_rd;
    wire        core_mem_wr;
    wire [23:0] core_mem_addr;
    wire [831:0] core_mem_wr_data;
    reg         core_mem_rd_d;
    reg         core_mem_wr_d;
    reg         core_mem_rd_pending;
    reg         core_mem_wr_pending;

    reg [2:0]   core_sdram_verify_state;
    reg [11:0]  core_sdram_verify_wait;
    reg         core_sdram_verify_done;
    reg         core_sdram_verify_pass;
    reg         core_sdram_verify_fail;
    reg         core_sdram_verify_wr_seen;
    reg         core_sdram_verify_rd_done;
    reg [31:0]  core_sdram_verify_wr_checksum;
    reg [31:0]  core_sdram_verify_rd_checksum;
    reg [5:0]   core_sdram_verify_sum_idx;
    wire        core_mem_rd_request;
    wire        core_mem_wr_request;

    localparam CORE_SDRAM_ST_IDLE       = 3'd0;
    localparam CORE_SDRAM_ST_SUM_WR     = 3'd1;
    localparam CORE_SDRAM_ST_WAIT_READ  = 3'd2;
    localparam CORE_SDRAM_ST_DONE       = 3'd3;
    localparam CORE_SDRAM_ST_SUM_RD     = 3'd4;

    wire [15:0] core_sdram_verify_wr_word =
        core_mem_wr_data[core_sdram_verify_sum_idx * 16 +: 16] | DQ_STUCK_MASK;
    wire [15:0] core_sdram_verify_rd_word =
        sdram_rd_manifold_masked[core_sdram_verify_sum_idx * 16 +: 16];
    wire [31:0] core_sdram_verify_rd_checksum_next =
        core_sdram_verify_rd_checksum + {16'd0, core_sdram_verify_rd_word};

    wire core_sdram_verify_capture = CORE_SDRAM_VERIFY_REQUIRED
                                   && (core_sdram_verify_state == CORE_SDRAM_ST_IDLE)
                                   && sdram_selftest_complete
                                   && !sdram_selftest_owns_bus
                                   && core_mem_wr_request;
    wire core_sdram_verify_read_complete = CORE_SDRAM_VERIFY_REQUIRED
                                         && (core_sdram_verify_state == CORE_SDRAM_ST_WAIT_READ)
                                         && core_mem_rd
                                         && sdram_burst_done;

    always @(posedge clk_core or negedge rst_n) begin
        if (!rst_n) begin
            core_sdram_verify_state <= CORE_SDRAM_ST_IDLE;
            core_sdram_verify_wait <= 12'd0;
            core_sdram_verify_done <= 1'b0;
            core_sdram_verify_pass <= 1'b0;
            core_sdram_verify_fail <= 1'b0;
            core_sdram_verify_wr_seen <= 1'b0;
            core_sdram_verify_rd_done <= 1'b0;
            core_sdram_verify_wr_checksum <= 32'd0;
            core_sdram_verify_rd_checksum <= 32'd0;
            core_sdram_verify_sum_idx <= 6'd0;
        end else begin
            if (!CORE_SDRAM_VERIFY_REQUIRED) begin
                core_sdram_verify_state <= CORE_SDRAM_ST_DONE;
                core_sdram_verify_done <= 1'b1;
                core_sdram_verify_pass <= 1'b1;
            end else begin
                case (core_sdram_verify_state)
                    CORE_SDRAM_ST_IDLE: begin
                        core_sdram_verify_wait <= 12'd0;
                        if (core_sdram_verify_capture) begin
                            core_sdram_verify_sum_idx <= 6'd0;
                            core_sdram_verify_wr_checksum <= 32'd0;
                            core_sdram_verify_rd_checksum <= 32'd0;
                            core_sdram_verify_wr_seen <= 1'b1;
                            core_sdram_verify_state <= CORE_SDRAM_ST_SUM_WR;
                        end
                    end

                    CORE_SDRAM_ST_SUM_WR: begin
                        core_sdram_verify_wr_checksum <= core_sdram_verify_wr_checksum
                                                       + {16'd0, core_sdram_verify_wr_word};
                        if (core_sdram_verify_sum_idx == 6'd51) begin
                            core_sdram_verify_sum_idx <= 6'd0;
                            core_sdram_verify_state <= CORE_SDRAM_ST_WAIT_READ;
                        end else begin
                            core_sdram_verify_sum_idx <= core_sdram_verify_sum_idx + 1'b1;
                        end
                    end

                    CORE_SDRAM_ST_WAIT_READ: begin
                        if (core_sdram_verify_read_complete) begin
                            core_sdram_verify_sum_idx <= 6'd0;
                            core_sdram_verify_rd_checksum <= 32'd0;
                            core_sdram_verify_state <= CORE_SDRAM_ST_SUM_RD;
                        end else if (core_sdram_verify_wait == SDRAM_SELFTEST_TIMEOUT) begin
                            core_sdram_verify_done <= 1'b1;
                            core_sdram_verify_fail <= 1'b1;
                            core_sdram_verify_state <= CORE_SDRAM_ST_DONE;
                        end else begin
                            core_sdram_verify_wait <= core_sdram_verify_wait + 1'b1;
                        end
                    end

                    CORE_SDRAM_ST_SUM_RD: begin
                        core_sdram_verify_rd_checksum <= core_sdram_verify_rd_checksum_next;
                        if (core_sdram_verify_sum_idx == 6'd51) begin
                            core_sdram_verify_rd_done <= 1'b1;
                            core_sdram_verify_done <= 1'b1;
                            core_sdram_verify_pass <= (core_sdram_verify_rd_checksum_next == core_sdram_verify_wr_checksum)
                                                    && (core_sdram_verify_wr_checksum != 32'd0);
                            core_sdram_verify_fail <= (core_sdram_verify_rd_checksum_next != core_sdram_verify_wr_checksum)
                                                    || (core_sdram_verify_wr_checksum == 32'd0);
                            core_sdram_verify_state <= CORE_SDRAM_ST_DONE;
                        end else begin
                            core_sdram_verify_sum_idx <= core_sdram_verify_sum_idx + 1'b1;
                        end
                    end

                    default: begin
                        core_sdram_verify_state <= CORE_SDRAM_ST_DONE;
                    end
                endcase
            end
        end
    end

    wire [31:0] core_sdram_verify_status_word = {
        8'hC0, 8'h5D,
        core_sdram_verify_done,
        core_sdram_verify_pass,
        core_sdram_verify_fail,
        core_sdram_verify_wr_seen,
        core_sdram_verify_rd_done,
        core_sdram_verify_state,
        2'b00,
        core_mem_rd,
        core_mem_wr,
        core_mem_rd_pending,
        core_mem_wr_pending,
        core_mem_rd_request,
        core_mem_wr_request
    };

    generate
        if (ENABLE_SDRAM) begin : gen_sdram
            // Bus Arbitration: Bootloader has priority until boot_done is high
            assign sdram_burst_rd = boot_done
                                   ? (sdram_selftest_owns_bus ? sdram_selftest_burst_rd
                                      : core_mem_rd_request)
                                   : 1'b0;
            assign sdram_burst_wr = boot_done
                                   ? (sdram_selftest_owns_bus ? sdram_selftest_burst_wr
                                      : (core_sdram_verify_capture ? 1'b0
                                         : core_mem_wr_request))
                                   : boot_mem_wr;
            assign sdram_mem_addr = boot_done
                                  ? (sdram_selftest_owns_bus ? SDRAM_SELFTEST_ADDR
                                     : {1'b0, core_mem_addr})
                                  : boot_mem_addr;
            assign sdram_wr_manifold = boot_done
                                     ? (sdram_selftest_owns_bus ? sdram_selftest_wr_manifold : core_mem_wr_data)
                                     : boot_mem_data;

            spu_mem_bridge_sdram #(
                .COL_BITS(SDRAM_COL_BITS),
                .ROW_BITS(SDRAM_ROW_BITS),
                .RANK_BITS(SDRAM_RANK_BITS),
                .XSDS_INVERTED_RANK_CS(SDRAM_XSDS_INVERTED_RANK_CS),
                .T_REFI(SDRAM_REFRESH_CYCLES),
                .READ_CAPTURE_OFFSET(SDRAM_READ_CAPTURE_OFFSET),
                .INVERT_SDRAM_CLK(SDRAM_INVERT_CLK)
            ) u_sdram (
                .clk(clk_core),
                .reset(!rst_n),
                .mem_ready(sdram_ready),
                .mem_burst_rd(sdram_burst_rd),
                .mem_burst_wr(sdram_burst_wr),
                .mem_addr(sdram_bridge_mem_addr),
                .mem_rd_manifold(sdram_rd_manifold),
                .mem_wr_manifold(sdram_wr_manifold),
                .mem_burst_done(sdram_burst_done),
                .sdram_clk(sdram_clk),
                .sdram_cke(), // Hardwired
                .sdram_cs_n(sdram_cs_n),
                .sdram_ras_n(sdram_ras_n),
                .sdram_cas_n(sdram_cas_n),
                .sdram_we_n(sdram_we_n),
                .sdram_ba(sdram_ba),
                .sdram_addr(sdram_addr_bus),
                .sdram_dq(sdram_dq)
            );

            // Physical Mapping of the Address Bus
            assign sdram_a0  = sdram_addr_bus[0];
            assign sdram_a1  = sdram_addr_bus[1];
            assign sdram_a2  = sdram_addr_bus[2];
            assign sdram_a3  = sdram_addr_bus[3];
            assign sdram_a4  = sdram_addr_bus[4];
            assign sdram_a5  = sdram_addr_bus[5];
            assign sdram_a6  = sdram_addr_bus[6];
            assign sdram_a7  = sdram_addr_bus[7];
            assign sdram_a8  = sdram_addr_bus[8];
            assign sdram_a9  = sdram_addr_bus[9];
            assign sdram_a10 = sdram_addr_bus[10];
            assign sdram_a11 = sdram_addr_bus[11];
            assign sdram_a12 = sdram_addr_bus[12];
            assign sdram_dm = 2'b00;
        end else begin : gen_no_sdram
            assign sdram_ready = 1'b1;
            assign sdram_burst_rd = 1'b0;
            assign sdram_burst_wr = 1'b0;
            assign sdram_mem_addr = 25'd0;
            assign sdram_rd_manifold = 832'd0;
            assign sdram_wr_manifold = 832'd0;
            assign sdram_burst_done = 1'b1;

            assign sdram_clk = clk_core;
            assign sdram_cs_n = 1'b1;
            assign sdram_ras_n = 1'b1;
            assign sdram_cas_n = 1'b1;
            assign sdram_we_n = 1'b1;
            assign sdram_ba = 2'b00;
            assign sdram_a0  = 1'b0;
            assign sdram_a1  = 1'b0;
            assign sdram_a2  = 1'b0;
            assign sdram_a3  = 1'b0;
            assign sdram_a4  = 1'b0;
            assign sdram_a5  = 1'b0;
            assign sdram_a6  = 1'b0;
            assign sdram_a7  = 1'b0;
            assign sdram_a8  = 1'b0;
            assign sdram_a9  = 1'b0;
            assign sdram_a10 = 1'b0;
            assign sdram_a11 = 1'b0;
            assign sdram_a12 = 1'b0;
            assign sdram_dq = 16'hzzzz;
            assign sdram_dm = 2'b00;
        end
    endgenerate

    // 5. The Body: SPU-13 Sovereign Core
    wire core_janus;           // from core state machine
    wire        core_hex_valid;
    wire [15:0] core_hex_q;
    wire [15:0] core_hex_r;
    wire [31:0] quadrance_out; // raw quadrance from Davis gate
    wire artery_wr_en;
    wire [63:0] artery_data;

    wire         cycle_wrap;
    wire [3:0]   current_axis_ptr;
    wire [63:0]  current_axis_data;
    wire [831:0] live_manifold;
    wire [51:0]  core_scale_table;
    wire [12:0]  core_scale_overflow;
    wire         core_rplu_dissoc;
    wire [12:0] core_rplu_dissoc_mask;
    wire [9:0]  core_rplu_addr;
    reg          sdram_ready_seen_core;
    reg          sdram_wr_seen_core;
    reg          sdram_done_seen_core;
    wire [3:0]   telemetry_header_status;

    always @(posedge clk_core or negedge rst_n) begin
        if (!rst_n) begin
            core_mem_rd_d <= 1'b0;
            core_mem_wr_d <= 1'b0;
            core_mem_rd_pending <= 1'b0;
            core_mem_wr_pending <= 1'b0;
        end else begin
            core_mem_rd_d <= core_mem_rd;
            core_mem_wr_d <= core_mem_wr;

            if (core_mem_rd && !core_mem_rd_d) begin
                core_mem_rd_pending <= 1'b1;
            end else if (sdram_burst_done && core_mem_rd_pending) begin
                core_mem_rd_pending <= 1'b0;
            end

            if (core_mem_wr && !core_mem_wr_d) begin
                core_mem_wr_pending <= 1'b1;
            end else if (sdram_burst_done && core_mem_wr_pending) begin
                core_mem_wr_pending <= 1'b0;
            end
        end
    end

    assign core_mem_rd_request = core_mem_rd_pending && !sdram_burst_done;
    assign core_mem_wr_request = core_mem_wr_pending && !sdram_burst_done;

    always @(posedge clk_core or negedge rst_n) begin
        if (!rst_n) begin
            sdram_ready_seen_core <= 1'b0;
            sdram_wr_seen_core <= 1'b0;
            sdram_done_seen_core <= 1'b0;
        end else begin
            if (sdram_ready) begin
                sdram_ready_seen_core <= 1'b1;
            end
            if (sdram_burst_wr) begin
                sdram_wr_seen_core <= 1'b1;
            end
            if (sdram_burst_done) begin
                sdram_done_seen_core <= 1'b1;
            end
        end
    end

    assign telemetry_header_status = ENABLE_SDRAM
                                   ? {sdram_ready_seen_core, sdram_wr_seen_core,
                                      sdram_done_seen_core, sdram_selftest_complete}
                                   : ENABLE_CORE_RPLU
                                   ? {1'b1, core_rplu_dissoc, |core_rplu_dissoc_mask, core_rplu_dissoc_mask[0]}
                                   : current_axis_ptr;

    reg [7:0] core_release_cnt;
    always @(posedge clk_core or negedge rst_n) begin
        if (!rst_n) begin
            core_release_cnt <= 8'd0;
        end else if (!boot_done || !sdram_selftest_complete) begin
            core_release_cnt <= 8'd0;
        end else if (core_release_cnt != 8'hFF) begin
            core_release_cnt <= core_release_cnt + 1'b1;
        end
    end
    // ── Instruction Sequencer ──────────────────────────────────
    wire seq_inst_valid;
    wire [63:0] seq_inst_word;
    wire seq_inst_done;
    wire [7:0] seq_pc_raw;
    wire seq_halted_raw;
    spu_sequencer #(.IMEM_DEPTH(64)) u_seq(
        .clk(clk_core), .rst_n(rst_n), .boot_done(boot_done),
        .inst_valid(seq_inst_valid), .inst_word(seq_inst_word),
        .inst_done(seq_inst_done),
        .pc_out(seq_pc_raw), .halted(seq_halted_raw), .program_size()
    );

    wire debug_run_core;
    assign debug_run_core = boot_done && sdram_selftest_complete && (core_release_cnt == 8'hFF);

    spu13_core #(
        .DEVICE("GW5A"),
        .ENABLE_RPLU(ENABLE_CORE_RPLU),
        .ENABLE_LATTICE(ENABLE_CORE_LATTICE),
        .ENABLE_MATH(ENABLE_CORE_MATH),
        .ENABLE_SEQUENCER(1'b0),
        .ENABLE_CORE_SOM(ENABLE_CORE_SOM),
        .ENABLE_CORE_RPLU_V2(ENABLE_CORE_RPLU_V2)
    ) u_core (
        .clk(clk_core),
        .rst_n(rst_n),
        .phi_8(phi_8 && debug_run_core),
        .phi_13(phi_13 && debug_run_core),
        .phi_21(phi_21 && debug_run_core),

        // Config / Phinary Inputs
        .dec_fast_cfg_wr_en(boot_rplu_cfg_wr_en),
        .dec_fast_cfg_sel(boot_rplu_cfg_sel),
        .dec_fast_cfg_material(boot_rplu_cfg_material),
        .dec_fast_cfg_addr(boot_rplu_cfg_addr),
        .dec_fast_cfg_data(boot_rplu_cfg_data),
        .phinary_cfg(16'h0001), // Enable=1, Material=0

        // Prime Hydration (live core hydration restored through lane-local writes)
        .prime_data(prime_data),
        .prime_addr(prime_addr),
        .prime_we(prime_we),
        .boot_done(boot_done),
        .pell_data(pell_data),
        .pell_addr(pell_addr),
        .pell_we(pell_we),

        // Manual Rotor
        .manual_rotor_en(manual_en),
        .manual_rotor_data({rotor_p_reg, rotor_q_reg}),

        // Instruction port (driven by internal sequencer)
        .inst_valid(seq_inst_valid),
        .inst_word(seq_inst_word),
        .inst_done(seq_inst_done),
        .hex_valid(core_hex_valid),
        .hex_q(core_hex_q),
        .hex_r(core_hex_r),

        // Memory Interface
        .mem_ready(sdram_ready),
        .mem_burst_rd(core_mem_rd),
        .mem_burst_wr(core_mem_wr),
        .mem_addr(core_mem_addr),
        .mem_rd_manifold(sdram_rd_manifold_masked),
        .mem_wr_manifold(core_mem_wr_data),
        .mem_burst_done(sdram_burst_done),

        // Telemetry / Status
        .artery_wr_en(artery_wr_en),
        .artery_wr_data(artery_data),
        .is_janus_point(core_janus),
        .bloom_complete(),
        .cycle_wrap(cycle_wrap),
        .current_axis_ptr(current_axis_ptr),
        .current_axis_data(current_axis_data),
        .manifold_out(live_manifold),
        .scale_table_out(core_scale_table),
        .scale_overflow_out(core_scale_overflow),
        .audio_mode(),
        .gasket_sum_out(),
        .quadrance_out(quadrance_out),
        .rplu_dissoc_out(core_rplu_dissoc),
        .rplu_dissoc_mask_out(core_rplu_dissoc_mask),
        .rplu_addr_out(core_rplu_addr),
        .ratio_cmp_res(),
        .ratio_cmp_valid()
    );

    // Piranha Pulse: assert when manifold has energy (quadrance > 0)
    // This bypasses the full RPLU stability scoreboard for bring-up validation.
    wire piranha_pulse;
    assign piranha_pulse = (quadrance_out > 32'h0);

    // 5. Heartbeat & LEDs
    reg [24:0] heartbeat = 0;
    reg pulse_p_last = 0;
    always @(posedge clk_core) begin
        heartbeat <= heartbeat + 1;
        pulse_p_last <= heartbeat[14];
    end
    assign pulse_p_trigger = (heartbeat[14] && !pulse_p_last);

    // Latch host input for display (already handled in flattened logic)
    // LED Assignment:
    // led[0]: Reset Status
    // led[1]: Piranha Pulse Heartbeat
    // led[2]: Host Input Activity (Lower bit)
    // 1Hz blink from raw 27MHz/50MHz crystal
    reg [25:0] sys_blink_cnt = 0;
    always @(posedge clk_50m) sys_blink_cnt <= sys_blink_cnt + 1;
    wire sys_heartbeat = sys_blink_cnt[24]; // ~1.5Hz at 50MHz

    // 1Hz blink from core clock (6.75MHz)
    reg [25:0] core_blink_cnt = 0;
    always @(posedge clk_core) core_blink_cnt <= core_blink_cnt + 1;
    wire core_heartbeat = core_blink_cnt[22]; // ~1.6Hz at 6.75MHz

    assign led[0] = ~sys_heartbeat;  // Blink if crystal is alive
    assign led[1] = ~core_heartbeat; // Blink if divider/core is alive
    assign led[2] = ~boot_done;      // ON during boot, OFF when bloomed

    // 6. UART Telemetry Bridge (115200 Baud)
    // Temporary bring-up mode: hold the core idle after boot and dump the raw
    // 24-bit prime words seen on the bootloader interface before they are
    // written into the hydrated manifold.
    reg [415:0] telemetry_q_cycle;
    reg [415:0] telemetry_q_snap_core;
    reg [415:0] boot_prime_words_core;
    reg [51:0]  telemetry_scale_snap_core;
    reg [12:0]  telemetry_overflow_snap_core;
    reg [12:0]  telemetry_rplu_snap_core;
    reg [9:0]   telemetry_rplu_addr_snap_core;
    reg [9:0]   telemetry_rplu_addr_max_core;
    reg [8:0]   telemetry_rplu_boot_mark_core;
    reg [15:0]  telemetry_rplu_loaded_core;
    reg [31:0]  telemetry_rplu_checksum_core;
    reg [31:0] telemetry_cycle_count_core;
    reg [31:0] telemetry_cycle_count_snap_core;
    reg [5:0]  boot_state_snap_core;
    reg [7:0]  seq_pc_snap_core;
    reg        seq_halted_snap_core;
    reg        telemetry_seq_core;
    reg [3:0]  boot_prime_count_core;
    reg [3:0]  boot_last_prime_addr_core;
    reg [23:0] boot_last_prime_data_core;
    reg [31:0] boot_summary_q_core;
    reg [3:0]  boot_summary_a_core;
    reg        boot_summary_seq_core;
    reg        boot_done_core_d;
    reg [415:0] telemetry_q_tx;
    reg [415:0] telemetry_q_burst;
    reg [51:0]  telemetry_scale_tx;
    reg [12:0]  telemetry_overflow_tx;
    reg [12:0]  telemetry_rplu_tx;
    reg [9:0]   telemetry_rplu_addr_tx;
    reg [8:0]   telemetry_rplu_boot_mark_tx;
    reg [15:0]  telemetry_rplu_loaded_tx;
    reg [31:0]  telemetry_rplu_checksum_tx;
    reg [31:0] telemetry_cycle_count_tx;
    reg [5:0]  boot_state_tx;
    reg [7:0]  seq_pc_tx;
    reg        seq_halted_tx;
    reg [31:0] boot_summary_q_tx;
    reg [3:0]  boot_summary_a_tx;
    reg [31:0] q_latch;
    reg [3:0]  a_latch;
    reg        line_is_header;
    reg        line_is_boot;
    reg        line_is_alive;
    reg        line_is_lattice;
    reg        line_is_rplu;
    reg        line_is_sdram;
    reg        line_is_core;
    reg        boot_done_meta;
    reg        boot_done_tx;
    reg        telemetry_seq_meta;
    reg        telemetry_seq_sync;
    reg        telemetry_seq_seen;
    reg        boot_summary_seq_meta;
    reg        boot_summary_seq_sync;
    reg        boot_summary_seq_seen;
    reg        boot_summary_pending;
    reg [5:0]  boot_summary_repeat_count;
    reg [3:0]  burst_axis_idx;
    reg        burst_active;
    reg        line_launch_pending;

    reg [8:0] tx_data;
    reg [3:0] tx_bit_cnt;
    reg [15:0] tx_clk_cnt;
    reg tx_busy;
    reg tx_out_active_low; // 0 = Idle (1), 1 = Active (0)

    assign uart_tx = !tx_out_active_low;
    assign uart_tx_telemetry = !tx_out_active_low;

    wire [7:0] msg [0:15];
    // When hex_valid pulses, override the message type
    reg        hex_msg_pending;
    reg [15:0] hex_q_latch, hex_r_latch;
    reg [3:0] msg_idx;
    reg [27:0] msg_timer;
    reg [27:0] telemetry_start_cnt;
    reg        telemetry_start_ready;

    always @(posedge clk_core or negedge rst_n) begin
        if (!rst_n) begin
            hex_msg_pending <= 0;
            hex_q_latch <= 0;
            hex_r_latch <= 0;
        end else begin
            if (core_hex_valid && !hex_msg_pending) begin
                hex_q_latch <= core_hex_q;
                hex_r_latch <= core_hex_r;
                hex_msg_pending <= 1;
            end else if (msg_idx == 4'd15) begin
                hex_msg_pending <= 0;
            end
        end
    end

    assign msg[0]  = hex_msg_pending ? "H" : (line_is_core ? "C" : (line_is_alive ? "U" : (line_is_header ? "S" : (line_is_rplu ? "R" : (line_is_sdram ? "M" : (line_is_lattice ? "L" : (line_is_boot ? "B" : "Q")))))));
    assign msg[1]  = ":";
    assign msg[2]  = hex_msg_pending ? hex2ascii(hex_q_latch[15:12]) : hex2ascii(q_latch[31:28]);
    assign msg[3]  = hex_msg_pending ? hex2ascii(hex_q_latch[11:8])  : hex2ascii(q_latch[27:24]);
    assign msg[4]  = hex_msg_pending ? hex2ascii(hex_q_latch[7:4])   : hex2ascii(q_latch[23:20]);
    assign msg[5]  = hex_msg_pending ? hex2ascii(hex_q_latch[3:0])   : hex2ascii(q_latch[19:16]);
    assign msg[6]  = hex_msg_pending ? " "                           : hex2ascii(q_latch[15:12]);
    assign msg[7]  = hex_msg_pending ? hex2ascii(hex_r_latch[15:12]) : hex2ascii(q_latch[11:8]);
    assign msg[8]  = hex_msg_pending ? hex2ascii(hex_r_latch[11:8])  : hex2ascii(q_latch[7:4]);
    assign msg[9]  = hex_msg_pending ? hex2ascii(hex_r_latch[7:4])   : hex2ascii(q_latch[3:0]);
    assign msg[10] = hex_msg_pending ? hex2ascii(hex_r_latch[3:0])   : " ";
    assign msg[11] = hex_msg_pending ? " "                            : (line_is_header ? "C" : "A");
    assign msg[12] = hex_msg_pending ? "("                            : ":";
    assign msg[13] = hex_msg_pending ? hex2ascii(hex_q_latch[15:12]) : hex2ascii(a_latch);
    assign msg[14] = 8'h0D;
    assign msg[15] = 8'h0A;
    reg [7:0] tx_msg_byte;
    always @(*) begin
        case (msg_idx)
            4'd0: tx_msg_byte = msg[0];
            4'd1: tx_msg_byte = msg[1];
            4'd2: tx_msg_byte = msg[2];
            4'd3: tx_msg_byte = msg[3];
            4'd4: tx_msg_byte = msg[4];
            4'd5: tx_msg_byte = msg[5];
            4'd6: tx_msg_byte = msg[6];
            4'd7: tx_msg_byte = msg[7];
            4'd8: tx_msg_byte = msg[8];
            4'd9: tx_msg_byte = msg[9];
            4'd10: tx_msg_byte = msg[10];
            4'd11: tx_msg_byte = msg[11];
            4'd12: tx_msg_byte = msg[12];
            4'd13: tx_msg_byte = msg[13];
            4'd14: tx_msg_byte = msg[14];
            4'd15: tx_msg_byte = msg[15];
            default: tx_msg_byte = 8'h20;
        endcase
    end

    localparam RPLU_TELEMETRY_BURST = ENABLE_CORE_RPLU && (!ENABLE_CORE_LATTICE || ENABLE_RPLU_TELEMETRY);
    localparam SDRAM_SELFTEST_TELEMETRY = ENABLE_SDRAM && ENABLE_SDRAM_SELFTEST;
    localparam CORE_SDRAM_VERIFY_TELEMETRY = ENABLE_SDRAM && ENABLE_CORE_SDRAM_VERIFY;

    task capture_cycle_quadrance;
        input [3:0] axis_idx;
        input [31:0] q_value;
        begin
            case (axis_idx)
                4'd0:  telemetry_q_cycle[0*32 +: 32]   <= q_value;
                4'd1:  telemetry_q_cycle[1*32 +: 32]   <= q_value;
                4'd2:  telemetry_q_cycle[2*32 +: 32]   <= q_value;
                4'd3:  telemetry_q_cycle[3*32 +: 32]   <= q_value;
                4'd4:  telemetry_q_cycle[4*32 +: 32]   <= q_value;
                4'd5:  telemetry_q_cycle[5*32 +: 32]   <= q_value;
                4'd6:  telemetry_q_cycle[6*32 +: 32]   <= q_value;
                4'd7:  telemetry_q_cycle[7*32 +: 32]   <= q_value;
                4'd8:  telemetry_q_cycle[8*32 +: 32]   <= q_value;
                4'd9:  telemetry_q_cycle[9*32 +: 32]   <= q_value;
                4'd10: telemetry_q_cycle[10*32 +: 32]  <= q_value;
                4'd11: telemetry_q_cycle[11*32 +: 32]  <= q_value;
                4'd12: telemetry_q_cycle[12*32 +: 32]  <= q_value;
                default: ;
            endcase
        end
    endtask

    task snapshot_burst_axis;
        input [3:0] axis_idx;
        begin
            case (axis_idx)
                4'd0:  q_latch <= telemetry_q_burst[0*32 +: 32];
                4'd1:  q_latch <= telemetry_q_burst[1*32 +: 32];
                4'd2:  q_latch <= telemetry_q_burst[2*32 +: 32];
                4'd3:  q_latch <= telemetry_q_burst[3*32 +: 32];
                4'd4:  q_latch <= telemetry_q_burst[4*32 +: 32];
                4'd5:  q_latch <= telemetry_q_burst[5*32 +: 32];
                4'd6:  q_latch <= SDRAM_SELFTEST_TELEMETRY ? sdram_selftest_error_mask_word : telemetry_cycle_count_tx;
                4'd7:  q_latch <= CORE_SDRAM_VERIFY_TELEMETRY ? core_sdram_verify_status_word : telemetry_q_burst[7*32 +: 32];
                4'd8:  q_latch <= CORE_SDRAM_VERIFY_TELEMETRY ? core_sdram_verify_wr_checksum : telemetry_q_burst[8*32 +: 32];
                4'd9:  q_latch <= CORE_SDRAM_VERIFY_TELEMETRY ? core_sdram_verify_rd_checksum : telemetry_q_burst[9*32 +: 32];
                4'd10: q_latch <= SDRAM_SELFTEST_TELEMETRY ? sdram_selftest_status_word : telemetry_q_burst[10*32 +: 32];
                4'd11: q_latch <= SDRAM_SELFTEST_TELEMETRY ? sdram_selftest_endpoints_word : telemetry_q_burst[11*32 +: 32];
                4'd12: q_latch <= SDRAM_SELFTEST_TELEMETRY ? sdram_selftest_checksum : telemetry_q_burst[12*32 +: 32];
                4'd13: q_latch <= RPLU_TELEMETRY_BURST ? {telemetry_rplu_boot_mark_tx, telemetry_rplu_tx, telemetry_rplu_addr_tx} : telemetry_scale_tx[31:0];
                4'd14: q_latch <= RPLU_TELEMETRY_BURST ? {16'd0, telemetry_rplu_loaded_tx} : {12'd0, telemetry_scale_tx[51:32]};
                4'd15: q_latch <= RPLU_TELEMETRY_BURST ? telemetry_rplu_checksum_tx : {19'd0, telemetry_overflow_tx};
                default: q_latch <= 32'd0;
            endcase
        end
    endtask

    always @(posedge clk_core) begin
        if (!rst_n) begin
            telemetry_q_cycle <= 416'd0;
            telemetry_q_snap_core <= 416'd0;
            boot_prime_words_core <= 416'd0;
            telemetry_scale_snap_core <= 52'd0;
            telemetry_overflow_snap_core <= 13'd0;
            telemetry_rplu_snap_core <= 13'd0;
            telemetry_rplu_addr_snap_core <= 10'd0;
            telemetry_rplu_addr_max_core <= 10'd0;
            telemetry_rplu_boot_mark_core <= 9'd0;
            telemetry_rplu_loaded_core <= 16'd0;
            telemetry_rplu_checksum_core <= 32'd0;
            telemetry_cycle_count_core <= 32'd0;
            telemetry_cycle_count_snap_core <= 32'd0;
            telemetry_seq_core <= 1'b0;
            boot_prime_count_core <= 4'd0;
            boot_last_prime_addr_core <= 4'd0;
            boot_last_prime_data_core <= 24'd0;
            boot_summary_q_core <= 32'd0;
            boot_summary_a_core <= 4'd0;
            boot_summary_seq_core <= 1'b0;
            boot_done_core_d <= 1'b0;
        end else begin
            boot_done_core_d <= boot_done;

            if (!boot_done && prime_we) begin
                boot_prime_count_core <= prime_addr + 1'b1;
                boot_last_prime_addr_core <= prime_addr;
                boot_last_prime_data_core <= prime_data;
                case (prime_addr)
                    4'd0:  boot_prime_words_core[0*32 +: 32]  <= {8'd0, prime_data};
                    4'd1:  boot_prime_words_core[1*32 +: 32]  <= {8'd0, prime_data};
                    4'd2:  boot_prime_words_core[2*32 +: 32]  <= {8'd0, prime_data};
                    4'd3:  boot_prime_words_core[3*32 +: 32]  <= {8'd0, prime_data};
                    4'd4:  boot_prime_words_core[4*32 +: 32]  <= {8'd0, prime_data};
                    4'd5:  boot_prime_words_core[5*32 +: 32]  <= {8'd0, prime_data};
                    4'd6:  boot_prime_words_core[6*32 +: 32]  <= {8'd0, prime_data};
                    4'd7:  boot_prime_words_core[7*32 +: 32]  <= {8'd0, prime_data};
                    4'd8:  boot_prime_words_core[8*32 +: 32]  <= {8'd0, prime_data};
                    4'd9:  boot_prime_words_core[9*32 +: 32]  <= {8'd0, prime_data};
                    4'd10: boot_prime_words_core[10*32 +: 32] <= {8'd0, prime_data};
                    4'd11: boot_prime_words_core[11*32 +: 32] <= {8'd0, prime_data};
                    4'd12: boot_prime_words_core[12*32 +: 32] <= {8'd0, prime_data};
                    default: ;
                endcase
            end

            if (!boot_done_core_d && boot_done) begin
                boot_summary_q_core <= {boot_prime_count_core, 4'h0, boot_jedec_id};
                boot_summary_a_core <= boot_last_prime_addr_core;
                boot_summary_seq_core <= ~boot_summary_seq_core;
                telemetry_q_snap_core <= boot_prime_words_core;
                telemetry_cycle_count_snap_core <= 32'd0;
                telemetry_rplu_boot_mark_core <= (boot_rplu_cfg_loaded != 16'd0) ? 9'h1A5 : 9'd0;
                telemetry_rplu_loaded_core <= boot_rplu_cfg_loaded;
                telemetry_rplu_checksum_core <= boot_rplu_cfg_checksum;
                telemetry_seq_core <= ~telemetry_seq_core;
            end

            if (debug_run_core) begin
                if (core_rplu_addr > telemetry_rplu_addr_max_core) begin
                    telemetry_rplu_addr_max_core <= core_rplu_addr;
                end

                if (phi_21) begin
                    capture_cycle_quadrance(current_axis_ptr, quadrance_out);
                    if (current_axis_ptr == 4'd12) begin
                        telemetry_cycle_count_core <= telemetry_cycle_count_core + 1'b1;
                        telemetry_cycle_count_snap_core <= telemetry_cycle_count_core + 1'b1;
                        telemetry_q_snap_core <= {quadrance_out, telemetry_q_cycle[383:0]};
                        telemetry_scale_snap_core <= core_scale_table;
                        telemetry_overflow_snap_core <= core_scale_overflow;
                        telemetry_rplu_snap_core <= core_rplu_dissoc_mask;
                        telemetry_rplu_addr_snap_core <= (core_rplu_addr > telemetry_rplu_addr_max_core) ? core_rplu_addr : telemetry_rplu_addr_max_core;
                        boot_state_snap_core <= boot_state;
                        seq_pc_snap_core <= seq_pc_raw;
                        seq_halted_snap_core <= seq_halted_raw;
                        telemetry_seq_core <= ~telemetry_seq_core;
                    end
                end
            end
        end
    end

    function [7:0] hex2ascii;
        input [3:0] hex;
        begin
            hex2ascii = (hex < 10) ? (8'h30 + hex) : (8'h37 + hex);
        end
    endfunction

    // Unified Synchronous Zero-Reset Logic
    always @(posedge clk_50m) begin
        if (!rst_n) begin
            msg_idx <= 0;
            msg_timer <= 0;
            tx_busy <= 0;
            tx_out_active_low <= 0; // 0 = Idle (Physical 1)
            tx_clk_cnt <= 0;
            tx_bit_cnt <= 0;
            tx_data <= 0;
            telemetry_q_tx <= 416'd0;
            telemetry_q_burst <= 416'd0;
            telemetry_scale_tx <= 52'd0;
            telemetry_overflow_tx <= 13'd0;
            telemetry_rplu_tx <= 13'd0;
            telemetry_rplu_addr_tx <= 10'd0;
            telemetry_rplu_boot_mark_tx <= 9'd0;
            telemetry_rplu_loaded_tx <= 16'd0;
            telemetry_rplu_checksum_tx <= 32'd0;
            telemetry_cycle_count_tx <= 32'd0;
            boot_summary_q_tx <= 32'd0;
            boot_summary_a_tx <= 4'd0;
            q_latch <= 32'd0;
            a_latch <= 4'd0;
            line_is_header <= 1'b0;
            line_is_boot <= 1'b0;
            line_is_alive <= 1'b0;
            line_is_lattice <= 1'b0;
            line_is_rplu <= 1'b0;
            line_is_sdram <= 1'b0;
            line_is_core <= 1'b0;
            boot_done_meta <= 1'b0;
            boot_done_tx <= 1'b0;
            telemetry_seq_meta <= 1'b0;
            telemetry_seq_sync <= 1'b0;
            telemetry_seq_seen <= 1'b0;
            boot_summary_seq_meta <= 1'b0;
            boot_summary_seq_sync <= 1'b0;
            boot_summary_seq_seen <= 1'b0;
            boot_summary_pending <= 1'b0;
            boot_summary_repeat_count <= 6'd0;
            burst_axis_idx <= 4'd0;
            burst_active <= 1'b0;
            line_launch_pending <= 1'b0;
            telemetry_start_cnt <= 28'd0;
            telemetry_start_ready <= 1'b0;
        end else begin
            boot_done_meta <= boot_done;
            boot_done_tx <= boot_done_meta;
            telemetry_seq_meta <= telemetry_seq_core;
            telemetry_seq_sync <= telemetry_seq_meta;
            boot_summary_seq_meta <= boot_summary_seq_core;
            boot_summary_seq_sync <= boot_summary_seq_meta;

            if (telemetry_seq_sync != telemetry_seq_seen) begin
                telemetry_seq_seen <= telemetry_seq_sync;
                telemetry_q_tx <= telemetry_q_snap_core;
                telemetry_scale_tx <= telemetry_scale_snap_core;
                telemetry_overflow_tx <= telemetry_overflow_snap_core;
                telemetry_rplu_tx <= telemetry_rplu_snap_core;
                telemetry_rplu_addr_tx <= telemetry_rplu_addr_snap_core;
                telemetry_rplu_boot_mark_tx <= telemetry_rplu_boot_mark_core;
                telemetry_rplu_loaded_tx <= telemetry_rplu_loaded_core;
                telemetry_rplu_checksum_tx <= telemetry_rplu_checksum_core;
                telemetry_cycle_count_tx <= telemetry_cycle_count_snap_core;
                boot_state_tx <= boot_state_snap_core;
                seq_pc_tx <= seq_pc_snap_core;
                seq_halted_tx <= seq_halted_snap_core;
            end

            if (boot_summary_seq_sync != boot_summary_seq_seen) begin
                boot_summary_seq_seen <= boot_summary_seq_sync;
                boot_summary_q_tx <= boot_summary_q_core;
                boot_summary_a_tx <= boot_summary_a_core;
                boot_summary_pending <= 1'b1;
                boot_summary_repeat_count <= 6'd30;
                msg_timer <= 28'd0;
            end

            if (!telemetry_start_ready) begin
                tx_busy <= 1'b0;
                tx_out_active_low <= 1'b0;
                msg_idx <= 4'd0;
                msg_timer <= 28'd0;
                burst_active <= 1'b0;
                line_launch_pending <= 1'b0;
                if (telemetry_start_cnt < UART_TX_START_DELAY - 1) begin
                    telemetry_start_cnt <= telemetry_start_cnt + 1'b1;
                end else begin
                    telemetry_start_ready <= 1'b1;
                end
            end else if (!tx_busy) begin
                tx_out_active_low <= 0; // Idle
                if (line_launch_pending) begin
                    line_launch_pending <= 1'b0;
                    tx_data <= {1'b1, tx_msg_byte};
                    tx_busy <= 1'b1;
                    tx_bit_cnt <= 4'd0;
                    tx_clk_cnt <= 16'd0;
                    tx_out_active_low <= 1'b1; // Start bit (Physical 0)
                end else if (msg_idx == 0) begin
                    if (!burst_active) begin
                        if (boot_summary_pending) begin
                            q_latch <= boot_summary_q_tx;
                            a_latch <= boot_summary_a_tx;
                            line_is_header <= 1'b0;
                            line_is_boot <= 1'b1;
                            line_is_alive <= 1'b0;
                            line_is_lattice <= 1'b0;
                            line_is_rplu <= 1'b0;
                            line_is_sdram <= 1'b0;
                            line_launch_pending <= 1'b1;
                            boot_summary_pending <= 1'b0;
                            if (boot_summary_repeat_count != 6'd0) begin
                                boot_summary_repeat_count <= boot_summary_repeat_count - 1'b1;
                            end
                            msg_timer <= 28'd0;
                        end else if (boot_summary_repeat_count != 6'd0) begin
                            if (msg_timer < UART_TX_BOOT_PERIOD) begin
                                msg_timer <= msg_timer + 1'b1;
                            end else begin
                                msg_timer <= 28'd0;
                                q_latch <= boot_summary_q_tx;
                                a_latch <= boot_summary_a_tx;
                                line_is_header <= 1'b0;
                                line_is_boot <= 1'b1;
                                line_is_alive <= 1'b0;
                                line_is_lattice <= 1'b0;
                                line_is_rplu <= 1'b0;
                                line_is_sdram <= 1'b0;
                                line_launch_pending <= 1'b1;
                                boot_summary_repeat_count <= boot_summary_repeat_count - 1'b1;
                            end
                        end else if (!boot_done_tx) begin
                            if (msg_timer < UART_TX_MSG_PERIOD) begin
                                msg_timer <= msg_timer + 1'b1;
                            end else begin
                                msg_timer <= 28'd0;
                                // Core status while booting: [23:18]=boot_state, [15:8]=PC, [0]=halted
                                q_latch <= {8'd0, boot_state_tx, seq_pc_tx, 7'd0, seq_halted_tx};
                                a_latch <= {3'd0, boot_done_tx};
                                line_is_header <= 1'b0;
                                line_is_boot <= 1'b0;
                                line_is_alive <= 1'b0;
                                line_is_core <= 1'b1;
                                line_is_lattice <= 1'b0;
                                line_is_rplu <= 1'b0;
                                line_is_sdram <= 1'b0;
                                line_launch_pending <= 1'b1;
                            end
                        end else if (msg_timer < UART_TX_MSG_PERIOD) begin
                            msg_timer <= msg_timer + 1'b1;
                        end else begin
                            msg_timer <= 28'd0;
                            burst_active <= 1'b1;
                            burst_axis_idx <= (ENABLE_CORE_LATTICE || ENABLE_CORE_RPLU) ? 4'd13 : 4'd0;
                            telemetry_q_burst <= telemetry_q_tx;
                            // Header Status: [23:18]=boot_state, [15:8]=PC, [0]=halted
                            q_latch <= {8'd0, boot_state_tx, seq_pc_tx, 7'd0, seq_halted_tx};
                            a_latch <= telemetry_header_status;
                            line_is_header <= 1'b1;
                            line_is_boot <= 1'b0;
                            line_is_alive <= 1'b0;
                            line_is_lattice <= 1'b0;
                            line_is_rplu <= 1'b0;
                            line_is_sdram <= 1'b0;
                            line_launch_pending <= 1'b1;
                        end
                    end else begin
                        snapshot_burst_axis(burst_axis_idx);
                        a_latch <= burst_axis_idx;
                        line_is_header <= 1'b0;
                        line_is_boot <= 1'b0;
                        line_is_alive <= 1'b0;
                        line_is_rplu <= (RPLU_TELEMETRY_BURST && (burst_axis_idx >= 4'd13));
                        line_is_sdram <= (SDRAM_SELFTEST_TELEMETRY && (burst_axis_idx == 4'd6))
                                      || (CORE_SDRAM_VERIFY_TELEMETRY && (burst_axis_idx >= 4'd7) && (burst_axis_idx <= 4'd9))
                                      || (SDRAM_SELFTEST_TELEMETRY && (burst_axis_idx >= 4'd10) && (burst_axis_idx <= 4'd12));
                        line_is_lattice <= (burst_axis_idx >= 4'd13) && !(RPLU_TELEMETRY_BURST && (burst_axis_idx >= 4'd13));
                        line_launch_pending <= 1'b1;
                    end
                end else begin
                    tx_data <= {1'b1, tx_msg_byte};
                    tx_busy <= 1'b1;
                    tx_bit_cnt <= 4'd0;
                    tx_clk_cnt <= 16'd0;
                    tx_out_active_low <= 1'b1; // Start bit (Physical 0)
                end
            end else begin
                if (tx_clk_cnt < UART_TX_CLKS_PER_BIT - 1) begin
                    tx_clk_cnt <= tx_clk_cnt + 1'b1;
                end else begin
                    tx_clk_cnt <= 16'd0;
                    if (tx_bit_cnt < 9) begin
                        if (tx_bit_cnt < 8) begin
                            tx_out_active_low <= !tx_data[0];
                            tx_data <= {1'b0, tx_data[8:1]};
                        end else begin
                            tx_out_active_low <= 1'b0; // Stop bit (Physical 1)
                        end
                        tx_bit_cnt <= tx_bit_cnt + 1'b1;
                    end else begin
                        tx_busy <= 1'b0;
                        tx_out_active_low <= 1'b0; // Idle
                        if (msg_idx == 15) begin
                            msg_idx <= 4'd0;
                            if (line_is_header) begin
                                burst_axis_idx <= burst_axis_idx;
                            end else if (RPLU_TELEMETRY_BURST && (burst_axis_idx == 4'd15)) begin
                                burst_axis_idx <= 4'd0;
                            end else if (RPLU_TELEMETRY_BURST && (burst_axis_idx >= 4'd13)) begin
                                burst_axis_idx <= burst_axis_idx + 1'b1;
                            end else if (burst_axis_idx == 4'd12) begin
                                burst_axis_idx <= 4'd0;
                                burst_active <= 1'b0;
                            end else if (burst_axis_idx == 4'd15) begin
                                burst_axis_idx <= 4'd0;
                            end else begin
                                burst_axis_idx <= burst_axis_idx + 1'b1;
                            end
                        end else begin
                            msg_idx <= msg_idx + 1'b1;
                        end
                    end
                end
            end
        end
    end

endmodule

// Simple UART Receiver for Host Input - Removed (Logic flattened into top)

// Gowin Hardware Primitive Blackbox (Only BUFG needed)
(* blackbox *)
module BUFG (
    input I,
    output O
);
endmodule

// Gowin Hardware Primitive Blackbox removed - no longer needed for async ascension
