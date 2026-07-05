// toroidal_regfile_ecc.v — Toroidal Register File with Integrity Check
//
// Adds per-entry XOR checksum detection on top of toroidal_regfile.
// 832-bit data → 32-bit XOR of all 32-bit words stored alongside each entry.
// On read, checksum is verified and integrity flag asserted on mismatch.
//
// Copyright 2026 John Curley — CC0 1.0 Universal

module toroidal_regfile_ecc #(
    parameter WIDTH = 832,
    parameter NUM = 8,
    parameter ADDR_WIDTH = 3,
    // Number of 32-bit words per entry (WIDTH/32, must be integer)
    parameter WORDS = WIDTH / 32
)(
    input  wire clk,
    input  wire rst_n,
    input  wire                    wr_en,
    input  wire [ADDR_WIDTH-1:0]   wr_addr,
    input  wire [WIDTH-1:0]        wr_data,
    input  wire                    rd_en,
    input  wire [ADDR_WIDTH-1:0]   rd_addr,
    output wire [WIDTH-1:0]        rd_data,
    input  wire                    rotate_start,
    input  wire [31:0]             rotate_amount,
    input  wire [ADDR_WIDTH-1:0]   rotate_idx,
    input  wire                    rotate_dir,
    input  wire                    method_sel,
    output wire                    rotate_done,
    output wire                    integrity_error   // set when read checksum mismatches
);

    // ── Internal toroidal regfile ────────────────────────────────
    wire [WIDTH-1:0] raw_rd;
    wire             raw_rot_done;

    toroidal_regfile #(.WIDTH(WIDTH), .NUM(NUM), .ADDR_WIDTH(ADDR_WIDTH))
    u_torus (
        .clk(clk), .rst_n(rst_n),
        .wr_en(wr_en), .wr_addr(wr_addr), .wr_data(wr_data),
        .rd_en(rd_en), .rd_addr(rd_addr), .rd_data(raw_rd),
        .rotate_start(rotate_start), .rotate_amount(rotate_amount),
        .rotate_idx(rotate_idx), .rotate_dir(rotate_dir),
        .method_sel(method_sel), .rotate_done(raw_rot_done)
    );

    assign rotate_done = raw_rot_done;

    // ── Checksum storage ─────────────────────────────────────────
    reg [31:0] chk_store [0:NUM-1];

    // ── Checksum: XOR of all 32-bit words in the entry ───────────
    function [31:0] entry_checksum;
        input [WIDTH-1:0] d;
        reg [31:0] acc;
        integer i;
        begin
            acc = 32'd0;
            for (i = 0; i < WORDS; i = i + 1)
                acc = acc ^ d[i*32 +: 32];
            entry_checksum = acc;
        end
    endfunction

    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < NUM; i = i + 1)
                chk_store[i] <= 32'd0;
        end else if (wr_en) begin
            chk_store[wr_addr] <= entry_checksum(wr_data);
        end
    end

    // ── Checksum verification on read ─────────────────────────────
    reg integrity_error_r;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            integrity_error_r <= 1'b0;
        end else if (rd_en) begin
            integrity_error_r <= (entry_checksum(raw_rd) != chk_store[rd_addr]);
        end
    end

    assign rd_data = raw_rd;
    assign integrity_error = integrity_error_r;

endmodule
