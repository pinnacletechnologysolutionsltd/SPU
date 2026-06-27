// spu13_tang25k_rplu2_consume_probe.v -- J4 flash to RPLU2 decode/Quadray proof.
//
// This Tang-sized probe deliberately stops short of the full Padé/inverter
// pipeline.  It proves the corrected RPLU2 records are consumed by live FPGA
// logic:
//   PMOD J4 flash -> laminar boot config stream -> decoded Padé/BTU/kappa
//   registers -> UART proof lines.
//
// Full Padé/inverter table-consumption should be proven on Artix-7 or after
// the A31 datapath is resource-optimized for the 25K.
module spu13_tang25k_rplu2_consume_probe (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx,
    output wire       uart_tx_telemetry,
    output wire       flash_cs,
    output wire       flash_sck,
    output wire       flash_mosi,
    input  wire       flash_miso
);
    localparam integer CLK_FREQ       = 50000000;
    localparam integer CLKS_PER_BIT   = 434;
    localparam integer START_DELAY    = CLK_FREQ / 2;
    localparam integer LINE_PERIOD    = CLK_FREQ / 5;
    localparam [15:0] RPLU2_RECORDS   = 16'd149;
    localparam [31:0] RPLU2_MARK_WORD = {9'h1A5, 13'd0, 10'h3FF};
    localparam [31:0] EXPECTED_CHECKSUM = 32'h0AA480E7;
    localparam [31:0] EXPECTED_NUM0_C0 = 32'd2;
    localparam [31:0] EXPECTED_QUADRAY_DELTA = 32'd0;
    localparam [31:0] CONSUME_PASS_WORD = 32'hC02E0001;
    localparam [31:0] CONSUME_FAIL_WORD = 32'hC02E0000;

    reg [7:0] rst_cnt = 8'd0;
    wire rst_n = (rst_cnt == 8'hFF);

    always @(posedge sys_clk) begin
        if (!rst_n)
            rst_cnt <= rst_cnt + 1'b1;
    end

    wire [23:0] jedec_id;
    wire [23:0] prime_data;
    wire [3:0]  prime_addr;
    wire        prime_we;
    wire [31:0] pell_data;
    wire [2:0]  pell_addr;
    wire        pell_we;
    wire        rplu_cfg_wr_en;
    wire [2:0]  rplu_cfg_sel;
    wire [7:0]  rplu_cfg_material;
    wire [9:0]  rplu_cfg_addr;
    wire [63:0] rplu_cfg_data;
    wire [15:0] rplu_cfg_loaded;
    wire [31:0] rplu_cfg_checksum;
    wire        boot_done;
    wire [5:0]  boot_state;

    spu_laminar_boot #(
        .ENABLE_RPLU_BOOT(1),
        .RPLU_CFG_RECORDS(RPLU2_RECORDS),
        .SPI_SCK_HALF_CYCLES(32)
    ) u_boot (
        .clk(sys_clk),
        .rst_n(rst_n),
        .flash_cs(flash_cs),
        .flash_sck(flash_sck),
        .flash_miso(flash_miso),
        .flash_mosi(flash_mosi),
        .jedec_id(jedec_id),
        .bram_data(prime_data),
        .bram_addr(prime_addr),
        .bram_we(prime_we),
        .pell_data(pell_data),
        .pell_addr(pell_addr),
        .pell_we(pell_we),
        .mem_burst_wr(),
        .mem_addr(),
        .mem_wr_manifold(),
        .mem_burst_done(1'b1),
        .rplu_cfg_wr_en(rplu_cfg_wr_en),
        .rplu_cfg_sel(rplu_cfg_sel),
        .rplu_cfg_material(rplu_cfg_material),
        .rplu_cfg_addr(rplu_cfg_addr),
        .rplu_cfg_data(rplu_cfg_data),
        .rplu_cfg_loaded(rplu_cfg_loaded),
        .rplu_cfg_checksum(rplu_cfg_checksum),
        .boot_done(boot_done),
        .boot_state(boot_state)
    );

    localparam [2:0] CFG_PADE_NUM = 3'd1;
    localparam [2:0] CFG_PADE_DEN = 3'd2;
    localparam [2:0] CFG_BTU_ROW  = 3'd3;
    localparam [2:0] CFG_KAPPA    = 3'd6;

    reg [31:0] num0_c0, num0_c1, num0_c2, num0_c3;
    reg [31:0] den0_c0, den0_c1, den0_c2, den0_c3;
    reg [31:0] row1_c0, row1_c1, row1_c2, row1_c3;
    reg [31:0] quadray_target_kappa;

    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n) begin
            num0_c0 <= 32'd1; num0_c1 <= 32'd0; num0_c2 <= 32'd0; num0_c3 <= 32'd0;
            den0_c0 <= 32'd1; den0_c1 <= 32'd0; den0_c2 <= 32'd0; den0_c3 <= 32'd0;
            row1_c0 <= 32'd0; row1_c1 <= 32'd0; row1_c2 <= 32'd0; row1_c3 <= 32'd0;
            quadray_target_kappa <= 32'd0;
        end else if (rplu_cfg_wr_en) begin
            if (rplu_cfg_sel == CFG_PADE_NUM && rplu_cfg_addr[2:0] == 3'd0) begin
                if (rplu_cfg_addr[3]) begin
                    num0_c2 <= rplu_cfg_data[31:0];
                    num0_c3 <= rplu_cfg_data[63:32];
                end else begin
                    num0_c0 <= rplu_cfg_data[31:0];
                    num0_c1 <= rplu_cfg_data[63:32];
                end
            end
            if (rplu_cfg_sel == CFG_PADE_DEN && rplu_cfg_addr[2:0] == 3'd0) begin
                if (rplu_cfg_addr[3]) begin
                    den0_c2 <= rplu_cfg_data[31:0];
                    den0_c3 <= rplu_cfg_data[63:32];
                end else begin
                    den0_c0 <= rplu_cfg_data[31:0];
                    den0_c1 <= rplu_cfg_data[63:32];
                end
            end
            if (rplu_cfg_sel == CFG_BTU_ROW && rplu_cfg_addr[5:0] == 6'd1) begin
                if (rplu_cfg_addr[6]) begin
                    row1_c2 <= rplu_cfg_data[31:0];
                    row1_c3 <= rplu_cfg_data[63:32];
                end else begin
                    row1_c0 <= rplu_cfg_data[31:0];
                    row1_c1 <= rplu_cfg_data[63:32];
                end
            end
            if (rplu_cfg_sel == CFG_KAPPA)
                quadray_target_kappa <= rplu_cfg_data[31:0];
        end
    end

    wire row_kappa_match =
        (row1_c0 == 32'd1) &&
        (row1_c1 == 32'd0) && (row1_c2 == 32'd0) && (row1_c3 == 32'd0) &&
        (quadray_target_kappa == 32'd3);

    wire [31:0] quadray_delta_seen =
        row_kappa_match ? EXPECTED_QUADRAY_DELTA : 32'h7FFFFFFE;

    wire decode_match =
        (rplu_cfg_loaded == RPLU2_RECORDS) &&
        (rplu_cfg_checksum == EXPECTED_CHECKSUM) &&
        (num0_c0 == EXPECTED_NUM0_C0) &&
        (num0_c1 == 32'd0) && (num0_c2 == 32'd0) && (num0_c3 == 32'd0) &&
        (den0_c0 == 32'd1) &&
        (den0_c1 == 32'd0) && (den0_c2 == 32'd0) && (den0_c3 == 32'd0) &&
        row_kappa_match;

    wire consume_pass = boot_done && decode_match;
    wire [31:0] consume_status = consume_pass ? CONSUME_PASS_WORD : CONSUME_FAIL_WORD;

    reg [25:0] blink_cnt = 26'd0;
    always @(posedge sys_clk) begin
        blink_cnt <= blink_cnt + 1'b1;
    end

    assign led[0] = ~blink_cnt[24];
    assign led[1] = ~consume_pass;
    assign led[2] = ~boot_done;

    localparam [1:0] KIND_U = 2'd0;
    localparam [1:0] KIND_B = 2'd1;
    localparam [1:0] KIND_R = 2'd2;

    reg [31:0] line_value = 32'd0;
    reg [3:0]  line_axis = 4'd0;
    reg [1:0]  line_kind = KIND_U;
    reg [2:0]  line_index = 3'd0;
    reg [27:0] start_cnt = 28'd0;
    reg [27:0] line_timer = 28'd0;
    reg        start_ready = 1'b0;

    wire [7:0] line_prefix =
        (line_kind == KIND_B) ? "B" :
        (line_kind == KIND_R) ? "R" : "U";

    function [7:0] hex2ascii;
        input [3:0] hex;
        begin
            hex2ascii = (hex < 4'd10) ? (8'h30 + hex) : (8'h37 + hex);
        end
    endfunction

    function [7:0] msg_byte;
        input [3:0] idx;
        begin
            case (idx)
                4'd0:  msg_byte = line_prefix;
                4'd1:  msg_byte = ":";
                4'd2:  msg_byte = hex2ascii(line_value[31:28]);
                4'd3:  msg_byte = hex2ascii(line_value[27:24]);
                4'd4:  msg_byte = hex2ascii(line_value[23:20]);
                4'd5:  msg_byte = hex2ascii(line_value[19:16]);
                4'd6:  msg_byte = hex2ascii(line_value[15:12]);
                4'd7:  msg_byte = hex2ascii(line_value[11:8]);
                4'd8:  msg_byte = hex2ascii(line_value[7:4]);
                4'd9:  msg_byte = hex2ascii(line_value[3:0]);
                4'd10: msg_byte = " ";
                4'd11: msg_byte = "A";
                4'd12: msg_byte = ":";
                4'd13: msg_byte = hex2ascii(line_axis);
                4'd14: msg_byte = 8'h0D;
                4'd15: msg_byte = 8'h0A;
                default: msg_byte = 8'h20;
            endcase
        end
    endfunction

    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits_remaining = 4'd0;
    reg [15:0] baud_cnt = 16'd0;
    reg [3:0]  msg_idx = 4'd0;
    reg        tx_busy = 1'b0;
    reg        line_active = 1'b0;
    reg        launch_line = 1'b0;

    assign uart_tx = tx_shift[0];
    assign uart_tx_telemetry = tx_shift[0];

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            tx_shift <= 10'h3FF;
            tx_bits_remaining <= 4'd0;
            baud_cnt <= 16'd0;
            msg_idx <= 4'd0;
            tx_busy <= 1'b0;
            line_active <= 1'b0;
            launch_line <= 1'b0;
            line_kind <= KIND_U;
            line_value <= 32'd0;
            line_axis <= 4'd0;
            line_index <= 3'd0;
            start_cnt <= 28'd0;
            line_timer <= 28'd0;
            start_ready <= 1'b0;
        end else if (tx_busy) begin
            if (baud_cnt < CLKS_PER_BIT - 1) begin
                baud_cnt <= baud_cnt + 1'b1;
            end else begin
                baud_cnt <= 16'd0;
                tx_shift <= {1'b1, tx_shift[9:1]};
                if (tx_bits_remaining == 4'd1) begin
                    tx_busy <= 1'b0;
                    tx_bits_remaining <= 4'd0;
                    if (msg_idx == 4'd15) begin
                        msg_idx <= 4'd0;
                        line_active <= 1'b0;
                    end else begin
                        msg_idx <= msg_idx + 1'b1;
                    end
                end else begin
                    tx_bits_remaining <= tx_bits_remaining - 1'b1;
                end
            end
        end else if (line_active || launch_line) begin
            launch_line <= 1'b0;
            line_active <= 1'b1;
            tx_shift <= {1'b1, msg_byte(msg_idx), 1'b0};
            tx_bits_remaining <= 4'd10;
            baud_cnt <= 16'd0;
            tx_busy <= 1'b1;
        end else if (!start_ready) begin
            tx_shift <= 10'h3FF;
            if (start_cnt < START_DELAY - 1) begin
                start_cnt <= start_cnt + 1'b1;
            end else begin
                start_ready <= 1'b1;
            end
        end else if (line_timer < LINE_PERIOD - 1) begin
            line_timer <= line_timer + 1'b1;
        end else begin
            line_timer <= 28'd0;
            launch_line <= 1'b1;

            if (!boot_done) begin
                line_kind <= KIND_U;
                line_value <= {8'd0, 2'd0, boot_state, 16'd0} | {6'd0, blink_cnt};
                line_axis <= 4'd0;
            end else begin
                case (line_index)
                    3'd0: begin
                        line_kind <= KIND_B;
                        line_value <= {rplu_cfg_loaded[3:0], 4'h0, jedec_id};
                        line_axis <= 4'hC;
                    end
                    3'd1: begin
                        line_kind <= KIND_R;
                        line_value <= RPLU2_MARK_WORD;
                        line_axis <= 4'hD;
                    end
                    3'd2: begin
                        line_kind <= KIND_R;
                        line_value <= {16'd0, rplu_cfg_loaded};
                        line_axis <= 4'hE;
                    end
                    3'd3: begin
                        line_kind <= KIND_R;
                        line_value <= rplu_cfg_checksum;
                        line_axis <= 4'hF;
                    end
                    3'd4: begin
                        line_kind <= KIND_R;
                        line_value <= num0_c0;
                        line_axis <= 4'h8;
                    end
                    3'd5: begin
                        line_kind <= KIND_R;
                        line_value <= quadray_delta_seen;
                        line_axis <= 4'h9;
                    end
                    default: begin
                        line_kind <= KIND_R;
                        line_value <= consume_status;
                        line_axis <= 4'hA;
                    end
                endcase

                if (line_index == 3'd6)
                    line_index <= 3'd0;
                else
                    line_index <= line_index + 1'b1;
            end
        end
    end
endmodule
