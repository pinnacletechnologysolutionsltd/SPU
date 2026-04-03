// SPU-13 Manifold Mirror (v1.0)
// Target: Unified SPU-13 Fleet
// Objective: Stream bit-perfect copy of Onboard Flash to PMOD.
// Logic: Block-by-block 'Autophagic' Replication.

module spu_manifold_mirror (
    input  wire         clk,
    input  wire         reset,
    input  wire         start_mirror, // Triggered via MIRR instruction
    
    // --- Internal Flash (Source) ---
    output reg          int_read_en,
    output reg  [23:0]  int_addr,
    input  wire [255:0] int_data_in,
    input  wire         int_ready,
    
    // --- External PMOD (Destination) ---
    output reg          ext_write_en,
    output reg  [23:0]  ext_addr,
    output reg  [255:0] ext_data_out,
    input  wire         ext_ready,
    
    output reg          mirror_active,
    output reg          mirror_done
);

    reg [3:0] state;
    localparam IDLE=0, READ_BLOCK=1, WRITE_BLOCK=2, NEXT_BLOCK=3;
    
    reg [23:0] current_ptr;
    localparam MAX_ADDR = 24'h7FFFFF; // 8MB limit

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= IDLE; mirror_active <= 0; mirror_done <= 0;
            current_ptr <= 0; int_read_en <= 0; ext_write_en <= 0;
        end else begin
            case (state)
                IDLE: begin
                    if (start_mirror) begin
                        mirror_active <= 1;
                        mirror_done <= 0;
                        current_ptr <= 0;
                        state <= READ_BLOCK;
                    end
                end

                READ_BLOCK: begin
                    if (int_ready && !int_read_en) begin
                        int_read_en <= 1;
                        int_addr <= current_ptr;
                    end else if (int_read_en && int_ready) begin
                        int_read_en <= 0;
                        ext_data_out <= int_data_in;
                        state <= WRITE_BLOCK;
                    end
                end

                WRITE_BLOCK: begin
                    if (ext_ready && !ext_write_en) begin
                        ext_write_en <= 1;
                        ext_addr <= current_ptr;
                    end else if (ext_write_en && ext_ready) begin
                        ext_write_en <= 0;
                        state <= NEXT_BLOCK;
                    end
                end

                NEXT_BLOCK: begin
                    if (current_ptr >= MAX_ADDR) begin
                        mirror_active <= 0;
                        mirror_done <= 1;
                        state <= IDLE;
                    end else begin
                        current_ptr <= current_ptr + 24'd32; // Next 256-bit page
                        state <= READ_BLOCK;
                    end
                end
            endcase
        end
    end

endmodule
