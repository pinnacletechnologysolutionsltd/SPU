// SPU System Orchestrator (v2.3 - TDM Sovereign Integration)
// Objective: Dual-Clock Orchestration for Resource-Folded Manifolds.
// Features: 24 MHz TDM Clock + 61.44 kHz Piranha Heartbeat.

module spu_system (
    input  wire        clk_ghost,     // 133 MHz Ghost OS Domain
    input  wire        clk_piranha,   // 61.44 kHz Master Pulse (Sovereign Domain)
    input  wire        clk_fast,      // 24 MHz TDM Clock (SPU Internal)
    input  wire        rst_n,
    
    // Ghost OS (Artery PIO)
    input  wire        wr_en,
    input  wire [63:0] wr_data,
    output wire        fifo_full,

    // RPLU config broadcast (piranha domain) — pulsed on DATA chord
    output wire        rplu_cfg_wr_en,
    output wire [2:0]  rplu_cfg_sel,
    output wire        rplu_cfg_material,
    output wire [9:0]  rplu_cfg_addr,
    output wire [63:0] rplu_cfg_data,

    // External RPLU CFG inputs (fast domain) — optional: connect board SPI loader here
    input  wire        ext_rplu_cfg_wr_en_fast,
    input  wire [2:0]  ext_rplu_cfg_sel_fast,
    input  wire        ext_rplu_cfg_material_fast,
    input  wire [9:0]  ext_rplu_cfg_addr_fast,
    input  wire [63:0] ext_rplu_cfg_data_fast,

    // PMOD SPI Flash (Autonomous Bootloader)
    output wire        pmod_sclk,
    output wire        pmod_cs_n,
    output wire        pmod_mosi,
    input  wire        pmod_miso,

    // SPI Slave Interface (for RP2350 Artery/Status)
    input  wire        spi_cs_n,
    input  wire        spi_sck,
    input  wire        spi_mosi,
    output wire        spi_miso,

    // Manifold Telemetry
    output wire [831:0] manifold_state,
    output wire [7:0]   satellite_snaps,
    output wire         is_janus_point,

    // I2S Audio Output (PCM5102A)
    output wire         i2s_bclk,
    output wire         i2s_lrclk,
    output wire         i2s_dout,

    // Proprioception alerts
    output wire         turbulence_alert,

    // SD Card (SAS Inhaler)
    output wire         sd_cs,
    output wire         sd_sck,
    output wire         sd_mosi,
    input  wire         sd_miso,

    // External Manifold Memory Bus (for DDR3/PSRAM expansion)
    input  wire                   master_mode, // 1 = Use external bus, 0 = Internal BRAM
    input  wire                   ext_mem_ready,
    output wire                   ext_mem_burst_rd,
    output wire                   ext_mem_burst_wr,
    output wire [23:0]            ext_mem_addr,
    input  wire [831:0]           ext_mem_rd_manifold,
    output wire [831:0]           ext_mem_wr_manifold,
    input  wire                   ext_mem_burst_done,

    // Industrial Gateway I/O (HUB75 Physical Interface)
    input  wire [3:0]             industrial_inputs,
    output wire [55:0]            industrial_io
);

    // Reset alias (active-high) for legacy modules that expect active-high reset
    wire reset = ~rst_n;

    // 1. Artery FIFO Bridge (Asynchronous Breath)
    wire [63:0] inhale_chord;
    wire        inhale_empty;
    reg         inhale_rd_en;

    // Allow internal CPU (SPU13 core) to issue RPLU runtime writes via CDC
    wire cortex_artery_wr_en;
    wire [63:0] cortex_artery_wr_data;

    // Forward declarations for signals used before formal definition
    wire        sd_inhaler_busy;
    wire        active_inhale_wr_en;
    wire [63:0] active_inhale_chord;
    reg         inhale_primed;
    reg [3:0]   inhale_axis_ptr;
    wire        phi_21;
    wire [1:0]  audio_mode;

    // Artery FIFO remains driven solely by the Ghost OS PIO (wr_en/wr_data)
    spu_artery_fifo u_artery (
        .wr_clk(clk_ghost), .wr_rst_n(rst_n),
        .wr_en(wr_en), .wr_data(wr_data), .full(fifo_full),
        .rd_clk(clk_piranha), .rd_rst_n(rst_n),
        .rd_en(inhale_rd_en), .rd_data(inhale_chord), .empty(inhale_empty)
    );

    // CDC: move SPU13 core-originated config writes (fast -> piranha)
    wire        core_piranha_cfg_wr_en;
    wire [2:0]  core_piranha_cfg_sel;
    wire        core_piranha_cfg_material;
    wire [9:0]  core_piranha_cfg_addr;
    wire [63:0] core_piranha_cfg_data;

    rplu_cfg_cdc u_cdc_core2p (
        .clk_src       (clk_fast),
        .rst_n_src     (rst_n),
        .wr_src        (cortex_artery_wr_en),
        .sel_src       (cortex_artery_wr_data[50:48]),
        .material_src  (cortex_artery_wr_data[47]),
        .addr_src      (cortex_artery_wr_data[46:37]),
        .data_src      (cortex_artery_wr_data),
        .clk_dst       (clk_piranha),
        .rst_n_dst     (rst_n),
        .wr_dst        (core_piranha_cfg_wr_en),
        .sel_dst       (core_piranha_cfg_sel),
        .material_dst  (core_piranha_cfg_material),
        .addr_dst      (core_piranha_cfg_addr),
        .data_dst      (core_piranha_cfg_data)
    );

    // Artery → RPLU decoder (optional runtime updates). Listens to inhaled chords
    // and produces a single-cycle write pulse with parameters on DATA chord.
    // V2.0: Now listens to active_inhale_chord (SD + Supervisor) after Mother hydration.
    wire dec_inhale_valid;
    assign dec_inhale_valid = inhale_primed ? active_inhale_wr_en : (inhale_rd_en && !sd_inhaler_busy);

    wire        dec_cfg_wr_en;
    wire [2:0]  dec_cfg_sel;
    wire        dec_cfg_material;
    wire [9:0]  dec_cfg_addr;
    wire [63:0] dec_cfg_data;

    rplu_artery_decoder u_rplu_dec (
        .clk(clk_piranha),
        .rst_n(rst_n),
        .inhale_valid(dec_inhale_valid),
        .inhale_chord(active_inhale_chord),
        .cfg_wr_en(dec_cfg_wr_en),
        .cfg_wr_sel(dec_cfg_sel),
        .cfg_wr_material(dec_cfg_material),
        .cfg_wr_addr(dec_cfg_addr),
        .cfg_wr_data(dec_cfg_data)
    );

    // -----------------------------------------------------------------
    // CDC: move external fast-domain RPLU writes (e.g., SPI loader) into
    // the piranha domain so runtime updates can be applied safely.
    // -----------------------------------------------------------------
    wire        ext_piranha_cfg_wr_en;
    wire [2:0]  ext_piranha_cfg_sel;
    wire        ext_piranha_cfg_material;
    wire [9:0]  ext_piranha_cfg_addr;
    wire [63:0] ext_piranha_cfg_data;

    // -----------------------------------------------------------------
    // Autonomous Hardware Bootrom & Config Mux
    // -----------------------------------------------------------------
    wire        hw_rd_trig;
    wire [23:0] hw_rd_addr;
    wire        hw_burst;
    wire        hw_rd_stop;
    wire [7:0]  hw_rd_data;
    wire        hw_rd_done;

    spu_flash_bridge u_flash (
        .clk(clk_fast),
        .rst_n(rst_n),
        .rd_trig(hw_rd_trig),
        .rd_addr(hw_rd_addr),
        .burst(hw_burst),
        .rd_stop(hw_rd_stop),
        .rd_data(hw_rd_data),
        .rd_done(hw_rd_done),
        .flash_sclk(pmod_sclk),
        .flash_cs_n(pmod_cs_n),
        .flash_mosi(pmod_mosi),
        .flash_miso(pmod_miso)
    );

    wire        hw_boot_done;
    wire        hw_fifo_wr;
    wire [77:0] hw_fifo_data;

    // Proprioception exports from Core
    wire [15:0] gasket_sum_out;
    wire [31:0] quadrance_out;
    wire        cycle_wrap;
    wire        rplu_dissoc_out;

    // ------------------------------------------------------------------ //
    // 8. Rational Proprioception (Health Monitor)                       //
    // ------------------------------------------------------------------ //
    wire [15:0] laminar_index;
    spu_proprioception u_proprio (
        .clk(clk_fast),
        .rst_n(rst_n),
        .gasket_sum(gasket_sum_out),
        .quadrance(quadrance_out),
        .pulse_commit(phi_21),
        .cycle_wrap(cycle_wrap),
        .rplu_dissoc(rplu_dissoc_out),
        .laminar_index(laminar_index),
        .turbulence_alert(turbulence_alert)
    );

    spu_hw_bootrom #(.ROM_PAYLOADS(16)) u_bootrom (
        .clk(clk_fast),
        .rst_n(rst_n),
        .rd_trig(hw_rd_trig),
        .rd_addr(hw_rd_addr),
        .burst(hw_burst),
        .rd_stop(hw_rd_stop),
        .rd_data(hw_rd_data),
        .rd_done(hw_rd_done),
        .fifo_wr(hw_fifo_wr),
        .fifo_data(hw_fifo_data),
        .fifo_full(1'b0), // The async fifo handles bursts fine behind the mux
        .lfi(laminar_index),
        .boot_done(hw_boot_done)
    );

    wire        mux_rplu_cfg_wr_en;
    wire [77:0] mux_rplu_cfg_data;

    spu_cfg_mux u_cfg_mux (
        .boot_done(hw_boot_done),
        .hw_fifo_wr(hw_fifo_wr),
        .hw_fifo_data(hw_fifo_data),
        .io_fifo_wr(ext_rplu_cfg_wr_en_fast),
        .io_fifo_data({ext_rplu_cfg_sel_fast, ext_rplu_cfg_material_fast, ext_rplu_cfg_addr_fast, ext_rplu_cfg_data_fast}),
        .out_fifo_wr(mux_rplu_cfg_wr_en),
        .out_fifo_data(mux_rplu_cfg_data)
    );

    rplu_cfg_cdc u_cdc_fast2p (
        .clk_src       (clk_fast),
        .rst_n_src     (rst_n),
        .wr_src        (mux_rplu_cfg_wr_en),
        .sel_src       (mux_rplu_cfg_data[77:75]),
        .material_src  (mux_rplu_cfg_data[74]),
        .addr_src      (mux_rplu_cfg_data[73:64]),
        .data_src      (mux_rplu_cfg_data[63:0]),
        .clk_dst       (clk_piranha),
        .rst_n_dst     (rst_n),
        .wr_dst        (ext_piranha_cfg_wr_en),
        .sel_dst       (ext_piranha_cfg_sel),
        .material_dst  (ext_piranha_cfg_material),
        .addr_dst      (ext_piranha_cfg_addr),
        .data_dst      (ext_piranha_cfg_data)
    );

    // Merge: external piranha-side writes take top priority, followed by core-originated
    // fast-domain writes (via CDC), then decoder-originated inhaled chords.
    assign rplu_cfg_wr_en       = ext_piranha_cfg_wr_en | core_piranha_cfg_wr_en | dec_cfg_wr_en;
    assign rplu_cfg_sel         = ext_piranha_cfg_wr_en ? ext_piranha_cfg_sel
                                    : (core_piranha_cfg_wr_en ? core_piranha_cfg_sel : dec_cfg_sel);
    assign rplu_cfg_material    = ext_piranha_cfg_wr_en ? ext_piranha_cfg_material
                                    : (core_piranha_cfg_wr_en ? core_piranha_cfg_material : dec_cfg_material);
    assign rplu_cfg_addr        = ext_piranha_cfg_wr_en ? ext_piranha_cfg_addr
                                    : (core_piranha_cfg_wr_en ? core_piranha_cfg_addr : dec_cfg_addr);
    assign rplu_cfg_data        = ext_piranha_cfg_wr_en ? ext_piranha_cfg_data
                                    : (core_piranha_cfg_wr_en ? core_piranha_cfg_data : dec_cfg_data);

    // Global Sentinel PLC Mode Control (Channel 5)
    reg global_sentinel_mode;
    always @(posedge clk_fast or negedge rst_n) begin
        if (!rst_n) global_sentinel_mode <= 1'b0;
        else if (ext_piranha_cfg_wr_en && ext_piranha_cfg_sel == 3'd5)
            global_sentinel_mode <= ext_piranha_cfg_data[0];
    end

    // RPLU Mode Register (Channel 6) — RP2350 Software Trigger
    //   0 = Smooth Flow  : Bank 0, Q(sqrt3) prime rational bases
    //   1 = Turbulent    : Bank 1, Q(sqrt5) Fibonacci ladder (deep surd bisection)
    // Write via SPI CMD 0xA5 with sel=6, data[0]=mode.
    // Read back via SPI CMD 0xAC byte[3][0].
    reg rplu_mode;
    always @(posedge clk_fast or negedge rst_n) begin
        if (!rst_n) rplu_mode <= 1'b0;
        else if (ext_piranha_cfg_wr_en && ext_piranha_cfg_sel == 3'd6)
            rplu_mode <= ext_piranha_cfg_data[0];
    end

    // -----------------------------------------------------------------
    // CDC: forward decoder (piranha) writes to fast domain for fast-domain
    // RPLU consumers. This provides a safe path for piranha-originated
    // writes to be visible in the fast clock domain.
    // -----------------------------------------------------------------
    wire        dec_fast_cfg_wr_en;
    wire [2:0]  dec_fast_cfg_sel;
    wire        dec_fast_cfg_material;
    wire [9:0]  dec_fast_cfg_addr;
    wire [63:0] dec_fast_cfg_data;

    // Forward the merged RPLU config bus (external piranha, core-originated, or decoder)
    // into the fast domain so rplu consumers in the fast clock (e.g., rplu_exp)
    // observe the complete set of runtime writes.
    rplu_cfg_cdc u_cdc_p2f (
        .clk_src       (clk_piranha),
        .rst_n_src     (rst_n),
        .wr_src        (rplu_cfg_wr_en),
        .sel_src       (rplu_cfg_sel),
        .material_src  (rplu_cfg_material),
        .addr_src      (rplu_cfg_addr),
        .data_src      (rplu_cfg_data),
        .clk_dst       (clk_fast),
        .rst_n_dst     (rst_n),
        .wr_dst        (dec_fast_cfg_wr_en),
        .sel_dst       (dec_fast_cfg_sel),
        .material_dst  (dec_fast_cfg_material),
        .addr_dst      (dec_fast_cfg_addr),
        .data_dst      (dec_fast_cfg_data)
    );

    // 2. Phi-Gated Pulse Generation (from 24 MHz TDM clock)
    wire phi_8, phi_13, phi_heart;
    spu_sierpinski_clk u_clk (
        .clk(clk_fast), .rst_n(rst_n),
        .phi_8(phi_8), .phi_13(phi_13), .phi_21(phi_21),
        .heartbeat(phi_heart)
    );

    // 3. Manifold Memory Model (Internal BRAM vs External Bridge)
    reg  [831:0] int_mem;
    wire         int_mem_ready = 1'b1;
    reg          int_mem_burst_done;

    // Arbitration: Use external memory if master_mode is set (e.g. Gowin with DDR3)
    assign mem_ready           = master_mode ? ext_mem_ready       : int_mem_ready;
    assign ext_mem_burst_rd    = master_mode ? mem_burst_rd        : 1'b0;
    assign ext_mem_burst_wr    = master_mode ? mem_burst_wr        : 1'b0;
    assign ext_mem_addr        = master_mode ? mem_addr            : 24'h0;
    assign ext_mem_wr_manifold = master_mode ? mem_wr_manifold     : 832'h0;
    
    assign mem_rd_manifold     = master_mode ? ext_mem_rd_manifold : int_mem;
    assign mem_burst_done      = master_mode ? ext_mem_burst_done  : int_mem_burst_done;

    wire [831:0] mem_wr_manifold; // Driven by SPU core
    wire [831:0] mem_rd_manifold; // Read by SPU core
    wire         mem_burst_rd;
    wire         mem_burst_wr;
    wire [23:0]  mem_addr;
    wire         mem_ready;
    wire         mem_burst_done;

    // 4. Sovereign Mother Unit (SPU-13 Cortex)
    wire [831:0] manifold_out;
    wire         bloom_done;
    // Cortex debug/status outputs (triage ties)
    wire [3:0]   current_axis_ptr;
    wire [63:0]  current_axis_data;
    wire signed [2:0] ratio_cmp_res;
    wire               ratio_cmp_valid;
    wire [51:0] scale_table_out;
    wire [12:0] scale_overflow_out;

    spu13_core #(.DEVICE("GW5A")) u_cortex (
        .clk(clk_fast),
        .rst_n(rst_n),
        .phi_8(phi_8), .phi_13(phi_13), .phi_21(phi_21),
        .dec_fast_cfg_wr_en(dec_fast_cfg_wr_en),
        .dec_fast_cfg_sel(dec_fast_cfg_sel),
        .dec_fast_cfg_material({7'd0, dec_fast_cfg_material}),
        .dec_fast_cfg_addr(dec_fast_cfg_addr),
        .dec_fast_cfg_data(dec_fast_cfg_data),
        .phinary_cfg(16'd0),
        .prime_data(24'd0),
        .prime_addr(4'd0),
        .prime_we(1'b0),
        .boot_done(1'b1),
        .pell_data(32'd0),
        .pell_addr(3'd0),
        .pell_we(1'b0),
        .manual_rotor_en(1'b0),
        .manual_rotor_data(64'd0),
        .mem_ready(mem_ready),
        .mem_burst_rd(mem_burst_rd),
        .mem_burst_wr(mem_burst_wr),
        .mem_addr(mem_addr),
        .mem_rd_manifold(mem_rd_manifold),
        .mem_wr_manifold(mem_wr_manifold),
        .mem_burst_done(mem_burst_done),
        .artery_wr_en(cortex_artery_wr_en),
        .artery_wr_data(cortex_artery_wr_data),
        .current_axis_ptr(current_axis_ptr),
        .current_axis_data(current_axis_data),
        .manifold_out(manifold_out),
        .bloom_complete(bloom_done),
        .ratio_cmp_res(ratio_cmp_res),
        .ratio_cmp_valid(ratio_cmp_valid),
        .scale_table_out(scale_table_out),
        .scale_overflow_out(scale_overflow_out),
        .is_janus_point(is_janus_point),
        .audio_mode(audio_mode),
        .gasket_sum_out(gasket_sum_out),
        .quadrance_out(quadrance_out),
        .cycle_wrap(cycle_wrap),
        .rplu_dissoc_out(rplu_dissoc_out),
        // Instruction interface (unused by default in top-level)
        .inst_valid(1'b0),
        .inst_word(64'd0)
    );

    // 5. Sentinel Satellites (4x SPU-4)
    wire [7:0] sentinel_whispers;
    wire [511:0] sentinel_telemetry;
    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : gen_sentinels
            spu4_top #(
                .MY_ID(i[2:0])
            ) u_sentinel (
                .clk(clk_fast), .rst_n(rst_n),
                .sentinel_mode(global_sentinel_mode),
                .piranha_pulse(clk_piranha),
                .bank_sel(rplu_mode),
                .rplu_cfg_wr_en(rplu_cfg_wr_en),
                .rplu_cfg_sel(rplu_cfg_sel),
                .rplu_cfg_material(rplu_cfg_material),
                .rplu_cfg_addr(rplu_cfg_addr),
                .rplu_cfg_data(rplu_cfg_data),
                .inst_data(24'h000000), // Static idle for now
                .pc(),
                .snap_alert(),
                .whisper_tx(),
                .state_out(),
                .debug_reg_r0(sentinel_telemetry[i*64 +: 64])
            );
        end
    endgenerate

    // 6. Artery Inhale → inhale_staging (Piranha domain — sole writer)
    //
    // Root cause of the old CDC race:
    //   int_mem had TWO always-block writers (clk_fast H_EXHALE + clk_piranha inhale),
    //   causing multi-driver synthesis errors and a simulation race where 24 MHz
    //   H_EXHALE bursts zeroed int_mem faster than 61.44 kHz inhale could fill it.
    //
    // Fix — three steps:
    //   1. Piranha domain writes chords into inhale_staging[0..12] (one reg per axis).
    //      Sets inhale_primed after the first complete 13-axis cycle.
    //   2. 2-FF CDC synchronizer promotes inhale_primed → fast domain.
    //   3. Fast domain (int_mem sole owner): on first inhale_primed_fast assertion,
    //      snapshots all 13 axes into int_mem in one clock.  Staging is guaranteed
    //      stable at this point (has been written ≥ 13 piranha periods = ≥ 211 µs
    //      before inhale_primed_fast can propagate to the fast domain).
    //      Thereafter H_EXHALE (mem_burst_wr) updates int_mem normally.

    // ------------------------------------------------------------------ //
    // 6. Artery Inhale (Flash, SD & Supervisor Hydration)                //
    // ------------------------------------------------------------------ //

    wire [63:0] sd_inhale_chord;
    wire        sd_inhale_wr_en;
    wire        sd_inhaler_done;

    wire [63:0] flash_inhale_chord;
    wire        flash_inhale_wr_en;
    wire        flash_inhaler_busy;
    wire        flash_inhaler_done;

    // Auto-load trigger: pulse start on reset release
    reg sd_auto_start_done;
    reg sd_start_trigger;
    reg flash_auto_start_done;
    reg flash_start_trigger;

    always @(posedge clk_piranha or negedge rst_n) begin
        if (!rst_n) begin
            sd_auto_start_done <= 1'b0;
            sd_start_trigger <= 1'b0;
            flash_auto_start_done <= 1'b0;
            flash_start_trigger <= 1'b0;
        end else begin
            sd_start_trigger <= 1'b0;
            flash_start_trigger <= 1'b0;

            // Phase 1: Inhale from Internal Flash (ROMs)
            if (!flash_auto_start_done) begin
                flash_start_trigger <= 1'b1;
                flash_auto_start_done <= 1'b1;
            end

            // Phase 2: Inhale from SD Card (Manifold) - Trigger after Flash is done
            if (flash_inhaler_done && !sd_auto_start_done) begin
                sd_start_trigger <= 1'b1;
                sd_auto_start_done <= 1'b1;
            end
        end
    end

    // Use the SD Inhaler module but redirected to Onboard Flash pins
    spu_sd_inhaler #(.CLK_DIV(8)) u_flash_inhaler (
        .clk            (clk_piranha),
        .rst_n          (rst_n),
        .start          (flash_start_trigger),
        .start_sector   (32'h2000),         // Start from 1MB Mark (Sector 2048) in Flash
        .num_chords     (16'd10),           // Load ROM set (Primes/coeffs)
        .busy           (flash_inhaler_busy),
        .done           (flash_inhaler_done),
        .chord_out      (flash_inhale_chord),
        .chord_valid    (flash_inhale_wr_en),
        .sd_cs          (pmod_cs_n),
        .sd_sck         (pmod_sclk),
        .sd_mosi        (pmod_mosi),
        .sd_miso        (pmod_miso)
    );

    spu_sd_inhaler #(.CLK_DIV(8)) u_sd_inhaler (
        .clk            (clk_piranha),
        .rst_n          (rst_n),
        .start          (sd_start_trigger),
        .start_sector   (32'h0),            // Autoload from Sector 0 on SD card
        .num_chords     (16'd13),           // Load default boot manifold (13 axes)
        .busy           (sd_inhaler_busy),
        .done           (sd_inhaler_done),
        .chord_out      (sd_inhale_chord),
        .chord_valid    (sd_inhale_wr_en),
        .sd_cs          (sd_cs),
        .sd_sck         (sd_sck),
        .sd_mosi        (sd_mosi),
        .sd_miso        (sd_miso)
    );

    // Multiplex the Artery pipeline: Flash -> SD -> Supervisor
    assign active_inhale_chord = flash_inhaler_busy ? flash_inhale_chord : (sd_inhaler_busy ? sd_inhale_chord : inhale_chord);
    assign active_inhale_wr_en = flash_inhaler_busy ? flash_inhale_wr_en : (sd_inhaler_busy ? sd_inhale_wr_en : (!inhale_empty && (inhale_axis_ptr < 4'd13)));
    
    reg [63:0] inhale_staging [0:12]; // piranha domain only
    // inhale_axis_ptr and inhale_primed declared at top

    always @(posedge clk_piranha or negedge rst_n) begin
        if (!rst_n) begin
            inhale_axis_ptr <= 4'h0;
            inhale_rd_en    <= 1'b0;
            inhale_primed   <= 1'b0;
        end else begin
            inhale_rd_en <= active_inhale_wr_en && !sd_inhaler_busy && !inhale_primed; // Only pull from Supervisor FIFO if SD is silent and hydration not done
            
            if (active_inhale_wr_en && !inhale_primed) begin
                inhale_staging[inhale_axis_ptr] <= active_inhale_chord;
                if (inhale_axis_ptr == 4'd12) begin
                    inhale_axis_ptr <= 4'h0;
                    inhale_primed   <= 1'b1; // Hydration complete
                end else
                    inhale_axis_ptr <= inhale_axis_ptr + 4'h1;
            end
        end
    end

    // 2-FF CDC synchronizer: inhale_primed (piranha) → clk_fast domain.
    reg inhale_primed_r1, inhale_primed_r2;
    always @(posedge clk_fast or negedge rst_n) begin
        if (!rst_n) {inhale_primed_r2, inhale_primed_r1} <= 2'b00;
        else        {inhale_primed_r2, inhale_primed_r1} <= {inhale_primed_r1, inhale_primed};
    end
    wire inhale_primed_fast = inhale_primed_r2;

    // int_mem: fast domain, single writer.
    // Sequencing:
    //   Phase A: snapshot not yet done — neither H_EXHALE nor snapshot updates int_mem.
    //   Phase B: inhale_primed_fast rises — ONE-TIME snapshot writes unit vectors.
    //            inhale_snap_done=1 after this cycle's NBAs.
    //   Phase C: wait for the core's next H_INHALE (mem_burst_rd=1) to READ the fresh
    //            int_mem.  When seen, set snap_inhale_done=1.
    //            Note: if snapshot fires in the same cycle as mem_burst_rd, the core
    //            reads OLD int_mem (zeros) — the H_INHALE that follows snapshot's NBA
    //            reads unit vectors (next cycle), so snap_inhale_done is safe.
    //   Phase D: snap_inhale_done=1 — H_EXHALE (mem_burst_wr) may update int_mem.
    //            First such H_EXHALE carries bloom-of-unit-vectors → is_janus_point.
    reg inhale_snap_done;
    reg snap_inhale_done;

    always @(posedge clk_fast or negedge rst_n) begin
        if (!rst_n) begin
            int_mem_burst_done <= 1'b0;
            int_mem          <= 832'h0;
            inhale_snap_done <= 1'b0;
            snap_inhale_done <= 1'b0;
        end else begin
            int_mem_burst_done <= !master_mode && (mem_burst_rd | mem_burst_wr);

            if (inhale_primed_fast && !inhale_snap_done) begin
                // Phase B: one-time snapshot; staging stable ≥ 211 µs at this point.
                int_mem[ 0*64 +: 64] <= inhale_staging[0];
                int_mem[ 1*64 +: 64] <= inhale_staging[1];
                int_mem[ 2*64 +: 64] <= inhale_staging[2];
                int_mem[ 3*64 +: 64] <= inhale_staging[3];
                int_mem[ 4*64 +: 64] <= inhale_staging[4];
                int_mem[ 5*64 +: 64] <= inhale_staging[5];
                int_mem[ 6*64 +: 64] <= inhale_staging[6];
                int_mem[ 7*64 +: 64] <= inhale_staging[7];
                int_mem[ 8*64 +: 64] <= inhale_staging[8];
                int_mem[ 9*64 +: 64] <= inhale_staging[9];
                int_mem[10*64 +: 64] <= inhale_staging[10];
                int_mem[11*64 +: 64] <= inhale_staging[11];
                int_mem[12*64 +: 64] <= inhale_staging[12];
                inhale_snap_done <= 1'b1;
            end else if (inhale_snap_done) begin
                // Phase C: watch for first H_INHALE that reads the fresh int_mem.
                // mem_burst_rd is high during the cycle the core samples mem_rd_manifold.
                // inhale_snap_done is checked in the ACTIVE region (pre-NBA), so if
                // snapshot fires on the same cycle as mem_burst_rd, snap_inhale_done
                // correctly waits for the NEXT mem_burst_rd (which reads unit vectors).
                if (!snap_inhale_done && mem_burst_rd)
                    snap_inhale_done <= 1'b1;
                // Phase D: normal H_EXHALE path — bloom results from unit vectors.
                if (snap_inhale_done && mem_burst_wr)
                    int_mem <= mem_wr_manifold;
            end
        end
    end

    assign manifold_state = manifold_out;

    // ------------------------------------------------------------------ //
    // 7. I2S Audio Output (Derived from Axis 0 & Axis 1)                //
    // ------------------------------------------------------------------ //
    // We take a 24-bit window from the 64-bit surds. 
    // Assuming Q32.32 format, bits [47:24] provide high-fidelity resonance.
    // audio_mode declared at top

    /*
    spu_i2s_out u_audio (
        .clk       (clk_fast),
        .rst_n     (rst_n),
        .mode      (audio_mode),
        .lfi       (laminar_index),
        .left_data (manifold_out[47:24]),   // Axis 0
        .right_data(manifold_out[111:88]),  // Axis 1
        .i2s_bclk  (i2s_bclk),
        .i2s_lrclk (i2s_lrclk),
        .i2s_dout  (i2s_dout)
    );
    */

    // Proprioception u_proprio module moved to section 8 (before bootrom)


    // ------------------------------------------------------------------ //
    // 9. SPI Slave Interface (Status & Artery)                          //
    // ------------------------------------------------------------------ //
    spu_spi_slave u_spi_slave (
        .clk             (clk_fast),
        .rst_n           (rst_n),
        .spi_cs_n        (spi_cs_n),
        .spi_sck         (spi_sck),
        .spi_mosi        (spi_mosi),
        .spi_miso        (spi_miso),
        .manifold_state  (manifold_out),
        .satellite_snaps (satellite_snaps[3:0]),
        .is_janus_point  (is_janus_point),
        .dissonance      (16'h0),           // unused
        .scale_table     (52'h0),           // unused
        .scale_overflow  (13'h0),           // unused
        .rplu_ratio_res  (ratio_cmp_res),
        .rplu_ratio_valid(ratio_cmp_valid),
        .fifo_full       (fifo_full),
        .laminar_index   (laminar_index),
        .turbulence      (turbulence_alert),
        .rplu_mode       (rplu_mode),
        .rplu_cfg_wr_en  (ext_piranha_cfg_wr_en),
        .rplu_cfg_sel    (ext_piranha_cfg_sel),
        .rplu_cfg_material (ext_piranha_cfg_material),
        .rplu_cfg_addr   (ext_piranha_cfg_addr),
        .rplu_cfg_data   (ext_piranha_cfg_data),
        .sentinel_telemetry (sentinel_telemetry)
    );

    // ------------------------------------------------------------------ //
    // 10. Industrial GATEWAY Peripheral                                 //
    // ------------------------------------------------------------------ //
    // Maps HUB75 output pins to SPU bus control for multi-axis motion
    spu_industrial_io #(
        .NUM_PWM(16),
        .NUM_BITBAND(56)
    ) u_industrial (
        .clk(clk_fast),
        .rst_n(rst_n),
        .bus_wr_en(ext_piranha_cfg_wr_en && ext_piranha_cfg_sel == 3'd4), // Channel 4 reserved for Indust.
        .bus_addr(ext_piranha_cfg_addr[7:0]),
        .bus_wr_data(ext_piranha_cfg_data[31:0]),
        .bus_rd_data(), // TODO: Connect to SPI status path
        .io_inputs(industrial_inputs),
        .io_outputs(industrial_io)
    );

endmodule
