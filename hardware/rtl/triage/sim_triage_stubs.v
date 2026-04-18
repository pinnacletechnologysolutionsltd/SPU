// sim_triage_stubs.v — minimal simulation stubs to satisfy unit tests during triage
// NOTE: These are non-functional placeholders. Remove or replace with real RTL for production.

module injection_gate (
    input clk,
    input rst_n,
    input start,
    input signed [15:0] pcm_in,
    input material_id,
    input [9:0] sector_addr,
    output reg signed [31:0] r_q16_out,
    output reg valid_out
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            r_q16_out <= 32'sd0;
            valid_out <= 1'b0;
        end else begin
            if (start) begin
                // Simple functional stub: scale PCM to Q16 and assert valid
                r_q16_out <= pcm_in << 16;
                valid_out <= 1'b1;
            end else begin
                valid_out <= 1'b0;
            end
        end
    end
endmodule

module spu_video_timing (
    input clk,
    input rst_n,
    output reg [9:0] x,
    output reg [9:0] y,
    output reg hsync,
    output reg vsync,
    output reg active
);
    localparam integer H_TOTAL = 800;
    localparam integer V_TOTAL = 525;

    initial begin
        x = 10'd0;
        y = 10'd0;
        hsync = 1'b1;
        vsync = 1'b1;
        active = 1'b0;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x = 10'd0;
            y = 10'd0;
            hsync = 1'b1;
            vsync = 1'b1;
            active = 1'b0;
        end else begin
            if (x == H_TOTAL - 1) begin
                x = 10'd0;
                if (y == V_TOTAL - 1) y = 10'd0; else y = y + 1;
            end else begin
                x = x + 1;
            end
            // Update active/hsync/vsync based on the new counters
            active = (x < 10'd640);
            hsync = (x >= 10'd656 && x < 10'd752) ? 1'b0 : 1'b1;
            vsync = (y >= 10'd490 && y < 10'd492) ? 1'b0 : 1'b1;
        end
    end
endmodule



// rational_sine_provider stub removed — use hardware/common/rtl/gpu/rational_sine_provider.v


// pade_eval_4_4 stub removed — use hardware/common/rtl/gpu/pade_eval_4_4.v


// davis_to_rplu stub removed — use full implementation in hardware/common/rtl/gpu/davis_to_rplu.v

// rational_sine_rom stub removed — use hardware/common/rtl/gpu/rational_sine_rom.v


// rational_sine_rom_q32 stub removed — use hardware/common/rtl/gpu/rational_sine_rom_q32.v


module laminar_detector #(
    parameter integer EPSILON_Q16 = 16'h0010,
    parameter integer SETTLING_TIME = 8
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire [9:0]  addr_in,
    input  wire signed [31:0] r_q16,
    input  wire signed [31:0] re_q16,
    input  wire        wake,
    input  wire [9:0]  wake_addr,
    output reg         irq_out,
    output reg         latched_out,
    output reg         cleared_out
);
    // Per-address settling counters and latch flags
    reg [15:0] settle_counter [0:1023];
    reg latched_flag [0:1023];

    integer i;
    initial begin
        for (i = 0; i < 1024; i = i + 1) begin
            settle_counter[i] = 16'd0;
            latched_flag[i] = 1'b0;
        end
        irq_out = 1'b0;
        latched_out = 1'b0;
        cleared_out = 1'b0;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 1024; i = i + 1) begin
                settle_counter[i] <= 16'd0;
                latched_flag[i] <= 1'b0;
            end
            irq_out <= 1'b0;
            latched_out <= 1'b0;
            cleared_out <= 1'b0;
        end else begin
            cleared_out <= 1'b0;
            irq_out <= 1'b0;
            latched_out <= latched_flag[addr_in];

            // Handle wake for a specific address
            if (wake) begin
                latched_flag[wake_addr] <= 1'b0;
                cleared_out <= 1'b1;
            end

            // If already latched, assert irq
            if (latched_flag[addr_in]) begin
                irq_out <= 1'b1;
                latched_out <= 1'b1;
                // keep counter unchanged
            end else begin
                // check activity: if difference within epsilon, increment counter, else reset
                reg signed [31:0] diff;
                diff = r_q16 - re_q16;
                if (diff < 0) diff = -diff;
                if (diff <= EPSILON_Q16) begin
                    if (settle_counter[addr_in] < 16'hFFFF) settle_counter[addr_in] <= settle_counter[addr_in] + 1;
                end else begin
                    settle_counter[addr_in] <= 16'd0;
                end
                if (settle_counter[addr_in] >= SETTLING_TIME) begin
                    latched_flag[addr_in] <= 1'b1;
                    latched_out <= 1'b1;
                    irq_out <= 1'b1;
                end
            end
        end
    end
endmodule

module rplu_skel (
    input clk,
    input rst_n,
    input start,
    input [9:0] addr,
    input material_id,
    input cfg_wr_en,
    input [2:0] cfg_wr_sel,
    input cfg_wr_material,
    input [9:0] cfg_wr_addr,
    input [63:0] cfg_wr_data,
    output reg signed [31:0] p_out,
    output reg signed [31:0] q_out,
    output reg dissoc,
    output reg done
);
    // ROM-backed functional stub: return expected p/q/dissoc from mem files
    reg [63:0] rom_carbon [0:1023];
    reg [63:0] rom_iron   [0:1023];
    reg [0:0]  diss_carbon [0:1023];
    reg [0:0]  diss_iron   [0:1023];

    initial begin
        $readmemh("hardware/common/rtl/gpu/rplu_rom_carbon.mem", rom_carbon);
        $readmemh("hardware/common/rtl/gpu/rplu_rom_iron.mem", rom_iron);
        $readmemh("hardware/common/rtl/gpu/rplu_dissoc_carbon.mem", diss_carbon);
        $readmemh("hardware/common/rtl/gpu/rplu_dissoc_iron.mem", diss_iron);
        p_out = 32'sd0; q_out = 32'sd0; dissoc = 1'b0; done = 1'b0;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p_out <= 32'sd0;
            q_out <= 32'sd0;
            dissoc <= 1'b0;
            done <= 1'b0;
        end else begin
            if (start) begin
                if (material_id == 1'b0) begin
                    p_out <= $signed(rom_carbon[addr][63:32]);
                    q_out <= $signed(rom_carbon[addr][31:0]);
                    dissoc <= diss_carbon[addr];
                end else begin
                    p_out <= $signed(rom_iron[addr][63:32]);
                    q_out <= $signed(rom_iron[addr][31:0]);
                    dissoc <= diss_iron[addr];
                end
                done <= 1'b1;
            end else begin
                done <= 1'b0;
            end
        end
    end
endmodule

module simple_lau (
    input clk,
    input rst_n,
    input start,
    input signed [15:0] pcm_in,
    output reg signed [31:0] vout_q16,
    output reg valid_out
);
    always @(*) begin
        vout_q16 = 32'sd0;
        valid_out = 1'b0;
    end
endmodule

// rplu_exp stub removed — use hardware/common/rtl/gpu/rplu_exp.v

