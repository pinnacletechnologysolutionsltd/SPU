// spu4_regfile.v
// 8-Register File for 4D± Quadray Coordinates (64-bit per Reg)
// Hardened for "Laminar Purity" (Zero-Branch & Strictly Bitwise).

module spu4_regfile (
    input clk,
    input rst_n,
    input we,                   // Write Enable
    input [2:0] addr_a,         // Read/Write Address A (Destination)
    input [2:0] addr_b,         // Read Address B (Source)
    input [63:0] din,           // Data Input (from ALU)
    output [63:0] dout_a,       // Data Output A
    output [63:0] dout_b        // Data Output B
);

    // 8 Registers, each 64 bits (4x16-bit Quadray components)
    reg [63:0] rf [7:0];

    // Laminar Write Mux Logic
    wire [7:0] sel_w;
    assign sel_w[0] = we && (addr_a == 3'd0);
    assign sel_w[1] = we && (addr_a == 3'd1);
    assign sel_w[2] = we && (addr_a == 3'd2);
    assign sel_w[3] = we && (addr_a == 3'd3);
    assign sel_w[4] = we && (addr_a == 3'd4);
    assign sel_w[5] = we && (addr_a == 3'd5);
    assign sel_w[6] = we && (addr_a == 3'd6);
    assign sel_w[7] = we && (addr_a == 3'd7);

    // Sync Update Loop (All registers in the manifold update every pulse)
    always @(posedge clk) begin
        // R0 defaults to Unit Vector [1,0,0,0] on reset
        rf[0] <= ({64{!rst_n}} & 64'h0100_0000_0000_0000) |
                 ({64{rst_n && sel_w[0]}} & din) |
                 ({64{rst_n && !sel_w[0]}} & rf[0]);
                 
        // R1-R7 default to 0 on reset
        rf[1] <= ({64{rst_n && sel_w[1]}} & din) | ({64{rst_n && !sel_w[1]}} & rf[1]) | ({64{!rst_n}} & 64'h0);
        rf[2] <= ({64{rst_n && sel_w[2]}} & din) | ({64{rst_n && !sel_w[2]}} & rf[2]) | ({64{!rst_n}} & 64'h0);
        rf[3] <= ({64{rst_n && sel_w[3]}} & din) | ({64{rst_n && !sel_w[3]}} & rf[3]) | ({64{!rst_n}} & 64'h0);
        rf[4] <= ({64{rst_n && sel_w[4]}} & din) | ({64{rst_n && !sel_w[4]}} & rf[4]) | ({64{!rst_n}} & 64'h0);
        rf[5] <= ({64{rst_n && sel_w[5]}} & din) | ({64{rst_n && !sel_w[5]}} & rf[5]) | ({64{!rst_n}} & 64'h0);
        rf[6] <= ({64{rst_n && sel_w[6]}} & din) | ({64{rst_n && !sel_w[6]}} & rf[6]) | ({64{!rst_n}} & 64'h0);
        rf[7] <= ({64{rst_n && sel_w[7]}} & din) | ({64{rst_n && !sel_w[7]}} & rf[7]) | ({64{!rst_n}} & 64'h0);
    end

    // Asynchronous Read
    assign dout_a = rf[addr_a];
    assign dout_b = rf[addr_b];

endmodule
