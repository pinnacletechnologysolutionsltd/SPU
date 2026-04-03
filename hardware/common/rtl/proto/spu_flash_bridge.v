// spu_flash_bridge.v (v3.0 — W25Q128JVSQ)
// Objective: Bit-serial SPI read for FPGA ↔ W25Q128JVSQ flash.
// Supports single-byte read and burst (consecutive bytes, CS held low).
// Protocol: CS↓ → CMD(03h,8b) → ADDR(24b) → DATA(8b×N) → CS↑
// SPI Mode 0 (CPOL=0, CPHA=0): MOSI driven on falling edge, sampled on rising.
//   Each bit = 2 system clocks: phase=0 (SCLK low, MOSI setup),
//                                phase=1 (SCLK high, MISO sample).
// SPI rate = clk/2 (e.g. 48 MHz → 24 MHz, within W25Q128 READ-03h 50 MHz limit).
// No floating point. No transcendentals. Bit-exact state machine.
// CC0 1.0 Universal.

module spu_flash_bridge (
    input  wire        clk,
    input  wire        rst_n,

    // Command interface (from spu_laminar_boot or Ghost OS)
    input  wire        rd_trig,      // Pulse high for one cycle to start read
    input  wire [23:0] rd_addr,      // Byte address into flash
    input  wire        burst,        // Hold high to stream consecutive bytes
    input  wire        rd_stop,      // Pulse to end burst after current byte
    output reg  [7:0]  rd_data,      // Data byte returned
    output reg         rd_done,      // Pulses one cycle per valid byte

    // W25Q128JVSQ physical SPI pins
    output reg         flash_sclk,
    output reg         flash_cs_n,
    output reg         flash_mosi,
    input  wire        flash_miso
);

    localparam IDLE    = 3'd0;
    localparam CMD_TX  = 3'd1;   // Transmit READ command (03h), 8 bits
    localparam ADDR_TX = 3'd2;   // Transmit 24-bit address MSB-first
    localparam DATA_RX = 3'd3;   // Receive 8-bit data byte (repeats in burst)
    localparam DONE    = 3'd4;

    localparam [7:0] CMD_READ = 8'h03;

    reg [2:0]  state;
    reg        phase;    // 0 = SCLK low / MOSI setup; 1 = SCLK high / MISO sample
    reg [4:0]  bit_cnt;
    reg [7:0]  cmd_reg;
    reg [23:0] addr_reg;
    reg [7:0]  rx_shift;
    reg        stop_latch; // latch rd_stop so it's safe as a pulse

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state      <= IDLE;
            phase      <= 1'b0;
            flash_cs_n <= 1'b1;
            flash_mosi <= 1'b0;
            flash_sclk <= 1'b0;
            rd_done    <= 1'b0;
            rd_data    <= 8'h00;
            bit_cnt    <= 5'd0;
            cmd_reg    <= 8'h00;
            addr_reg   <= 24'h0;
            rx_shift   <= 8'h00;
            stop_latch <= 1'b0;
        end else begin
            rd_done <= 1'b0;  // pulse semantics — deassert every cycle by default

            // Latch rd_stop so a single-cycle pulse isn't missed
            if (rd_stop) stop_latch <= 1'b1;

            case (state)
                // ── IDLE: wait for trigger ────────────────────────────────
                IDLE: begin
                    flash_cs_n <= 1'b1;
                    flash_sclk <= 1'b0;
                    flash_mosi <= 1'b0;
                    stop_latch <= 1'b0;
                    if (rd_trig) begin
                        flash_cs_n <= 1'b0;
                        cmd_reg    <= CMD_READ;
                        addr_reg   <= rd_addr;
                        bit_cnt    <= 5'd7;
                        phase      <= 1'b0;
                        state      <= CMD_TX;
                    end
                end

                // ── CMD_TX: clock out 8-bit READ command MSB-first ────────
                // phase=0: SCLK low, drive MOSI
                // phase=1: SCLK high, shift register
                CMD_TX: begin
                    if (!phase) begin
                        flash_sclk <= 1'b0;
                        flash_mosi <= cmd_reg[7];
                        phase      <= 1'b1;
                    end else begin
                        flash_sclk <= 1'b1;
                        cmd_reg    <= {cmd_reg[6:0], 1'b0};
                        phase      <= 1'b0;
                        if (bit_cnt == 5'd0) begin
                            bit_cnt <= 5'd23;
                            state   <= ADDR_TX;
                        end else
                            bit_cnt <= bit_cnt - 5'd1;
                    end
                end

                // ── ADDR_TX: clock out 24-bit address MSB-first ───────────
                ADDR_TX: begin
                    if (!phase) begin
                        flash_sclk <= 1'b0;
                        flash_mosi <= addr_reg[23];
                        phase      <= 1'b1;
                    end else begin
                        flash_sclk <= 1'b1;
                        addr_reg   <= {addr_reg[22:0], 1'b0};
                        phase      <= 1'b0;
                        if (bit_cnt == 5'd0) begin
                            bit_cnt  <= 5'd7;
                            rx_shift <= 8'h00;
                            state    <= DATA_RX;
                        end else
                            bit_cnt <= bit_cnt - 5'd1;
                    end
                end

                // ── DATA_RX: clock in 8-bit data byte MSB-first ──────────
                // In burst mode the flash auto-increments address; CS stays low.
                // phase=0: SCLK low (MOSI idle, setup gap between bytes)
                // phase=1: SCLK high, sample MISO into rx_shift
                DATA_RX: begin
                    if (!phase) begin
                        flash_sclk <= 1'b0;
                        flash_mosi <= 1'b0;
                        phase      <= 1'b1;
                    end else begin
                        flash_sclk <= 1'b1;
                        rx_shift   <= {rx_shift[6:0], flash_miso};
                        phase      <= 1'b0;
                        if (bit_cnt == 5'd0) begin
                            rd_data <= {rx_shift[6:0], flash_miso};
                            rd_done <= 1'b1;
                            if (burst && !stop_latch && !rd_stop) begin
                                // Burst: stay in DATA_RX, reset for next byte
                                bit_cnt  <= 5'd7;
                                rx_shift <= 8'h00;
                            end else begin
                                stop_latch <= 1'b0;
                                state      <= DONE;
                            end
                        end else
                            bit_cnt <= bit_cnt - 5'd1;
                    end
                end

                // ── DONE: deassert CS, return to IDLE ─────────────────────
                DONE: begin
                    flash_sclk <= 1'b0;
                    flash_cs_n <= 1'b1;
                    flash_mosi <= 1'b0;
                    state      <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule

