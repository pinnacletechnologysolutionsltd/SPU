`timescale 1ns / 1ps

// spu_sd_inhaler.v — Streams 64-bit Chords from SD Card into the SPU Artery.
// Groups 8 consecutive bytes from a 512-byte SD sector into a single Chord.

module spu_sd_inhaler #(
    parameter ADDR_WIDTH = 32,
    parameter CLK_DIV    = 8
) (
    input  wire                   clk,
    input  wire                   rst_n,

    // Control interface
    input  wire                   start,        // pulse to start inhalation
    input  wire [ADDR_WIDTH-1:0]  start_sector, // start block address
    input  wire [15:0]            num_chords,   // how many 64-bit chords to read (e.g. 13 for boot)
    output reg                    busy,
    output reg                    done,
    output reg                    error,

    // Artery Inhale Interface
    output reg  [63:0]            chord_out,
    output reg                    chord_valid,

    // SD Master physical interface
    output wire                   sd_cs,
    output wire                   sd_sck,
    output wire                   sd_mosi,
    input  wire                   sd_miso
);

    // Internal state
    localparam S_IDLE      = 3'd0;
    localparam S_REQ_BLOCK = 3'd1;
    localparam S_WAIT_BUSY = 3'd2;
    localparam S_ASSEMBLING = 3'd3;
    localparam S_DONE      = 3'd4;
    localparam S_ERROR     = 3'd5;

    reg [2:0]  state;
    reg [15:0] chord_count;
    reg [2:0]  byte_within_chord;
    reg [63:0] shift_reg;
    reg [ADDR_WIDTH-1:0] current_sector;

    // SD Master signals
    reg  sd_start_pulse;
    wire sd_busy;
    wire sd_data_valid;
    wire [7:0] sd_data_out;
    wire sd_last_byte;

    sd_card_master #(.CLK_DIV(CLK_DIV)) u_sd_master (
        .clk        (clk),
        .rst_n      (rst_n),
        .start_read (sd_start_pulse),
        .block_addr (current_sector),
        .busy       (sd_busy),
        .data_valid (sd_data_valid),
        .data_out   (sd_data_out),
        .last       (sd_last_byte),
        .sd_cs      (sd_cs),
        .sd_sck     (sd_sck),
        .sd_mosi    (sd_mosi),
        .sd_miso    (sd_miso)
    );

    always @(posedge clk) begin
        if (!rst_n) begin
            state <= S_IDLE;
            busy <= 1'b0;
            done <= 1'b0;
            error <= 1'b0;
            chord_out <= 64'h0;
            chord_valid <= 1'b0;
            sd_start_pulse <= 1'b0;
            current_sector <= 32'h0;
            chord_count <= 16'h0;
            byte_within_chord <= 3'd0;
            shift_reg <= 64'h0;
        end else begin
            sd_start_pulse <= 1'b0;
            chord_valid <= 1'b0;

            case (state)
                S_IDLE: begin
                    done <= 1'b0;
                    error <= 1'b0;
                    if (start) begin
                        busy <= 1'b1;
                        current_sector <= start_sector;
                        chord_count <= 0;
                        byte_within_chord <= 0;
                        state <= S_REQ_BLOCK;
                    end
                end

                S_REQ_BLOCK: begin
                    sd_start_pulse <= 1'b1;
                    state <= S_WAIT_BUSY;
                end

                S_WAIT_BUSY: begin
                    if (sd_busy) state <= S_ASSEMBLING;
                end

                S_ASSEMBLING: begin
                    if (sd_data_valid) begin
                        // Assemble 64-bit chord (Big Endian: first byte is MSB bits 63:56)
                        shift_reg <= {shift_reg[55:0], sd_data_out};
                        
                        if (byte_within_chord == 3'd7) begin
                            chord_out <= {shift_reg[55:0], sd_data_out};
                            chord_valid <= 1'b1;
                            chord_count <= chord_count + 1;
                            byte_within_chord <= 0;

                            if (chord_count + 1 >= num_chords) begin
                                state <= S_DONE;
                            end
                        end else begin
                            byte_within_chord <= byte_within_chord + 1;
                        end
                    end

                    if (!sd_busy && (state == S_ASSEMBLING)) begin
                        if (chord_count < num_chords) begin
                            // Block ended but we need more chords
                            current_sector <= current_sector + 1;
                            state <= S_REQ_BLOCK;
                        end else begin
                            state <= S_DONE;
                        end
                    end
                end

                S_DONE: begin
                    busy <= 1'b0;
                    done <= 1'b1;
                    state <= S_IDLE;
                end

                S_ERROR: begin
                    busy <= 1'b0;
                    error <= 1'b1;
                    state <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
