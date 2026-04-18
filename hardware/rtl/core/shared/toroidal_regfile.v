// Toroidal register file prototype
// Parameterized width and number of registers. Provides two rotate methods:
//  - method_sel = 0: combinational rotate by amount (single-cycle update)
//  - method_sel = 1: serial rotate (one bit per cycle)

`timescale 1ns/1ps
module toroidal_regfile #(
    parameter WIDTH = 832,
    parameter NUM = 8,
    parameter ADDR_WIDTH = 3
)(
    input  wire clk,
    input  wire rst_n,

    // Write port (synchronous)
    input  wire                    wr_en,
    input  wire [ADDR_WIDTH-1:0]   wr_addr,
    input  wire [WIDTH-1:0]        wr_data,

    // Read port (synchronous)
    input  wire                    rd_en,
    input  wire [ADDR_WIDTH-1:0]   rd_addr,
    output reg  [WIDTH-1:0]        rd_data,

    // Rotate control
    input  wire                    rotate_start,
    input  wire [31:0]             rotate_amount, // bits
    input  wire [ADDR_WIDTH-1:0]   rotate_idx,    // which register
    input  wire                    rotate_dir,    // 0 = left, 1 = right
    input  wire                    method_sel,    // 0 = combinational, 1 = serial
    output reg                     rotate_done
);

    // Register storage
    reg [WIDTH-1:0] mem [0:NUM-1];

    // internal state for serial rotate
    reg rotate_busy;
    reg [31:0] s_remaining;

    integer i;

    // combinational rotate function (returns rotated value)
    function [WIDTH-1:0] rotate_comb;
        input [WIDTH-1:0] val;
        input [31:0] amt;
        input dir;
        integer kk;
        begin
            if (WIDTH == 0) begin
                rotate_comb = val;
            end else begin
                kk = (amt % WIDTH);
                if (kk == 0) begin
                    rotate_comb = val;
                end else begin
                    if (dir == 0) begin
                        rotate_comb = (val << kk) | (val >> (WIDTH - kk));
                    end else begin
                        rotate_comb = (val >> kk) | (val << (WIDTH - kk));
                    end
                end
            end
        end
    endfunction

    // single-step rotate (one-bit)
    function [WIDTH-1:0] rot_step;
        input [WIDTH-1:0] val;
        input dir;
        begin
            if (dir == 0) begin
                // rotate left by 1
                rot_step = {val[WIDTH-2:0], val[WIDTH-1]};
            end else begin
                // rotate right by 1
                rot_step = {val[0], val[WIDTH-1:1]};
            end
        end
    endfunction

    // synchronous behavior
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < NUM; i = i + 1) begin
                mem[i] <= {WIDTH{1'b0}};
            end
            rd_data <= {WIDTH{1'b0}};
            rotate_busy <= 1'b0;
            rotate_done <= 1'b0;
            s_remaining <= 32'd0;
        end else begin
            // write
            if (wr_en) begin
                mem[wr_addr] <= wr_data;
            end

            // read (synchronous)
            if (rd_en) begin
                rd_data <= mem[rd_addr];
            end

            // rotate control
            if (!rotate_busy && rotate_start) begin
                // quick path: zero rotation
                if ((rotate_amount % WIDTH) == 0) begin
                    rotate_done <= 1'b1;
                    rotate_busy <= 1'b0;
                end else begin
                    if (method_sel == 1'b0) begin
                        // combinational rotate applied synchronously (single cycle update)
                        mem[rotate_idx] <= rotate_comb(mem[rotate_idx], rotate_amount, rotate_dir);
                        rotate_done <= 1'b1;
                        rotate_busy <= 1'b0;
                    end else begin
                        // serial rotate: schedule multi-cycle shifts
                        rotate_busy <= 1'b1;
                        s_remaining <= (rotate_amount % WIDTH);
                        rotate_done <= 1'b0;
                    end
                end
            end else if (rotate_busy) begin
                if (s_remaining == 0) begin
                    rotate_busy <= 1'b0;
                    rotate_done <= 1'b1;
                end else begin
                    mem[rotate_idx] <= rot_step(mem[rotate_idx], rotate_dir);
                    s_remaining <= s_remaining - 1;
                    rotate_done <= 1'b0;
                end
            end else begin
                rotate_done <= 1'b0;
            end
        end
    end

endmodule
