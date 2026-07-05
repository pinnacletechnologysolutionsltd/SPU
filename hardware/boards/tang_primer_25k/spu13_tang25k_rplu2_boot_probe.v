// spu13_tang25k_rplu2_boot_probe.v -- J4 flash/RPLU2 boot hydration probe.
//
// This is intentionally smaller than the full SPU-13/RPLU2 core.  It uses the
// production laminar bootloader against the PMOD J4 flash and emits the same
// B:/R: telemetry shape consumed by tools/probe_tang25k_rplu_flash.py.
module spu13_tang25k_rplu2_boot_probe (
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

    reg [7:0] rst_cnt = 8'd0;
    wire rst_n = (rst_cnt == 8'hFF);

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            rst_cnt <= rst_cnt + 1'b1;
        end
    end

    wire [23:0] jedec_id;
    wire [23:0] prime_data;
    wire [3:0]  prime_addr;
    wire        prime_we;
    wire [31:0] pell_data;
    wire [2:0]  pell_addr;
    wire        pell_we;
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
        .rplu_cfg_wr_en(),
        .rplu_cfg_sel(),
        .rplu_cfg_material(),
        .rplu_cfg_addr(),
        .rplu_cfg_data(),
        .rplu_cfg_loaded(rplu_cfg_loaded),
        .rplu_cfg_checksum(rplu_cfg_checksum),
        .boot_done(boot_done),
        .boot_state(boot_state)
    );

    reg [25:0] blink_cnt = 26'd0;
    always @(posedge sys_clk) begin
        blink_cnt <= blink_cnt + 1'b1;
    end

    assign led[0] = ~blink_cnt[24];
    assign led[1] = ~flash_sck;
    assign led[2] = ~boot_done;

    localparam [1:0] KIND_U = 2'd0;
    localparam [1:0] KIND_B = 2'd1;
    localparam [1:0] KIND_R = 2'd2;

    reg [31:0] line_value = 32'd0;
    reg [3:0]  line_axis = 4'd0;
    reg [1:0]  line_kind = KIND_U;
    reg [1:0]  rplu_line = 2'd0;
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
            rplu_line <= 2'd0;
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
            end else if (rplu_line == 2'd0) begin
                line_kind <= KIND_B;
                line_value <= {rplu_cfg_loaded[3:0], 4'h0, jedec_id};
                line_axis <= 4'hC;
                rplu_line <= 2'd1;
            end else if (rplu_line == 2'd1) begin
                line_kind <= KIND_R;
                line_value <= RPLU2_MARK_WORD;
                line_axis <= 4'hD;
                rplu_line <= 2'd2;
            end else if (rplu_line == 2'd2) begin
                line_kind <= KIND_R;
                line_value <= {16'd0, rplu_cfg_loaded};
                line_axis <= 4'hE;
                rplu_line <= 2'd3;
            end else begin
                line_kind <= KIND_R;
                line_value <= rplu_cfg_checksum;
                line_axis <= 4'hF;
                rplu_line <= 2'd0;
            end
        end
    end
endmodule
