module spu13_tang25k_boot_probe (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx,
    output wire       uart_tx_telemetry,
    output wire       flash_cs,
    output wire       flash_sck,
    output wire       flash_mosi,
    input  wire       flash_miso
);
    localparam integer CLK_FREQ         = 50000000;
    localparam integer CLKS_PER_BIT     = 434;
    localparam integer START_DELAY      = CLK_FREQ / 2;
    localparam integer LINE_PERIOD      = CLK_FREQ / 5;

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
    wire        boot_done;

    spu_laminar_boot u_boot (
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
        .mem_burst_wr(),
        .mem_addr(),
        .mem_wr_manifold(),
        .mem_burst_done(1'b1),
        .boot_done(boot_done)
    );

    reg [31:0] seed_word0 = 32'd0;
    reg [31:0] seed_word1 = 32'd0;
    reg [31:0] seed_word2 = 32'd0;
    reg [31:0] seed_word3 = 32'd0;
    reg [31:0] seed_word4 = 32'd0;
    reg [31:0] seed_word5 = 32'd0;
    reg [31:0] seed_word6 = 32'd0;
    reg [31:0] seed_word7 = 32'd0;
    reg [31:0] seed_word8 = 32'd0;
    reg [31:0] seed_word9 = 32'd0;
    reg [31:0] seed_word10 = 32'd0;
    reg [31:0] seed_word11 = 32'd0;
    reg [31:0] seed_word12 = 32'd0;
    reg [3:0]  seed_count = 4'd0;
    reg [3:0]  last_seed_axis = 4'd0;

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            seed_count <= 4'd0;
            last_seed_axis <= 4'd0;
        end else if (!boot_done && prime_we && prime_addr < 4'd13) begin
            case (prime_addr)
                4'd0:  seed_word0 <= {8'd0, prime_data};
                4'd1:  seed_word1 <= {8'd0, prime_data};
                4'd2:  seed_word2 <= {8'd0, prime_data};
                4'd3:  seed_word3 <= {8'd0, prime_data};
                4'd4:  seed_word4 <= {8'd0, prime_data};
                4'd5:  seed_word5 <= {8'd0, prime_data};
                4'd6:  seed_word6 <= {8'd0, prime_data};
                4'd7:  seed_word7 <= {8'd0, prime_data};
                4'd8:  seed_word8 <= {8'd0, prime_data};
                4'd9:  seed_word9 <= {8'd0, prime_data};
                4'd10: seed_word10 <= {8'd0, prime_data};
                4'd11: seed_word11 <= {8'd0, prime_data};
                4'd12: seed_word12 <= {8'd0, prime_data};
                default: ;
            endcase
            seed_count <= prime_addr + 1'b1;
            last_seed_axis <= prime_addr;
        end
    end

    reg [25:0] blink_cnt = 26'd0;
    always @(posedge sys_clk) begin
        blink_cnt <= blink_cnt + 1'b1;
    end

    assign led[0] = ~blink_cnt[24];
    assign led[1] = ~flash_sck;
    assign led[2] = ~boot_done;

    reg [31:0] line_value = 32'd0;
    reg [3:0]  line_axis = 4'd0;
    reg [1:0]  line_kind = 2'd0;
    reg [3:0]  burst_axis = 4'd0;
    reg [27:0] start_cnt = 28'd0;
    reg [27:0] line_timer = 28'd0;
    reg        start_ready = 1'b0;
    reg        boot_line_sent = 1'b0;

    localparam [1:0] KIND_U = 2'd0;
    localparam [1:0] KIND_B = 2'd1;
    localparam [1:0] KIND_Q = 2'd2;

    wire [7:0] line_prefix =
        (line_kind == KIND_B) ? "B" :
        (line_kind == KIND_Q) ? "Q" : "U";

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

    function [31:0] seed_word;
        input [3:0] axis;
        begin
            case (axis)
                4'd0:  seed_word = seed_word0;
                4'd1:  seed_word = seed_word1;
                4'd2:  seed_word = seed_word2;
                4'd3:  seed_word = seed_word3;
                4'd4:  seed_word = seed_word4;
                4'd5:  seed_word = seed_word5;
                4'd6:  seed_word = seed_word6;
                4'd7:  seed_word = seed_word7;
                4'd8:  seed_word = seed_word8;
                4'd9:  seed_word = seed_word9;
                4'd10: seed_word = seed_word10;
                4'd11: seed_word = seed_word11;
                4'd12: seed_word = seed_word12;
                default: seed_word = 32'd0;
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
            burst_axis <= 4'd0;
            start_cnt <= 28'd0;
            line_timer <= 28'd0;
            start_ready <= 1'b0;
            boot_line_sent <= 1'b0;
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
                line_value <= {6'd0, blink_cnt};
                line_axis <= 4'd0;
            end else if (!boot_line_sent) begin
                line_kind <= KIND_B;
                line_value <= {seed_count, 4'h0, jedec_id};
                line_axis <= last_seed_axis;
                boot_line_sent <= 1'b1;
            end else begin
                line_kind <= KIND_Q;
                line_value <= seed_word(burst_axis);
                line_axis <= burst_axis;
                if (burst_axis == 4'd12) begin
                    burst_axis <= 4'd0;
                end else begin
                    burst_axis <= burst_axis + 1'b1;
                end
            end
        end
    end
endmodule
