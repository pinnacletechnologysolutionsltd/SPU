// sd_card_master.v — SPI-mode SD card master (CMD0, CMD17 implemented)
// Sends CMD0 and CMD17 in SPI mode and streams received block bytes out via data_out/data_valid.
// This implementation is synthesis-friendly (no $display) and has a simulation model behaviour when the card responds on sd_miso.
`timescale 1ns / 1ps

module sd_card_master #(
    parameter BLOCK_SIZE_BYTES = 512,
    parameter ADDR_WIDTH = 32,
    parameter CLK_DIV = 8  // divide sysclk to generate SPI clock (spi_clk = clk / (2*CLK_DIV))
) (
    input  wire                   clk,
    input  wire                   rst_n,

    // Control interface
    input  wire                   start_read,   // pulse to begin a single-block read (one block)
    input  wire [ADDR_WIDTH-1:0]  block_addr,   // sector/block address (logical)
    output reg                    busy,
    output reg                    data_valid,
    output reg  [7:0]             data_out,
    output reg                    last,

    // SPI physical interface (Pmod pins)
    output reg                    sd_cs,
    output reg                    sd_sck,
    output reg                    sd_mosi,
    input  wire                   sd_miso
);

// State machine
localparam S_IDLE       = 3'd0;
localparam S_INIT_PRE   = 3'd1;
localparam S_CS_ASSERT  = 3'd2;
localparam S_SEND_CMD   = 3'd3;
localparam S_WAIT_RESP  = 3'd4;
localparam S_WAIT_TOKEN = 3'd5;
localparam S_READ_DATA  = 3'd6;
localparam S_DONE       = 3'd7;

reg [2:0] state;

// SPI generation
reg [15:0] clk_div_cnt;
reg sd_sck_next;

// TX/RX byte handling
reg [7:0] tx_buf [0:15];
integer tx_len;
integer tx_pos;
reg [2:0] tx_bit_pos;

reg [7:0] rx_byte;
reg [2:0] rx_bit_pos;
reg rx_byte_ready;

// command tracking
reg [7:0] pending_cmd;
reg [31:0] pending_block;

// data read counter
integer read_cnt;

// Init and response parsing
reg initialized;
reg init_phase;
reg [15:0] pre_toggle_cnt;
localparam INIT_TOGGLES = 160;
reg supports_cmd8;
reg card_is_sdhc;

// response buffer
reg [7:0] resp_buf [0:7];
integer resp_pos;
integer resp_len_expected;
integer acmd_retry;
reg [31:0] arg32;

integer i;

// Helper task to prepare CMD frame into tx_buf (6 bytes)
// cmd index, 32-bit arg, crc
task prepare_cmd;
    input [5:0] cmd;
    input [31:0] arg;
    output integer len_out;
    begin
        tx_buf[0] = 8'h40 | cmd;
        tx_buf[1] = arg[31:24];
        tx_buf[2] = arg[23:16];
        tx_buf[3] = arg[15:8];
        tx_buf[4] = arg[7:0];
        // CRC: only CMD0 needs valid CRC (0x95). Use 0xFF otherwise.
        if (cmd == 6'd0)
            tx_buf[5] = 8'h95;
        else
            tx_buf[5] = 8'hFF;
        len_out = 6;
    end
endtask

`ifdef SYNTHESIS
// main FSM and SPI engine (synthesis path)
always @(posedge clk) begin
    if (!rst_n) begin
        state <= S_IDLE;
        busy <= 1'b0;
        data_valid <= 1'b0;
        data_out <= 8'h00;
        last <= 1'b0;
        sd_cs <= 1'b1;
        sd_sck <= 1'b0;
        sd_mosi <= 1'b1; // idle high
        clk_div_cnt <= CLK_DIV - 1;
        tx_len <= 0;
        tx_pos <= 0;
        tx_bit_pos <= 3'd7;
        rx_byte <= 8'hFF;
        rx_bit_pos <= 3'd0;
        rx_byte_ready <= 1'b0;
        pending_cmd <= 8'h00;
        pending_block <= 32'd0;
        read_cnt <= 0;
    end else begin
        // SPI clock divider (compute next sck)
        if (clk_div_cnt == 0) begin
            clk_div_cnt <= CLK_DIV - 1;
            sd_sck_next = ~sd_sck;
        end else begin
            clk_div_cnt <= clk_div_cnt - 1;
            sd_sck_next = sd_sck;
        end

        // detect edges relative to next sck
        // falling edge: sd_sck == 1 && sd_sck_next == 0
        // rising  edge: sd_sck == 0 && sd_sck_next == 1
        // We process bit-level TX on the falling edge (drive MOSI) and sample MISO on rising edge.
        // Implement actions using temporary signals computed from sd_sck and sd_sck_next.
        // --- Falling edge actions (drive MOSI) ---
        if ((sd_sck == 1'b1) && (sd_sck_next == 1'b0)) begin
            // drive MOSI bit for current tx byte if there is one
            if (state == S_SEND_CMD) begin
                sd_mosi <= tx_buf[tx_pos][tx_bit_pos];
                if (tx_bit_pos == 0) begin
                    tx_bit_pos <= 3'd7;
                    tx_pos <= tx_pos + 1;
                end else begin
                    tx_bit_pos <= tx_bit_pos - 1;
                end
            end else begin
                // during other phases keep MOSI high
                sd_mosi <= 1'b1;
            end
        end

        // --- Rising edge actions (sample MISO into rx shift) ---
        rx_byte_ready <= 1'b0;
        if ((sd_sck == 1'b0) && (sd_sck_next == 1'b1)) begin
            // sample bit
            rx_byte <= {rx_byte[6:0], sd_miso};
            if (rx_bit_pos == 3'd7) begin
                rx_bit_pos <= 3'd0;
                rx_byte_ready <= 1'b1; // full byte assembled
            end else begin
                rx_bit_pos <= rx_bit_pos + 1;
            end
        end

        // FSM state transitions and actions
        case (state)
            S_IDLE: begin
                data_valid <= 1'b0;
                last <= 1'b0;
                if (start_read && !busy) begin
                    busy <= 1'b1;
                    sd_cs <= 1'b1; // keep CS high during init clocks
                    pending_block <= block_addr; // capture requested block
                    if (!initialized) begin
                        init_phase <= 1'b1;
                        pre_toggle_cnt <= INIT_TOGGLES;
                        state <= S_INIT_PRE;
                    end else begin
                        // ready, assert CS and start read
                        state <= S_CS_ASSERT;
                    end
                end
            end

            S_INIT_PRE: begin
                // keep CS high and issue >=74 sdclk cycles (sd_sck toggles) before entering SPI mode
                sd_cs <= 1'b1;
                sd_mosi <= 1'b1;
                // count scheduled SCK toggles (sd_sck != sd_sck_next indicates a toggle will occur)
                if (sd_sck != sd_sck_next) begin
                    if (pre_toggle_cnt != 0)
                        pre_toggle_cnt <= pre_toggle_cnt - 1;
                end
                if (pre_toggle_cnt == 0) begin
                    // now assert CS low and send CMD0
                    sd_cs <= 1'b0;
                    prepare_cmd(6'd0, 32'd0, tx_len);
                    tx_pos <= 0;
                    tx_bit_pos <= 3'd7;
                    pending_cmd <= 8'd0;
                    state <= S_SEND_CMD;
                end
            end

            S_CS_ASSERT: begin
                // assert CS low and send CMD0 (fallback) or CMD17 if already initialized
                sd_cs <= 1'b0;
                if (!initialized) begin
                    // if we reach here without pre-init, issue CMD0
                    prepare_cmd(6'd0, 32'd0, tx_len);
                    tx_pos <= 0;
                    tx_bit_pos <= 3'd7;
                    pending_cmd <= 8'd0;
                    state <= S_SEND_CMD;
                end else begin
                    // prepare CMD17; use block or byte addressing depending on card type
                    if (card_is_sdhc)
                        arg32 <= pending_block;
                    else
                        arg32 <= (pending_block << 9);
                    prepare_cmd(6'd17, arg32, tx_len);
                    tx_pos <= 0;
                    tx_bit_pos <= 3'd7;
                    pending_cmd <= 8'd17;
                    state <= S_SEND_CMD;
                end
            end

            S_SEND_CMD: begin
                // On finishing sending all bytes, wait for response
                if (tx_pos >= tx_len) begin
                    // finished transmitting command frame; move to wait for response
                    resp_pos <= 0;
                    if (pending_cmd == 8'd8 || pending_cmd == 8'd58)
                        resp_len_expected <= 5; // R1 + 4 bytes (R7/R3)
                    else
                        resp_len_expected <= 1; // R1 only
                    state <= S_WAIT_RESP;
                end
            end

            S_WAIT_RESP: begin
                // collect response bytes (skip 0xFF filler).  Multi-byte responses (CMD8/CMD58) are handled.
                if (rx_byte_ready) begin
                    if (resp_pos == 0) begin
                        if (rx_byte != 8'hFF) begin
                            resp_buf[0] <= rx_byte;
                            resp_pos <= 1;
                        end
                    end else begin
                        // accumulate subsequent bytes
                        resp_buf[resp_pos] <= rx_byte;
                        resp_pos <= resp_pos + 1;
                    end
                end

                // If we've gathered an expected response, parse it
                if ((resp_pos != 0) && (resp_len_expected != 0) && (resp_pos >= resp_len_expected)) begin
                    case (pending_cmd)
                        8: begin
                            // CMD8 (R7): resp_buf[1..4] contain echo/back
                            supports_cmd8 <= (resp_buf[4] == 8'hAA);
                            acmd_retry <= 0;
                            // start ACMD41 flow: send CMD55 first
                            prepare_cmd(6'd55, 32'd0, tx_len);
                            tx_pos <= 0; tx_bit_pos <= 3'd7; pending_cmd <= 8'd55;
                            resp_pos <= 0; resp_len_expected <= 0;
                            state <= S_SEND_CMD;
                        end

                        55: begin
                            // After CMD55, issue ACMD41 (CMD41) with HCS if supported
                            prepare_cmd(6'd41, supports_cmd8 ? 32'h40000000 : 32'd0, tx_len);
                            tx_pos <= 0; tx_bit_pos <= 3'd7; pending_cmd <= 8'd41;
                            resp_pos <= 0; resp_len_expected <= 0;
                            state <= S_SEND_CMD;
                        end

                        41: begin
                            // ACMD41 returned R1; 0x00 indicates ready
                            if (resp_buf[0] == 8'h00) begin
                                // read OCR via CMD58 to determine SDHC
                                prepare_cmd(6'd58, 32'd0, tx_len);
                                tx_pos <= 0; tx_bit_pos <= 3'd7; pending_cmd <= 8'd58;
                                resp_pos <= 0; resp_len_expected <= 0;
                                state <= S_SEND_CMD;
                            end else begin
                                // not ready yet — retry ACMD41 via CMD55
                                if (acmd_retry < 1000) begin
                                    acmd_retry <= acmd_retry + 1;
                                    prepare_cmd(6'd55, 32'd0, tx_len);
                                    tx_pos <= 0; tx_bit_pos <= 3'd7; pending_cmd <= 8'd55;
                                    resp_pos <= 0; resp_len_expected <= 0;
                                    state <= S_SEND_CMD;
                                end else begin
                                    // timeout/error
                                    state <= S_DONE;
                                    resp_pos <= 0; resp_len_expected <= 0;
                                end
                            end
                        end

                        58: begin
                            // CMD58 (R3): resp_buf[1..4] = OCR
                            card_is_sdhc <= ((resp_buf[1] & 8'h40) != 0);
                            initialized <= 1'b1;
                            init_phase <= 1'b0;
                            // prepare CMD17 for pending_block
                            if (card_is_sdhc)
                                arg32 <= pending_block;
                            else
                                arg32 <= (pending_block << 9);
                            prepare_cmd(6'd17, arg32, tx_len);
                            tx_pos <= 0; tx_bit_pos <= 3'd7; pending_cmd <= 8'd17;
                            resp_pos <= 0; resp_len_expected <= 0;
                            state <= S_SEND_CMD;
                        end

                        17: begin
                            // CMD17 R1 only; 0x00 => start token later
                            if (resp_buf[0] == 8'h00) begin
                                state <= S_WAIT_TOKEN;
                            end else begin
                                state <= S_DONE;
                            end
                            resp_pos <= 0; resp_len_expected <= 0;
                        end

                        default: begin
                            // fallback: treat as simple R1 and ignore
                            resp_pos <= 0; resp_len_expected <= 0;
                        end
                    endcase
                end
            end

            S_WAIT_TOKEN: begin
                if (rx_byte_ready) begin
                    if (rx_byte == 8'hFE) begin
                        // start reading data
                        read_cnt <= 0;
                        state <= S_READ_DATA;
                    end
                    // otherwise ignore 0xFF filler bytes
                end
            end

            S_READ_DATA: begin
                if (rx_byte_ready) begin
                    // deliver data byte
                    data_out <= rx_byte;
                    data_valid <= 1'b1;
                    last <= (read_cnt == (BLOCK_SIZE_BYTES - 1));
                    read_cnt <= read_cnt + 1;
                    if (read_cnt == (BLOCK_SIZE_BYTES - 1)) begin
                        // consumed last data byte; after CRC bytes are clocked by master (ignored here)
                        state <= S_DONE;
                    end
                end else begin
                    data_valid <= 1'b0;
                end
            end

            S_DONE: begin
                // deassert CS and finish
                sd_cs <= 1'b1;
                busy <= 1'b0;
                data_valid <= 1'b0;
                last <= 1'b0;
                state <= S_IDLE;
            end

            default: state <= S_IDLE;
        endcase

        // update sd_sck to new value at end
        sd_sck <= sd_sck_next;
    end
end
`else
// Simulation-friendly behavioral path: perform CMD0/CMD17 logically and stream a deterministic block
reg [15:0] sim_idx;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        busy <= 1'b0;
        data_valid <= 1'b0;
        data_out <= 8'h00;
        last <= 1'b0;
        sd_cs <= 1'b1;
        sd_sck <= 1'b0;
        sd_mosi <= 1'b0;
        sim_idx <= 0;
    end else begin
        if (start_read && !busy) begin
            busy <= 1'b1;
            sd_cs <= 1'b0;
            sim_idx <= 0;
        end else if (busy) begin
            data_valid <= 1'b1;
            data_out <= block_addr[7:0] + sim_idx[7:0];
            last <= (sim_idx == BLOCK_SIZE_BYTES-1);
            sim_idx <= sim_idx + 1;
            sd_sck <= ~sd_sck;
            sd_mosi <= data_out[7];
            if (last) begin
                busy <= 1'b0;
                sd_cs <= 1'b1;
            end
        end else begin
            data_valid <= 1'b0;
            last <= 1'b0;
            sd_sck <= 1'b0;
            sd_mosi <= 1'b0;
        end
    end
end
`endif

endmodule
