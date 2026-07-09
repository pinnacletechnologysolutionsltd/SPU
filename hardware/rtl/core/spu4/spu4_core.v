// SPU-4 Symmetry Core (v1.0)
// Objective: A compact 4-axis (Quadray) core with TDM-folded ALU.
// Architecture: 4 axes (A,B,C,D) x 32 bits.
// Logic: Rational field Q(sqrt3) isotropic transformations.

module spu4_core (
    input  wire        clk,
    input  wire        reset,
    
    // SPI Physical Pins (For Sovereign Boot)
    output wire        spi_cs_n,
    output wire        spi_sck,
    output wire        spi_mosi,
    input  wire        spi_miso,
    
    // Sentinel Control
    input  wire        piranha_pulse,
    input  wire        sentinel_mode,

    // Programming Interface (From RP2040 PIO - Auxiliary)
    input  wire        prog_en_aux,
    input  wire [3:0]  prog_addr_aux,
    input  wire [15:0] prog_data_aux,
    input  wire        mode_autonomous,

    // Quadray Inputs (Used only in Slave Mode)
    input  wire [15:0] A_in, B_in, C_in, D_in,
    
    // Rotor Coefficients (Used only in Slave Mode)
    input  wire [15:0] F_rat, 
    input  wire [15:0] G_rat, 
    input  wire [15:0] H_rat, 
    
    // SovereignBus Interface (External PMODs)
    output wire [7:0]  bus_addr,
    output wire        bus_wen,
    output wire        bus_ren,
    input  wire        bus_ready,

    // AP Memory PSRAM PMOD Pins
    output wire        psram_ce_n,
    output wire        psram_clk,
    inout  wire [3:0]  psram_dq,
    
    // Quadray Outputs (Sovereign state)
    output wire [15:0] A_out, B_out, C_out, D_out,
    output wire        bloom_complete,

    // Dissonance — saturating |gasket_sum| for cluster bridge
    // per knowledge/SPU_LEXICON.md "Dissonance" entry (2026-07-08)
    output wire [7:0]  dissonance,

    // Whisper v1 coherence-plane emitter (Arlinghaus meso tier)
    // TX line for the constellation coherence plane.
    output wire        whisper_tx
);

    // 1. Soft-Start & Power Dispatch
    wire [7:0] bloom_intensity;
    spu_soft_start u_soft_start (
        .clk(clk),
        .rst_n(!reset),
        .bloom_intensity(bloom_intensity),
        .bloom_complete(bloom_complete)
    );

    // 2. Sovereign Boot Master (The Inhale)
    wire        inhale_en, inhale_done;
    wire [3:0]  inhale_addr;
    wire [15:0] inhale_data;
    
    spu4_boot_master u_boot (
        .clk(clk), .reset(reset),
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck), .spi_mosi(spi_mosi), .spi_miso(spi_miso),
        .inhale_en(inhale_en), .inhale_addr(inhale_addr), .inhale_data(inhale_data), .inhale_done(inhale_done)
    );

    // 3. Dream Sequencer (Autonomous Logic)
    wire [15:0] dream_instr;
    wire        dream_start;
    wire [3:0]  dream_pc;
    wire        alu_done;
    wire        alu_hush;
    
    // Configuration register via programming interface: prog_addr_aux==0xF
    wire prog_cfg_write;
    assign prog_cfg_write = prog_en_aux & (prog_addr_aux == 4'hF);
    wire prog_en_to_seq;
    assign prog_en_to_seq = inhale_en | (prog_en_aux & ~prog_cfg_write);

    reg [15:0] phinary_cfg;
    always @(posedge clk or posedge reset) begin
        if (reset) phinary_cfg <= 16'h0000;
        else if (prog_cfg_write) phinary_cfg <= prog_data_aux;
    end

    wire phinary_enable;
    assign phinary_enable = phinary_cfg[0];
    wire phinary_chirality;
    assign phinary_chirality = phinary_cfg[1];

    spu4_dream_sequencer u_sequencer (
        .clk(clk),
        .rst_n(!reset),
        .prog_en(prog_en_to_seq),
        .prog_addr(inhale_en ? inhale_addr : prog_addr_aux),
        .prog_data(inhale_en ? inhale_data : prog_data_aux),
        .inhale_done(inhale_done),
        .current_instr(dream_instr),
        .alu_start(dream_start),
        .alu_done(alu_done),
        .alu_hush(alu_hush),
        .piranha_pulse(piranha_pulse),
        .sentinel_mode(sentinel_mode),
        .pc(dream_pc)
    );

    // 4. SovereignBus Decoder
    assign bus_addr = dream_instr[7:0];
    assign bus_wen  = (dream_instr[15:12] == 4'h6);
    assign bus_ren  = (dream_instr[15:12] == 4'h7);

    // Folded ALU outputs — declared early so bus can reference alu_A
    wire [15:0] alu_A, alu_B, alu_C, alu_D;

    wire [22:0] psram_addr;
    wire        psram_rd_en, psram_wr_en;
    wire [15:0] psram_wr_data;
    wire        psram_ready_wire, psram_init_done;
    wire [15:0] psram_rd_data;

    spu4_sovereign_bus u_bus (
        .clk(clk), .reset(reset),
        .addr(bus_addr), .wen(bus_wen), .ren(bus_ren),
        .wr_data(alu_A),          // Write A-axis to RAM
        .addr_hi_wen(1'b0), .addr_hi_in(23'h0), // Future: RAM_SET_ADDR
        .psram_addr(psram_addr),
        .sel_pmod_mem(), .sel_pmod_gpu(), .sel_nerve(),
        .psram_rd_en(psram_rd_en), .psram_wr_en(psram_wr_en),
        .psram_wr_data(psram_wr_data),
        .psram_ready(psram_ready_wire),
        .ready()
    );

    // 5. AP Memory PSRAM Controller
    spu_psram_ctrl u_psram (
        .clk(clk), .reset(reset),
        .rd_en(psram_rd_en), .wr_en(psram_wr_en),
        .addr(psram_addr),
        .wr_data(psram_wr_data),
        .rd_data(psram_rd_data),
        .ready(psram_ready_wire),
        .init_done(psram_init_done),
        .psram_ce_n(psram_ce_n),
        .psram_clk(psram_clk),
        .psram_dq(psram_dq)
    );

    // 5. Folded ALU (TDM)
    // (alu_A-D wires declared before u_bus above)
    
    wire [15:0] F_eff;
    assign F_eff = mode_autonomous ? 16'h0050 : F_rat;
    wire [15:0] G_eff;
    assign G_eff = mode_autonomous ? 16'h00B5 : G_rat;
    wire [15:0] H_eff;
    assign H_eff = mode_autonomous ? 16'h0050 : H_rat;

    spu4_euclidean_alu u_alu (
        .clk(clk),
        .reset(reset | alu_hush), // Gate via reset for 'Laminar Hush'
        .start(mode_autonomous ? dream_start : 1'b1),
        .bloom_intensity(bloom_intensity),
        .mode_autonomous(mode_autonomous),
        .A_in(A_in), .B_in(B_in), .C_in(C_in), .D_in(D_in),
        .F(F_eff), .G(G_eff), .H(H_eff),
        .A_out(alu_A), .B_out(alu_B), .C_out(alu_C), .D_out(alu_D),
        .done(alu_done)
    );
    
    assign A_out = alu_A;
    assign B_out = alu_B;
    assign C_out = alu_C;
    assign D_out = alu_D;

    // Dissonance: saturating absolute value of gasket residual
    // dissonance[7:0] = min(|A+B+C+D|, 255)
    // 0x00 ⇔ laminar, 0xFF ⇔ saturated (|S| ≥ 255)
    wire signed [16:0] gasket_sum_ext;
    assign gasket_sum_ext = {alu_A[15], alu_A} + {alu_B[15], alu_B}
                          + {alu_C[15], alu_C} + {alu_D[15], alu_D};
    wire [16:0] abs_sum;
    assign abs_sum = gasket_sum_ext[16] ? (~gasket_sum_ext + 17'd1) : gasket_sum_ext;
    assign dissonance = (abs_sum > 17'd255) ? 8'hFF : abs_sum[7:0];

    // ── Whisper v1 coherence-plane emitter ──────────────────────────
    // The emitter continuously broadcasts the node's laminar state,
    // dissonance, and a sequence number while the core is operational.
    // Silence means incoherent or dead — the listener's 3-miss rule
    // detects this without any protocol handshake.
    //
    // is_laminar: system is operational after boot completes.
    // node_id:    hardwired per satellite; configurable via parameter.
    // flags_in:   snap_locked from sentinel_mode, henosis=0 (SPU-4
    //             has no tagged ROTC), relayed=0 (edge node).
    // dissonance: the gasket_sum residual from the ALU.
    localparam WHISPER_CLK_HZ  = 50000000;
    localparam WHISPER_BAUD    = 115200;
    localparam WHISPER_PERIOD  = WHISPER_CLK_HZ / 6000;

    wire is_laminar_w;
    assign is_laminar_w = bloom_complete && !reset;

    wire [2:0] whisper_flags;
    assign whisper_flags = {1'b0, 1'b0, sentinel_mode};  // {relayed, henosis, snap_locked}

    spu_whisper_v1_emitter #(
        .CLK_HZ(WHISPER_CLK_HZ), .BAUD(WHISPER_BAUD), .PERIOD_CYCLES(WHISPER_PERIOD)
    ) u_whisper (
        .clk(clk), .rst_n(!reset),
        .is_laminar(is_laminar_w),
        .node_id(4'h1),          // satellite ID: configurable per instance
        .flags_in(whisper_flags),
        .dissonance(dissonance),
        .som_label(8'h00),       // placeholder — wire edge SOM output here
        .tx(whisper_tx),
        .busy()
    );

    // Phinary chiral adder integration (enabled by default)
    wire [15:0] phin_A;
    assign phin_A = A_in;
    wire [15:0] phin_B;
    assign phin_B = B_in;
    wire [15:0] phout_S;
    wire phout_void;
    wire phout_ovf;

    chiral_phinary_adder_param #(
        .WIDTH(16),
        .INT_BITS(8),
        .LAMINAR_THR(16'h0A00)
    ) u_phinary_adder (
        .clk(clk),
        .rst(reset),
        .surd_A(phin_A),
        .surd_B(phin_B),
        .chirality(phinary_chirality),
        .surd_Sum(phout_S),
        .void_state(phout_void),
        .overflow(phout_ovf)
    );


endmodule
