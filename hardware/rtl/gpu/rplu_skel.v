// RPLU skeleton: parameterized multi-material ROM lookup (v2.0)
//
// v2.0: Expanded from 2-material (carbon/iron) to NUM_MATERIALS (default 4, max 16).
//       material_id is ceil(log2(NUM_MATERIALS)). ROM arrays loaded at boot via
//       cfg_wr_en interface from SPI flash.  $readmemh provides sim defaults.
//
// Material ID assignments:
//   0 = carbon   1 = iron   2 = aluminum   3 = silicon
//   4 = titanium 5 = nickel 6 = copper     7 = tungsten
//   8-15 = reserved (user-loadable via cfg interface)
//
// LUT cost: each material adds 1024×65 bits of distributed RAM (~66 Kb).
// Default NUM_MATERIALS=2 keeps baseline identical; set to 4 for engineering set.

module rplu_skel #(
    parameter NUM_MATERIALS = 2,
    parameter TABLE_DEPTH   = 1024,
    parameter ADDR_WIDTH    = 10
)(
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 start,
    input  wire [ADDR_WIDTH-1:0] addr,
    input  wire [3:0]           material_id,

    // Runtime config/write interface
    input  wire                 cfg_wr_en,
    input  wire [2:0]           cfg_wr_sel,
    input  wire [3:0]           cfg_wr_material,
    input  wire [ADDR_WIDTH-1:0] cfg_wr_addr,
    input  wire [63:0]          cfg_wr_data,

    output reg  signed [31:0]   p_out,
    output reg  signed [31:0]   q_out,
    output reg                  dissoc,
    output reg                  done
);

    // ── 2D ROM storage ──────────────────────────────────────────────
    reg [63:0] rom  [0:NUM_MATERIALS-1][0:TABLE_DEPTH-1];
    reg        diss [0:NUM_MATERIALS-1][0:TABLE_DEPTH-1];
    reg [63:0] init_rom_carbon [0:TABLE_DEPTH-1];
    reg [63:0] init_rom_iron   [0:TABLE_DEPTH-1];
    reg        init_diss_carbon[0:TABLE_DEPTH-1];
    reg        init_diss_iron  [0:TABLE_DEPTH-1];

    // Simulation defaults: carbon (0) and iron (1) from .mem files.
    // Yosys synthesis: BRAM inference from $readmemh on Gowin devices.
    initial begin : sim_init
        integer m, i;
        for (m = 0; m < NUM_MATERIALS; m = m + 1)
            for (i = 0; i < TABLE_DEPTH; i = i + 1) begin
                rom[m][i]  = 64'd0;
                diss[m][i] = 1'b0;
            end
        $readmemh("hardware/rtl/arch/rplu_rom_carbon.mem", init_rom_carbon);
        $readmemh("hardware/rtl/arch/rplu_rom_iron.mem", init_rom_iron);
        $readmemh("hardware/rtl/arch/rplu_dissoc_carbon.mem", init_diss_carbon);
        $readmemh("hardware/rtl/arch/rplu_dissoc_iron.mem", init_diss_iron);
        for (i = 0; i < TABLE_DEPTH; i = i + 1) begin
            if (NUM_MATERIALS >= 1) begin
                rom[0][i]  = init_rom_carbon[i];
                diss[0][i] = init_diss_carbon[i];
            end
            if (NUM_MATERIALS >= 2) begin
                rom[1][i]  = init_rom_iron[i];
                diss[1][i] = init_diss_iron[i];
            end
        end
    end

    // ── Runtime config writes (bootloader / artery) ─────────────────
    always @(posedge clk) begin
        if (cfg_wr_en && cfg_wr_material < NUM_MATERIALS) begin
            case (cfg_wr_sel)
                3'd0: rom[cfg_wr_material][cfg_wr_addr]  <= cfg_wr_data;
                3'd1: diss[cfg_wr_material][cfg_wr_addr] <= cfg_wr_data[0];
                default: ;
            endcase
        end
    end

    // ── 2-stage lookup pipeline ─────────────────────────────────────
    reg [63:0] dout_stage0;
    reg        diss_stage0;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dout_stage0 <= 64'd0;
            diss_stage0 <= 1'b0;
            p_out  <= 32'sd0;
            q_out  <= 32'sd0;
            dissoc <= 1'b0;
            done   <= 1'b0;
        end else begin
            done <= 1'b0;
            if (start) begin
                if (material_id < NUM_MATERIALS) begin
                    dout_stage0 <= rom[material_id][addr];
                    diss_stage0 <= diss[material_id][addr];
                end else begin
                    dout_stage0 <= 64'd0;
                    diss_stage0 <= 1'b0;
                end
            end
            p_out  <= $signed(dout_stage0[63:32]);
            q_out  <= $signed(dout_stage0[31:0]);
            dissoc <= diss_stage0;
            done   <= start;
        end
    end

endmodule
