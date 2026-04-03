// spu_register_file.v - Hardened for 15-Sigma Snap
module spu_register_file (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [2:0]  wr_addr,
    input  wire [17:0] wr_data,
    input  wire        wr_en,
    input  wire [2:0]  rd_addr,
    output wire [17:0] rd_data,
    input  wire [2:0]  tdm_slot // Added to verify Slot J
);
    localparam SLOT_J = 3'b100;
    reg [17:0] rf [7:0];
    
    initial begin
        rf[0] = 18'h1A785; // Initialize R0 to PHI_1
        rf[1] = 0; rf[2] = 0; rf[3] = 0;
        rf[4] = 0; rf[5] = 0; rf[6] = 0; rf[7] = 0;
    end

    // Hardened Write-Back: Latch on falling edge during Slot-J
    always @(negedge clk) begin
        if (!rst_n) begin
            rf[0] <= 18'h1A785; 
        end else if (wr_en && (tdm_slot == SLOT_J)) begin
            rf[wr_addr] <= wr_data;
        end
    end

    assign rd_data = rf[rd_addr];
endmodule
