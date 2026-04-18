// spu4_sovereign_bus.v (v1.1 - Refractive Memory)
// Objective: Zero-latency Address Decoder + PSRAM Indirect Addressing.
// Standard: 8-bit direct | 24-bit indirect via addr_hi register.

module spu4_sovereign_bus (
    input  wire        clk,
    input  wire        reset,

    // 8-bit instruction address + R/W strobes
    input  wire [7:0]  addr,
    input  wire        wen,
    input  wire        ren,
    input  wire [15:0] wr_data,

    // 24-bit PSRAM indirect address (set via RAM_SET_ADDR instruction)
    input  wire        addr_hi_wen,
    input  wire [22:0] addr_hi_in,
    output reg  [22:0] psram_addr,

    // Core Register Selects (0x00–0x0F)
    output wire        sel_core_regs,

    // PMOD Selects
    output wire        sel_pmod_mem,   // 0x10–0x1F → AP Memory PSRAM
    output wire        sel_pmod_gpu,   // 0x20–0x2F → VGA
    output wire        sel_nerve,      // 0x30–0x3F → Whisper PWI

    // PSRAM passthrough
    output wire        psram_rd_en,
    output wire        psram_wr_en,
    output wire [15:0] psram_wr_data,

    // Ready (combinational for core regs; registered for PSRAM)
    input  wire        psram_ready,
    output wire        ready
);

    assign sel_core_regs  = (addr[7:4] == 4'h0);
    assign sel_pmod_mem   = (addr[7:4] == 4'h1);
    assign sel_pmod_gpu   = (addr[7:4] == 4'h2);
    assign sel_nerve      = (addr[7:4] == 4'h3);

    assign psram_rd_en    = sel_pmod_mem & ren;
    assign psram_wr_en    = sel_pmod_mem & wen;
    assign psram_wr_data  = wr_data;

    // 24-bit indirect address register (loaded by RAM_SET_ADDR)
    always @(posedge clk or posedge reset) begin
        if (reset)       psram_addr <= 23'h0;
        else if (addr_hi_wen) psram_addr <= addr_hi_in;
    end

    // Ready: PSRAM access needs to wait; everything else is zero-latency
    assign ready = sel_pmod_mem ? psram_ready : 1'b1;

endmodule
