// RPLU skeleton: simple ROM-based lookup per material
module rplu_skel (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire [9:0] addr,          // 0..1023
    input wire material_id,         // 0 = carbon, 1 = iron
    // runtime config/write interface
    input wire cfg_wr_en,
    input wire [2:0] cfg_wr_sel,
    input wire cfg_wr_material,
    input wire [9:0] cfg_wr_addr,
    input wire [63:0] cfg_wr_data,
    output reg signed [31:0] p_out,
    output reg signed [31:0] q_out,
    output reg dissoc,
    output reg done
);

    reg [63:0] rom_carbon [0:1023];
    reg [63:0] rom_iron   [0:1023];
    reg [0:0]  diss_carbon[0:1023];
    reg [0:0]  diss_iron  [0:1023];

    initial begin
        $readmemh("hardware/common/rtl/gpu/rplu_rom_carbon.mem", rom_carbon);
        $readmemh("hardware/common/rtl/gpu/rplu_rom_iron.mem", rom_iron);
        $readmemh("hardware/common/rtl/gpu/rplu_dissoc_carbon.mem", diss_carbon);
        $readmemh("hardware/common/rtl/gpu/rplu_dissoc_iron.mem", diss_iron);
    end

    // allow runtime writes to the ROMs/dissoc arrays
    always @(posedge clk) begin
        if (cfg_wr_en) begin
            if (cfg_wr_sel == 3'd0) begin
                // write 64-bit packed P/Q into ROM for chosen material
                if (cfg_wr_material == 1'b0) rom_carbon[cfg_wr_addr] <= cfg_wr_data;
                else rom_iron[cfg_wr_addr] <= cfg_wr_data;
            end else if (cfg_wr_sel == 3'd1) begin
                // write dissociation bit
                if (cfg_wr_material == 1'b0) diss_carbon[cfg_wr_addr] <= cfg_wr_data[0];
                else diss_iron[cfg_wr_addr] <= cfg_wr_data[0];
            end
        end
    end

    // two-stage register to ensure outputs are valid one cycle after start
    reg [63:0] dout_stage0;
    reg       diss_stage0;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dout_stage0 <= 64'd0;
            diss_stage0 <= 1'b0;
            p_out <= 32'sd0;
            q_out <= 32'sd0;
            dissoc <= 1'b0;
            done <= 1'b0;
        end else begin
            // default
            done <= 1'b0;
            // stage0: capture ROM on start
            if (start) begin
                if (material_id == 1'b0) begin
                    dout_stage0 <= rom_carbon[addr];
                    diss_stage0 <= diss_carbon[addr];
                end else begin
                    dout_stage0 <= rom_iron[addr];
                    diss_stage0 <= diss_iron[addr];
                end
            end
            // stage1: present outputs from stage0
            p_out <= $signed(dout_stage0[63:32]);
            q_out <= $signed(dout_stage0[31:0]);
            dissoc <= diss_stage0;
            // indicate done when start was asserted in previous cycle (approx)
            done <= start;
        end
    end
endmodule
