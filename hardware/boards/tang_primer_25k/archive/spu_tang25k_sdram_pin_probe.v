// Minimal Tang Primer 25K SDRAM header pin probe.
//
// Keeps SDRAM commands inactive and walks every DQ pin through high-Z, low,
// and high phases. UART reports M:D2<phase><index><sample> A:<index>.

module spu_tang25k_sdram_pin_probe (
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
    localparam integer CLKS_PER_BIT = 434;       // 50 MHz / 115200
    localparam integer PHASE_TICKS  = 12_500_000; // 250 ms

    reg [25:0] phase_cnt = 26'd0;
    reg [1:0]  phase = 2'd0;
    reg [1:0]  report_phase = 2'd0;
    reg [3:0]  probe_idx = 4'd0;
    reg [3:0]  report_idx = 4'd0;
    reg        emit_line = 1'b0;

    reg [15:0] dq_sample = 16'd0;
    reg [15:0] dq_latch = 16'd0;

    wire drive_low  = (phase == 2'd1);
    wire drive_high = (phase == 2'd2);
    wire drive_active = drive_low || drive_high;

    genvar dq_i;
    generate
        for (dq_i = 0; dq_i < 16; dq_i = dq_i + 1) begin : gen_dq_walk
            assign sdram_dq[dq_i] = (drive_active && (probe_idx == dq_i[3:0]))
                                  ? drive_high
                                  : 1'bz;
        end
    endgenerate

    // Keep the SDRAM device deselected so it should not drive DQ.
    assign sdram_clk   = 1'b0;
    assign sdram_cs_n  = 1'b1;
    assign sdram_ras_n = 1'b1;
    assign sdram_cas_n = 1'b1;
    assign sdram_we_n  = 1'b1;
    assign sdram_ba    = 2'b00;
    assign sdram_a0    = 1'b0;
    assign sdram_a1    = 1'b0;
    assign sdram_a2    = 1'b0;
    assign sdram_a3    = 1'b0;
    assign sdram_a4    = 1'b0;
    assign sdram_a5    = 1'b0;
    assign sdram_a6    = 1'b0;
    assign sdram_a7    = 1'b0;
    assign sdram_a8    = 1'b0;
    assign sdram_a9    = 1'b0;
    assign sdram_a10   = 1'b0;
    assign sdram_a11   = 1'b0;
    assign sdram_a12   = 1'b0;
    assign sdram_dm    = 2'b11;

    // LEDs are active-low on the Tang Primer 25K.
    assign led = {~drive_high, ~drive_low, ~probe_idx[0]};

    always @(posedge sys_clk) begin
        dq_sample <= sdram_dq;
        emit_line <= 1'b0;
        if (phase_cnt == PHASE_TICKS - 1) begin
            phase_cnt <= 26'd0;
            dq_latch <= dq_sample;
            report_phase <= phase;
            report_idx <= probe_idx;
            if (phase == 2'd2) begin
                phase <= 2'd0;
                probe_idx <= probe_idx + 1'b1;
            end else begin
                phase <= phase + 1'b1;
            end
            emit_line <= 1'b1;
        end else begin
            phase_cnt <= phase_cnt + 1'b1;
        end
    end

    wire [31:0] report_word = {8'hD2, 2'd0, report_phase, report_idx, dq_latch};

    function [7:0] hex_digit;
        input [3:0] value;
        begin
            hex_digit = (value < 4'd10) ? (8'h30 + value) : (8'h41 + value - 4'd10);
        end
    endfunction

    reg [3:0] msg_idx = 4'd0;
    reg [7:0] tx_byte = 8'h00;
    reg [9:0] tx_shift = 10'h3ff;
    reg [15:0] baud_cnt = 16'd0;
    reg [3:0] bit_cnt = 4'd0;
    reg tx_busy = 1'b0;
    reg line_pending = 1'b0;

    assign uart_tx = tx_shift[0];
    assign uart_tx_telemetry = tx_shift[0];

    always @* begin
        case (msg_idx)
            4'd0:  tx_byte = "M";
            4'd1:  tx_byte = ":";
            4'd2:  tx_byte = hex_digit(report_word[31:28]);
            4'd3:  tx_byte = hex_digit(report_word[27:24]);
            4'd4:  tx_byte = hex_digit(report_word[23:20]);
            4'd5:  tx_byte = hex_digit(report_word[19:16]);
            4'd6:  tx_byte = hex_digit(report_word[15:12]);
            4'd7:  tx_byte = hex_digit(report_word[11:8]);
            4'd8:  tx_byte = hex_digit(report_word[7:4]);
            4'd9:  tx_byte = hex_digit(report_word[3:0]);
            4'd10: tx_byte = " ";
            4'd11: tx_byte = "A";
            4'd12: tx_byte = ":";
            4'd13: tx_byte = hex_digit(report_idx);
            4'd14: tx_byte = 8'h0d;
            4'd15: tx_byte = 8'h0a;
            default: tx_byte = 8'h20;
        endcase
    end

    always @(posedge sys_clk) begin
        if (emit_line) begin
            line_pending <= 1'b1;
        end

        if (tx_busy) begin
            if (baud_cnt < CLKS_PER_BIT - 1) begin
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
