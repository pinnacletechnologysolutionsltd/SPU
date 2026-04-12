// SPU Laminar Power Dispatcher (v4.1)
// Hardened for "Laminar Purity" (Zero-Branch Logic).
// Objective: Implement bitwise parametric state scaling for the manifold.
//
// New in v4.1: channel_stress input from SPU_WHISPER_RX.
//   When channel_stress >= STRESS_CAP the effective bloom intensity is clamped,
//   preventing the manifold from running at full power on a degraded channel.
//   Four stress tiers map onto the existing 4 intensity bands:
//     stress < 0x40 → no cap (full bloom_intensity used)
//     stress < 0x80 → cap at 0xC0 (75%)
//     stress < 0xC0 → cap at 0x80 (50%)
//     stress >= 0xC0 → cap at 0x40 (25%) — sustained channel degradation

module spu_laminar_power #(
    parameter WIDTH = 128 // SPU-4 Default
)(
    input  wire             clk,
    input  wire             rst_n,
    input  wire             reset,           // (optional) active-high compatibility
    input  wire [7:0]       bloom_intensity,
    input  wire [7:0]       channel_stress,   // from SPU_WHISPER_RX; 0=clean 0xFF=severe
    input  wire [WIDTH-1:0] reg_in,
    output reg  [WIDTH-1:0] reg_out,
    input  wire [2:0]       boot_phase,       // compatibility (opcode -> boot-phase mapping)
    output wire             henosis_active    // compatibility output
);

// Compatibility wiring: prefer explicit reset if provided
wire rst_n_local;
assign rst_n_local = (reset === 1'bx) ? rst_n : ~reset;
assign henosis_active = 1'b0; // default stub (no henosis signalling in this triage build)

    // ── Stress-derived intensity cap (Laminar mux, no branches) ──────────
    wire [7:0] stress_cap =
        ({8{channel_stress >= 8'hC0}} & 8'h40) |
        ({8{channel_stress >= 8'h80 && channel_stress < 8'hC0}} & 8'h80) |
        ({8{channel_stress >= 8'h40 && channel_stress < 8'h80}} & 8'hC0) |
        ({8{channel_stress <  8'h40}} & 8'hFF);

    wire [7:0] eff_intensity = (bloom_intensity < stress_cap)
                             ? bloom_intensity : stress_cap;

    // ── Power Scale Mux Controls (Algebraic Selection) ───────────────────
    wire c_100;
    assign c_100 = (eff_intensity == 8'hFF);
    wire c_75;
    assign c_75 = (eff_intensity >= 8'hC0 && !c_100);
    wire c_50;
    assign c_50 = (eff_intensity >= 8'h80 && !c_100 && !c_75);
    wire c_25;
    assign c_25 = (eff_intensity >= 8'h40 && !c_100 && !c_75 && !c_50);
    wire c_0;
    assign c_0 = (!c_100 && !c_75 && !c_50 && !c_25);

    wire [WIDTH-1:0] val_100;
    assign val_100 = reg_in;
    wire [WIDTH-1:0] val_75;
    assign val_75 = reg_in - (reg_in >> 2);
    wire [WIDTH-1:0] val_50;
    assign val_50 = (reg_in >> 1);
    wire [WIDTH-1:0] val_25;
    assign val_25 = (reg_in >> 2);
    wire [WIDTH-1:0] val_0;
    assign val_0 = {WIDTH{1'b0}};

    wire [WIDTH-1:0] next_out =
        ({WIDTH{c_100}} & val_100) |
        ({WIDTH{c_75}}  & val_75)  |
        ({WIDTH{c_50}}  & val_50)  |
        ({WIDTH{c_25}}  & val_25)  |
        ({WIDTH{c_0}}   & val_0);

    always @(posedge clk) begin
        if (!rst_n_local)
            reg_out <= {WIDTH{1'b0}};
        else
            reg_out <= next_out;
    end

endmodule
