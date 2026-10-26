// spu_hw_bootrom.v
// Autonomous Hardware Boot Sequencer
// Takes control of the SPI Flash bridge on power up, streams `N` payloads
// natively from offset 0x000000, formats them, and pushes them directly
// into the SPU Async FIFO. Yields control when complete.

module spu_hw_bootrom #(
    parameter ROM_PAYLOADS = 16  // How many 78-bit payloads to read
) (
    input  wire        clk,
    input  wire        rst_n,

    // Interface to spu_flash_bridge
    output reg         rd_trig,
    output reg  [23:0] rd_addr,
    output reg         burst,
    output reg         rd_stop,
    input  wire [7:0]  rd_data,
    input  wire        rd_done,

    // Interface to Configuration Mux (towards spu_async_fifo)
    output reg         fifo_wr,
    output reg  [77:0] fifo_data,
    input  wire        fifo_full,

    // System Status
    input  wire  [15:0] lfi,
    output reg          boot_done
);

    // 11 bytes per payload to ensure byte alignment:
    // Byte 0: {4'b0, sel[2:0], material[0]}
    // Byte 1: {6'b0, addr[9:8]}
    // Byte 2: {addr[7:0]}
    // Bytes 3..10: {data[63:0]} (8 bytes)
    localparam TOTAL_BYTES = ROM_PAYLOADS * 11; 

    reg [2:0]  state;
    localparam ST_INIT   = 3'd0;
    localparam ST_START  = 3'd1;
    localparam ST_STREAM = 3'd2;
    localparam ST_PUSH   = 3'd3;
    localparam ST_BREATH = 3'd4;
    localparam ST_DONE   = 3'd5;

    reg [3:0]  byte_idx; // 0..10 index within a single 11-byte payload
    reg [23:0] total_bytes_read;
    
    // Shift register for 11 bytes (88 bits)
    reg [87:0] payload_shift;
    reg [7:0]  timeout_cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_trig <= 1'b0;
            rd_addr <= 24'd0;
            burst   <= 1'b0;
            rd_stop <= 1'b0;
            
            fifo_wr   <= 1'b0;
            fifo_data <= 78'd0;
            
            boot_done <= 1'b0;
            
            state            <= ST_INIT;
            byte_idx         <= 4'd0;
            total_bytes_read <= 24'd0;
            payload_shift    <= 88'd0;
        end else begin
            rd_trig <= 1'b0;
            rd_stop <= 1'b0;
            fifo_wr <= 1'b0;

            case (state)
                ST_INIT: begin
                    if (ROM_PAYLOADS == 0) begin
                        boot_done <= 1'b1;
                        state <= ST_DONE;
                    end else begin
                        state <= ST_START;
                    end
                end

                ST_START: begin
                    rd_trig <= 1'b1;     // Kick off flash read
                    rd_addr <= 24'h0;    // Always start at offset 0
                    burst   <= 1'b1;     // Streaming mode
                    state   <= ST_STREAM;
                end

                ST_STREAM: begin
                    if (rd_done) begin
                        // Shift big-endian data byte into holding register
                        payload_shift <= {payload_shift[79:0], rd_data};
                        byte_idx <= byte_idx + 4'd1;
                        total_bytes_read <= total_bytes_read + 24'd1;

                        if (total_bytes_read == TOTAL_BYTES - 1) begin
                            // It's the very last byte
                            rd_stop <= 1'b1;
                            burst   <= 1'b0;
                        end

                        if (byte_idx == 4'd10) begin
                            // We have accumulated full 11 bytes (88 bits)
                            byte_idx <= 4'd0;
                            state <= ST_PUSH; // Wait for FIFO to be ready before pushing
                        end
                    end
                end

                ST_PUSH: begin
                    if (!fifo_full) begin
                        fifo_wr <= 1'b1;
                        
                        // Extract 78-bit payload from the 88-bit shift register.
                        // Since new bytes entered at the LSB, oldest byte (Byte 0) is at [87:80].
                        // Byte 1: [79:72], Byte 2: [71:64], Bytes 3..10: [63:0]
                        fifo_data <= {
                            payload_shift[83:81], // sel:      Byte 0 bits [3:1]
                            payload_shift[80],    // material: Byte 0 bit  [0]
                            payload_shift[73:72], // addr_hi:  Byte 1 bits [1:0]
                            payload_shift[71:64], // addr_lo:  Byte 2 bits [7:0]
                            payload_shift[63:0]   // data:     Bytes 3..10
                        };
                        
                        if (total_bytes_read >= TOTAL_BYTES) begin
                            state <= ST_BREATH;
                        end else begin
                            state <= ST_STREAM;
                        end
                    end
                end

                ST_BREATH: begin
                    // Inject Golden Seed (A=1, B=1) as a 78-bit config chord
                    if (!fifo_full && !boot_done) begin
                        fifo_wr <= 1'b1;
                        fifo_data <= {3'b010, 1'b0, 10'd0, 32'h0001_0001, 32'h0001_0001};
                        timeout_cnt <= timeout_cnt + 8'd1;
                    end

                    // Harmony reached! Proceed to normal operation.
                    if (lfi > 16'hF000) begin
                        state <= ST_DONE;
                        boot_done <= 1'b1;
                    end
                    // Timeout reached! Perform a "Default Flush" to stay alive.
                    else if (timeout_cnt == 8'hFF) begin
                        state <= ST_DONE;
                        boot_done <= 1'b1; // Proceed anyway, let supervisor handle the mess
                    end
                end

                ST_DONE: begin
                    boot_done <= 1'b1;
                end

                default: state <= ST_INIT;
            endcase
        end
    end

endmodule
