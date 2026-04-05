// spu_i2c_bridge.v — I2C Master Bridge  v1.0
//
// Generic bit-bang I2C master targeting Tang Primer 25K (GW5A-LV25MG121NES).
// No hard-IP primitives (replaces archive spu_i2c_bridge.v which used SB_I2C).
//
// Supports: standard 100 kHz and fast 400 kHz modes.
// Protocol: 7-bit address, 1-byte register, 1-byte data (read or write).
//
// SovereignBus integration:
//   Write to bus_addr 0x90 with bus_wdata = {slave_addr[6:0], rw, reg_addr[7:0], data[7:0], 8'h00}
//   rw = 0 → write,  rw = 1 → read
//   After transaction, bus_rdata holds read byte (valid when bus_ready high).

`default_nettype none

module spu_i2c_bridge #(
    parameter CLK_FREQ   = 27_000_000,
    parameter I2C_FREQ   = 400_000       // 400 kHz fast mode
)(
    input  wire        clk,
    input  wire        reset,

    // SovereignBus slave (address 0x90)
    input  wire [7:0]  bus_addr,
    input  wire [31:0] bus_wdata,
    input  wire        bus_wen,
    output reg  [31:0] bus_rdata,
    output reg         bus_ready,

    // Open-drain I2C pins (pull up externally)
    output reg         scl_oe,   // 1 = drive low,  0 = release (pulled high)
    output reg         sda_oe,
    input  wire        sda_in
);

    localparam HALF_PERIOD = CLK_FREQ / (2 * I2C_FREQ);   // clocks per half-bit

    // Transaction fields decoded from bus_wdata
    // [31:25] = slave_addr[6:0]
    // [24]    = rw (0=write, 1=read)
    // [23:16] = reg_addr
    // [15:8]  = write_data
    // [7:0]   = reserved

    localparam S_IDLE       = 4'd0;
    localparam S_START      = 4'd1;
    localparam S_ADDR       = 4'd2;
    localparam S_ACK1       = 4'd3;
    localparam S_REG        = 4'd4;
    localparam S_ACK2       = 4'd5;
    localparam S_DATA       = 4'd6;
    localparam S_ACK3       = 4'd7;
    localparam S_STOP       = 4'd8;
    localparam S_DONE       = 4'd9;
    localparam S_RSTART     = 4'd10;   // repeated start for read
    localparam S_RADDR      = 4'd11;
    localparam S_RACK       = 4'd12;
    localparam S_RDATA      = 4'd13;
    localparam S_RNACK      = 4'd14;

    reg [3:0]  state;
    reg [15:0] timer;
    reg [3:0]  bit_idx;
    reg [7:0]  shift_reg;
    reg        rw_flag;
    reg [7:0]  rx_byte;

    reg [6:0]  r_slave_addr;
    reg [7:0]  r_reg_addr;
    reg [7:0]  r_wdata;

    // Half-bit clock tick
    wire tick = (timer == HALF_PERIOD - 1);

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state     <= S_IDLE;
            timer     <= 0;
            scl_oe    <= 1'b0;
            sda_oe    <= 1'b0;
            bus_ready <= 1'b0;
            bus_rdata <= 32'h0;
        end else begin
            bus_ready <= 1'b0;
            timer     <= timer + 1'b1;

            case (state)
                S_IDLE: begin
                    scl_oe <= 1'b0;
                    sda_oe <= 1'b0;
                    if (bus_wen && bus_addr == 8'h90) begin
                        r_slave_addr <= bus_wdata[31:25];
                        rw_flag      <= bus_wdata[24];
                        r_reg_addr   <= bus_wdata[23:16];
                        r_wdata      <= bus_wdata[15:8];
                        timer        <= 0;
                        state        <= S_START;
                    end
                end

                // START: SDA low while SCL high
                S_START: begin
                    scl_oe <= 1'b0;            // SCL high
                    if (tick) begin
                        sda_oe <= 1'b1;        // SDA low → START
                        timer  <= 0;
                        state  <= S_ADDR;
                        shift_reg <= {r_slave_addr, 1'b0};  // write direction
                        bit_idx   <= 4'd7;
                    end
                end

                // Clock out 8-bit address+RW byte
                S_ADDR: begin
                    if (tick) begin
                        timer  <= 0;
                        if (scl_oe) begin       // falling edge — advance bit
                            scl_oe <= 1'b0;
                            if (bit_idx == 4'd0) begin
                                state  <= S_ACK1;
                                sda_oe <= 1'b0; // release SDA for ACK
                            end else begin
                                bit_idx   <= bit_idx - 1'b1;
                                shift_reg <= {shift_reg[6:0], 1'b0};
                                sda_oe    <= ~shift_reg[7];
                            end
                        end else begin          // rising edge
                            scl_oe <= 1'b1;
                            sda_oe <= ~shift_reg[7];
                        end
                    end
                end

                S_ACK1: begin   // clock one ACK bit (device pulls SDA low)
                    if (tick) begin
                        timer <= 0;
                        if (!scl_oe) begin      // rising edge
                            scl_oe    <= 1'b1;
                        end else begin          // falling edge
                            scl_oe    <= 1'b0;
                            shift_reg <= r_reg_addr;
                            bit_idx   <= 4'd7;
                            sda_oe    <= ~r_reg_addr[7];
                            state     <= S_REG;
                        end
                    end
                end

                S_REG: begin
                    if (tick) begin
                        timer <= 0;
                        if (scl_oe) begin
                            scl_oe <= 1'b0;
                            if (bit_idx == 4'd0) begin
                                state  <= S_ACK2;
                                sda_oe <= 1'b0;
                            end else begin
                                bit_idx   <= bit_idx - 1'b1;
                                shift_reg <= {shift_reg[6:0], 1'b0};
                                sda_oe    <= ~shift_reg[7];
                            end
                        end else begin
                            scl_oe <= 1'b1;
                            sda_oe <= ~shift_reg[7];
                        end
                    end
                end

                S_ACK2: begin
                    if (tick) begin
                        timer <= 0;
                        if (!scl_oe) begin
                            scl_oe <= 1'b1;
                        end else begin
                            scl_oe <= 1'b0;
                            if (rw_flag) begin
                                // READ: issue repeated start then address+1
                                sda_oe <= 1'b0;   // SDA high before RSTART
                                state  <= S_RSTART;
                            end else begin
                                shift_reg <= r_wdata;
                                bit_idx   <= 4'd7;
                                sda_oe    <= ~r_wdata[7];
                                state     <= S_DATA;
                            end
                        end
                    end
                end

                S_DATA: begin
                    if (tick) begin
                        timer <= 0;
                        if (scl_oe) begin
                            scl_oe <= 1'b0;
                            if (bit_idx == 4'd0) begin
                                state  <= S_ACK3;
                                sda_oe <= 1'b0;
                            end else begin
                                bit_idx   <= bit_idx - 1'b1;
                                shift_reg <= {shift_reg[6:0], 1'b0};
                                sda_oe    <= ~shift_reg[7];
                            end
                        end else begin
                            scl_oe <= 1'b1;
                            sda_oe <= ~shift_reg[7];
                        end
                    end
                end

                S_ACK3: begin
                    if (tick) begin
                        timer <= 0;
                        if (!scl_oe) begin
                            scl_oe <= 1'b1;
                        end else begin
                            scl_oe <= 1'b0;
                            sda_oe <= 1'b1;   // SDA low before STOP
                            state  <= S_STOP;
                        end
                    end
                end

                S_RSTART: begin   // Repeated START for read
                    if (tick) begin
                        timer  <= 0;
                        scl_oe <= 1'b0;
                        sda_oe <= 1'b0;       // SDA low = repeated START
                        shift_reg <= {r_slave_addr, 1'b1};  // read direction
                        bit_idx   <= 4'd7;
                        state     <= S_RADDR;
                    end
                end

                S_RADDR: begin
                    if (tick) begin
                        timer <= 0;
                        if (scl_oe) begin
                            scl_oe <= 1'b0;
                            if (bit_idx == 4'd0) begin
                                state  <= S_RACK;
                                sda_oe <= 1'b0;
                            end else begin
                                bit_idx   <= bit_idx - 1'b1;
                                shift_reg <= {shift_reg[6:0], 1'b0};
                                sda_oe    <= ~shift_reg[7];
                            end
                        end else begin
                            scl_oe <= 1'b1;
                            sda_oe <= ~shift_reg[7];
                        end
                    end
                end

                S_RACK: begin
                    if (tick) begin
                        timer <= 0;
                        if (!scl_oe) begin
                            scl_oe <= 1'b1;
                        end else begin
                            scl_oe <= 1'b0;
                            sda_oe <= 1'b0;   // release SDA for device to drive
                            bit_idx <= 4'd7;
                            rx_byte <= 8'h0;
                            state  <= S_RDATA;
                        end
                    end
                end

                S_RDATA: begin
                    if (tick) begin
                        timer <= 0;
                        if (!scl_oe) begin   // rising edge — sample
                            scl_oe <= 1'b1;
                            rx_byte <= {rx_byte[6:0], sda_in};
                        end else begin       // falling edge — advance
                            scl_oe <= 1'b0;
                            if (bit_idx == 4'd0) begin
                                state  <= S_RNACK;
                                sda_oe <= 1'b1;  // NACK (master ends read)
                            end else
                                bit_idx <= bit_idx - 1'b1;
                        end
                    end
                end

                S_RNACK: begin
                    if (tick) begin
                        timer <= 0;
                        if (!scl_oe) begin
                            scl_oe <= 1'b1;
                        end else begin
                            scl_oe <= 1'b0;
                            sda_oe <= 1'b1;
                            state  <= S_STOP;
                        end
                    end
                end

                S_STOP: begin
                    if (tick) begin
                        timer  <= 0;
                        scl_oe <= 1'b0;   // SCL high
                        if (!scl_oe) begin
                            sda_oe <= 1'b0;   // SDA high = STOP
                            state  <= S_DONE;
                        end
                    end
                end

                S_DONE: begin
                    bus_rdata <= {24'h0, rx_byte};
                    bus_ready <= 1'b1;
                    state     <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
`default_nettype wire
