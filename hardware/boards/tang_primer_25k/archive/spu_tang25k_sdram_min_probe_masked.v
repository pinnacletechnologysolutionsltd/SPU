// Minimal Tang Primer 25K SDRAM read/write probe.
//
// Uses the production SDRAM bridge, but removes the SPU core and flash
// bootloader from the build. UART emits:
//   M:<status>    A:A
//   M:<endpoints> A:B
//   M:<checksum>  A:C
//   M:<errmask>   A:6

`include "spu_arch_defines.vh"

module spu_tang25k_sdram_min_probe_masked #(
    parameter SDRAM_COL_BITS = 9,
    parameter SDRAM_ROW_BITS = 13,
    parameter SDRAM_RANK_BITS = 1,
    parameter SDRAM_XSDS_INVERTED_RANK_CS = 1,
    parameter SDRAM_REFRESH_CYCLES = 49,
    parameter SDRAM_READ_CAPTURE_OFFSET = 3,
    parameter SDRAM_INVERT_CLK = 1,
    parameter [15:0] DQ_STUCK_MASK = 16'h0402
) (
    input  wire        sys_clk,
    output wire [2:0]  led,
    output wire        uart_tx,
    output wire        uart_tx_telemetry,

    output wire        sdram_clk,
    output wire        sdram_cs_n,
    output wire        sdram_ras_n,
    output wire        sdram_cas_n,
    output wire        sdram_we_n,
    output wire [1:0]  sdram_ba,
    output wire        sdram_a0,
    output wire        sdram_a1,
    output wire        sdram_a2,
    output wire        sdram_a3,
    output wire        sdram_a4,
    output wire        sdram_a5,
    output wire        sdram_a6,
    output wire        sdram_a7,
    output wire        sdram_a8,
    output wire        sdram_a9,
    output wire        sdram_a10,
    output wire        sdram_a11,
    output wire        sdram_a12,
    inout  wire [15:0] sdram_dq,
    output wire [1:0]  sdram_dm
);
    localparam integer UART_CLKS_PER_BIT = 434;       // 50 MHz / 115200
    localparam integer UART_LINE_PERIOD  = 5_000_000; // 100 ms at 50 MHz
    localparam integer SDRAM_RANK_SELECT_BIT = SDRAM_COL_BITS + SDRAM_ROW_BITS + 2;
    localparam [24:0] TEST_ADDR_25 =
        (SDRAM_RANK_BITS != 0) ? (25'h000A040 | (25'd1 << SDRAM_RANK_SELECT_BIT))
                               : 25'h01A040;
    localparam [11:0] TEST_TIMEOUT = 12'hFFF;

    wire clk_50m;
    BUFG u_bufg_50m (.I(sys_clk), .O(clk_50m));

    reg [5:0] clk_div = 6'd0;
    always @(posedge clk_50m) clk_div <= clk_div + 1'b1;

    wire clk_sdram_raw = clk_div[2]; // 6.25 MHz, matching the SPU probe top.
    wire clk_sdram;
    BUFG u_bufg_sdram (.I(clk_sdram_raw), .O(clk_sdram));

    reg [7:0] rst_cnt = 8'd0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge clk_sdram) begin
        if (!rst_n) rst_cnt <= rst_cnt + 1'b1;
    end

    function [15:0] test_pattern;
        input [5:0] idx;
        begin
            test_pattern = 16'hA55A ^ {idx, ~idx, idx[3:0]};
        end
    endfunction

    reg [`MANIFOLD_WIDTH-1:0] wr_manifold;
    integer pattern_i;
    always @(*) begin
        wr_manifold = {`MANIFOLD_WIDTH{1'b0}};
        for (pattern_i = 0; pattern_i < 52; pattern_i = pattern_i + 1) begin
            wr_manifold[pattern_i * 16 +: 16] = test_pattern(pattern_i[5:0]);
        end
    end

    wire sdram_ready;
    reg  burst_rd = 1'b0;
    reg  burst_wr = 1'b0;
    wire [`MANIFOLD_WIDTH-1:0] rd_manifold;
    wire burst_done;
    wire [12:0] sdram_addr_bus;
    wire [SDRAM_COL_BITS+SDRAM_ROW_BITS+SDRAM_RANK_BITS+1:0] mem_addr =
        TEST_ADDR_25[SDRAM_COL_BITS+SDRAM_ROW_BITS+SDRAM_RANK_BITS+1:0];

    spu_mem_bridge_sdram #(
        .COL_BITS(SDRAM_COL_BITS),
        .ROW_BITS(SDRAM_ROW_BITS),
        .RANK_BITS(SDRAM_RANK_BITS),
        .XSDS_INVERTED_RANK_CS(SDRAM_XSDS_INVERTED_RANK_CS),
        .T_REFI(SDRAM_REFRESH_CYCLES),
        .READ_CAPTURE_OFFSET(SDRAM_READ_CAPTURE_OFFSET),
        .INVERT_SDRAM_CLK(SDRAM_INVERT_CLK)
    ) u_sdram (
        .clk(clk_sdram),
        .reset(!rst_n),
        .mem_ready(sdram_ready),
        .mem_burst_rd(burst_rd),
        .mem_burst_wr(burst_wr),
        .mem_addr(mem_addr),
        .mem_rd_manifold(rd_manifold),
        .mem_wr_manifold(wr_manifold),
        .mem_burst_done(burst_done),
        .sdram_clk(sdram_clk),
        .sdram_cke(),
        .sdram_cs_n(sdram_cs_n),
        .sdram_ras_n(sdram_ras_n),
        .sdram_cas_n(sdram_cas_n),
        .sdram_we_n(sdram_we_n),
        .sdram_ba(sdram_ba),
        .sdram_addr(sdram_addr_bus),
        .sdram_dq(sdram_dq)
    );

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
    assign sdram_dm  = 2'b00;

    reg        match_calc;
    reg [5:0]  mismatch_calc;
    reg [31:0] checksum_calc;
    reg [15:0] exp0_obs1_mask_calc;
    reg [15:0] exp1_obs0_mask_calc;
    integer check_i;
    always @(*) begin
        match_calc = 1'b1;
        mismatch_calc = 6'd0;
        checksum_calc = 32'd0;
        exp0_obs1_mask_calc = 16'd0;
        exp1_obs0_mask_calc = 16'd0;
        for (check_i = 0; check_i < 52; check_i = check_i + 1) begin
            checksum_calc = checksum_calc + {16'd0, rd_manifold[check_i * 16 +: 16]};
            exp0_obs1_mask_calc = exp0_obs1_mask_calc
                                 | (~test_pattern(check_i[5:0])
                                    & rd_manifold[check_i * 16 +: 16]);
            exp1_obs0_mask_calc = exp1_obs0_mask_calc
                                 | (test_pattern(check_i[5:0])
                                    & ~rd_manifold[check_i * 16 +: 16]);
            if ((rd_manifold[check_i * 16 +: 16] | DQ_STUCK_MASK) != (test_pattern(check_i[5:0]) | DQ_STUCK_MASK)) begin
                match_calc = 1'b0;
                if (mismatch_calc != 6'h3F) mismatch_calc = mismatch_calc + 1'b1;
            end
        end
    end

    localparam ST_IDLE       = 3'd0;
    localparam ST_WRITE      = 3'd1;
    localparam ST_WAIT_WRITE = 3'd2;
    localparam ST_READ       = 3'd3;
    localparam ST_WAIT_READ  = 3'd4;
    localparam ST_DONE       = 3'd5;

    reg [2:0]  state = ST_IDLE;
    reg [11:0] wait_cnt = 12'd0;
    reg [11:0] ready_wait = 12'd0;
    reg [3:0]  retries = 4'd0;
    reg        done = 1'b0;
    reg        pass = 1'b0;
    reg        fail = 1'b0;
    reg        wr_done = 1'b0;
    reg        rd_done = 1'b0;
    reg [5:0]  mismatch_count = 6'd0;
    reg [15:0] first_word = 16'd0;
    reg [15:0] last_word = 16'd0;
    reg [31:0] checksum = 32'd0;
    reg [15:0] exp0_obs1_mask = 16'd0;
    reg [15:0] exp1_obs0_mask = 16'd0;

    always @(posedge clk_sdram) begin
        if (!rst_n) begin
            burst_rd <= 1'b0;
            burst_wr <= 1'b0;
            state <= ST_IDLE;
            wait_cnt <= 12'd0;
            ready_wait <= 12'd0;
            retries <= 4'd0;
            done <= 1'b0;
            pass <= 1'b0;
            fail <= 1'b0;
            wr_done <= 1'b0;
            rd_done <= 1'b0;
            mismatch_count <= 6'd0;
            first_word <= 16'd0;
            last_word <= 16'd0;
            checksum <= 32'd0;
            exp0_obs1_mask <= 16'd0;
            exp1_obs0_mask <= 16'd0;
        end else begin
            burst_rd <= 1'b0;
            burst_wr <= 1'b0;

            case (state)
                ST_IDLE: begin
                    if (sdram_ready) begin
                        if (ready_wait == 12'h3FF) begin
                            state <= ST_WRITE;
                        end else begin
                            ready_wait <= ready_wait + 1'b1;
                        end
                    end
                end

                ST_WRITE: begin
                    burst_wr <= 1'b1;
                    wait_cnt <= 12'd0;
                    state <= ST_WAIT_WRITE;
                end

                ST_WAIT_WRITE: begin
                    if (burst_done) begin
                        wr_done <= 1'b1;
                        retries <= 4'd0;
                        wait_cnt <= 12'd0;
                        state <= ST_READ;
                    end else if (wait_cnt == TEST_TIMEOUT) begin
                        if (retries == 4'hF) begin
                            done <= 1'b1;
                            fail <= 1'b1;
                            state <= ST_DONE;
                        end else begin
                            retries <= retries + 1'b1;
                            wait_cnt <= 12'd0;
                            state <= ST_WRITE;
                        end
                    end else begin
                        wait_cnt <= wait_cnt + 1'b1;
                    end
                end

                ST_READ: begin
                    burst_rd <= 1'b1;
                    wait_cnt <= 12'd0;
                    state <= ST_WAIT_READ;
                end

                ST_WAIT_READ: begin
                    if (burst_done) begin
                        rd_done <= 1'b1;
                        done <= 1'b1;
                        pass <= match_calc;
                        fail <= !match_calc;
                        mismatch_count <= mismatch_calc;
                        first_word <= rd_manifold[15:0];
                        last_word <= rd_manifold[831:816];
                        checksum <= checksum_calc;
                        exp0_obs1_mask <= exp0_obs1_mask_calc;
                        exp1_obs0_mask <= exp1_obs0_mask_calc;
                        state <= ST_DONE;
                    end else if (wait_cnt == TEST_TIMEOUT) begin
                        if (retries == 4'hF) begin
                            done <= 1'b1;
                            fail <= 1'b1;
                            state <= ST_DONE;
                        end else begin
                            retries <= retries + 1'b1;
                            wait_cnt <= 12'd0;
                            state <= ST_READ;
                        end
                    end else begin
                        wait_cnt <= wait_cnt + 1'b1;
                    end
                end

                default: begin
                    state <= ST_DONE;
                end
            endcase
        end
    end

    wire [31:0] status_word = {
        8'h5D, 8'hA5,
        done,
        pass,
        fail,
        wr_done,
        rd_done,
        state,
        2'b00,
        mismatch_count
    };
    wire [31:0] endpoints_word = {first_word, last_word};
    wire [31:0] error_mask_word = {exp1_obs0_mask, exp0_obs1_mask};

    assign led[0] = ~sdram_ready;
    assign led[1] = ~pass;
    assign led[2] = ~fail;

    function [7:0] hex_digit;
        input [3:0] value;
        begin
            hex_digit = (value < 4'd10) ? (8'h30 + value) : (8'h41 + value - 4'd10);
        end
    endfunction

    reg [31:0] line_word = 32'd0;
    reg [3:0]  line_axis = 4'd10;
    reg [1:0]  report_sel = 2'd0;
    reg [22:0] line_timer = 23'd0;
    reg        emit_line = 1'b0;

    always @(posedge clk_50m) begin
        emit_line <= 1'b0;
        if (line_timer == UART_LINE_PERIOD - 1) begin
            line_timer <= 23'd0;
            emit_line <= 1'b1;
            case (report_sel)
                2'd0: begin line_word <= status_word;    line_axis <= 4'hA; end
                2'd1: begin line_word <= endpoints_word; line_axis <= 4'hB; end
                2'd2: begin line_word <= checksum;       line_axis <= 4'hC; end
                default: begin line_word <= error_mask_word; line_axis <= 4'h6; end
            endcase
            report_sel <= report_sel + 1'b1;
        end else begin
            line_timer <= line_timer + 1'b1;
        end
    end

    reg [3:0] msg_idx = 4'd0;
    reg [7:0] tx_byte = 8'h00;
    reg [9:0] tx_shift = 10'h3FF;
    reg [15:0] baud_cnt = 16'd0;
    reg [3:0] bit_cnt = 4'd0;
    reg tx_busy = 1'b0;
    reg line_pending = 1'b0;

    assign uart_tx = tx_shift[0];
    assign uart_tx_telemetry = tx_shift[0];

    always @(*) begin
        case (msg_idx)
            4'd0:  tx_byte = "M";
            4'd1:  tx_byte = ":";
            4'd2:  tx_byte = hex_digit(line_word[31:28]);
            4'd3:  tx_byte = hex_digit(line_word[27:24]);
            4'd4:  tx_byte = hex_digit(line_word[23:20]);
            4'd5:  tx_byte = hex_digit(line_word[19:16]);
            4'd6:  tx_byte = hex_digit(line_word[15:12]);
            4'd7:  tx_byte = hex_digit(line_word[11:8]);
            4'd8:  tx_byte = hex_digit(line_word[7:4]);
            4'd9:  tx_byte = hex_digit(line_word[3:0]);
            4'd10: tx_byte = " ";
            4'd11: tx_byte = "A";
            4'd12: tx_byte = ":";
            4'd13: tx_byte = hex_digit(line_axis);
            4'd14: tx_byte = 8'h0D;
            4'd15: tx_byte = 8'h0A;
            default: tx_byte = 8'h20;
        endcase
    end

    always @(posedge clk_50m) begin
        if (emit_line) begin
            line_pending <= 1'b1;
        end

        if (tx_busy) begin
            if (baud_cnt < UART_CLKS_PER_BIT - 1) begin
                baud_cnt <= baud_cnt + 1'b1;
            end else begin
                baud_cnt <= 16'd0;
                tx_shift <= {1'b1, tx_shift[9:1]};
                if (bit_cnt == 4'd9) begin
                    tx_busy <= 1'b0;
                    bit_cnt <= 4'd0;
                    if (msg_idx == 4'd15) begin
                        msg_idx <= 4'd0;
                    end else begin
                        msg_idx <= msg_idx + 1'b1;
                    end
                end else begin
                    bit_cnt <= bit_cnt + 1'b1;
                end
            end
        end else if (line_pending) begin
            tx_shift <= {1'b1, tx_byte, 1'b0};
            tx_busy <= 1'b1;
            baud_cnt <= 16'd0;
            bit_cnt <= 4'd0;
            if (msg_idx == 4'd15) begin
                line_pending <= 1'b0;
            end
        end
    end
endmodule

(* blackbox *)
module BUFG (
    input I,
    output O
);
endmodule
