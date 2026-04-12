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

    // Manifold Telemetry
    output wire [831:0] manifold_state,
    output wire [3:0]   satellite_snaps,
    output wire         is_janus_point
);

    // Reset alias (active-high) for legacy modules that expect active-high reset
    wire reset = ~rst_n;

    // 1. Artery FIFO Bridge (Asynchronous Breath)
    wire [63:0] inhale_chord;
    wire        inhale_empty;
    reg         inhale_rd_en;

    SPU_ARTERY_FIFO u_artery (
        .wr_clk(clk_ghost), .wr_rst_n(rst_n),
        .wr_en(wr_en), .wr_data(wr_data), .full(fifo_full),
        .rd_clk(clk_piranha), .rd_rst_n(rst_n),
        .rd_en(inhale_rd_en), .rd_data(inhale_chord), .empty(inhale_empty)
    );

    // Artery → RPLU decoder (optional runtime updates). Listens to inhaled chords
    // and produces a single-cycle write pulse with parameters on DATA chord.
    // Decoder outputs are captured to internal wires (dec_*). External fast-domain
    // SPI loader inputs (ext_*) are moved into piranha domain via CDC (see below),
    // then merged and exported as rplu_cfg_*.
    wire        dec_cfg_wr_en;
    wire [2:0]  dec_cfg_sel;
    wire        dec_cfg_material;
    wire [9:0]  dec_cfg_addr;
    wire [63:0] dec_cfg_data;

    rplu_artery_decoder u_rplu_dec (
        .clk(clk_piranha),
        .rst_n(rst_n),
        .inhale_valid(inhale_rd_en),
        .inhale_chord(inhale_chord),
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

    rplu_cfg_cdc u_cdc_fast2p (
        .clk_src       (clk_fast),
        .rst_n_src     (rst_n),
        .wr_src        (ext_rplu_cfg_wr_en_fast),
        .sel_src       (ext_rplu_cfg_sel_fast),
        .material_src  (ext_rplu_cfg_material_fast),
        .addr_src      (ext_rplu_cfg_addr_fast),
        .data_src      (ext_rplu_cfg_data_fast),
        .clk_dst       (clk_piranha),
        .rst_n_dst     (rst_n),
        .wr_dst        (ext_piranha_cfg_wr_en),
        .sel_dst       (ext_piranha_cfg_sel),
        .material_dst  (ext_piranha_cfg_material),
        .addr_dst      (ext_piranha_cfg_addr),
        .data_dst      (ext_piranha_cfg_data)
    );

    // Merge: external piranha-side writes take priority over decoder writes.
    assign rplu_cfg_wr_en       = ext_piranha_cfg_wr_en | dec_cfg_wr_en;
    assign rplu_cfg_sel         = ext_piranha_cfg_wr_en ? ext_piranha_cfg_sel : dec_cfg_sel;
    assign rplu_cfg_material    = ext_piranha_cfg_wr_en ? ext_piranha_cfg_material : dec_cfg_material;
    assign rplu_cfg_addr        = ext_piranha_cfg_wr_en ? ext_piranha_cfg_addr : dec_cfg_addr;
    assign rplu_cfg_data        = ext_piranha_cfg_wr_en ? ext_piranha_cfg_data : dec_cfg_data;

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

    rplu_cfg_cdc u_cdc_p2f (
        .clk_src       (clk_piranha),
        .rst_n_src     (rst_n),
        .wr_src        (dec_cfg_wr_en),
        .sel_src       (dec_cfg_sel),
        .material_src  (dec_cfg_material),
        .addr_src      (dec_cfg_addr),
        .data_src      (dec_cfg_data),
        .clk_dst       (clk_fast),
        .rst_n_dst     (rst_n),
        .wr_dst        (dec_fast_cfg_wr_en),
        .sel_dst       (dec_fast_cfg_sel),
        .material_dst  (dec_fast_cfg_material),
        .addr_dst      (dec_fast_cfg_addr),
        .data_dst      (dec_fast_cfg_data)
    );

    // 2. Phi-Gated Pulse Generation (from 24 MHz TDM clock)
    wire phi_8, phi_13, phi_21, phi_heart;
    spu_sierpinski_clk u_clk (
        .clk(clk_fast), .rst_n(rst_n),
        .phi_8(phi_8), .phi_13(phi_13), .phi_21(phi_21),
        .heartbeat(phi_heart)
    );

    // 3. Internal Manifold Memory Model (832-bit, fast domain)
    //    int_mem is driven solely by the always block in section 6 below.
    reg  [831:0] int_mem;
    wire         mem_ready;
    assign mem_ready = 1'b1;
    wire [831:0] mem_rd_manifold;
    assign mem_rd_manifold = int_mem;
    wire         mem_burst_rd;
    wire         mem_burst_wr;
    wire [23:0]  mem_addr;
    wire [831:0] mem_wr_manifold;
    reg          mem_burst_done;

    // 4. Sovereign Mother Unit (SPU-13 Cortex)
    wire [831:0] manifold_out;
    wire         bloom_done;

    spu13_core #(.DEVICE("SIM")) u_cortex (
        .clk(clk_fast),
        .rst_n(rst_n),
        .phi_8(phi_8), .phi_13(phi_13), .phi_21(phi_21),
        .mem_ready(mem_ready),
        .mem_burst_rd(mem_burst_rd),
        .mem_burst_wr(mem_burst_wr),
        .mem_addr(mem_addr),
        .mem_rd_manifold(mem_rd_manifold),
        .mem_wr_manifold(mem_wr_manifold),
        .mem_burst_done(mem_burst_done),
        .dec_fast_cfg_wr_en(dec_fast_cfg_wr_en),
        .dec_fast_cfg_sel(dec_fast_cfg_sel),
        .dec_fast_cfg_material(dec_fast_cfg_material),
        .dec_fast_cfg_addr(dec_fast_cfg_addr),
        .dec_fast_cfg_data(dec_fast_cfg_data),
        .manifold_out(manifold_out),
        .bloom_complete(bloom_done),
        .is_janus_point(is_janus_point)
    );

    // 5. Sentinel Satellites (4x SPU-4)
    wire [3:0] sentinel_whispers;
    genvar i;
    generate
        for (i = 0; i < 4; i = i + 1) begin : gen_sentinels
            spu4_top u_sentinel (
                .clk(clk_piranha), .rst_n(rst_n),
                .inst_data(24'h800000), // OP_SNAP
                .snap_alert(satellite_snaps[i]),
                .whisper_tx(sentinel_whispers[i]),
                .debug_reg_r0(),
                .rplu_cfg_wr_en(rplu_cfg_wr_en),
                .rplu_cfg_sel(rplu_cfg_sel),
                .rplu_cfg_material(rplu_cfg_material),
                .rplu_cfg_addr(rplu_cfg_addr),
                .rplu_cfg_data(rplu_cfg_data)
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

    reg [63:0] inhale_staging [0:12]; // piranha domain only
    reg [3:0]  inhale_axis_ptr;
    reg        inhale_primed;          // write-once: set after first full 13-axis cycle

    always @(posedge clk_piranha or negedge rst_n) begin
        if (!rst_n) begin
            inhale_axis_ptr <= 4'h0;
            inhale_rd_en    <= 1'b0;
            inhale_primed   <= 1'b0;
        end else begin
            inhale_rd_en <= !inhale_empty && (inhale_axis_ptr < 4'd13);
            if (inhale_rd_en) begin
                inhale_staging[inhale_axis_ptr] <= inhale_chord;
                if (inhale_axis_ptr == 4'd12) begin
                    inhale_axis_ptr <= 4'h0;
                    inhale_primed   <= 1'b1; // stays set forever
                end else
                    inhale_axis_ptr <= inhale_axis_ptr + 4'h1;
            end
        end
    end

    // 2-FF CDC synchronizer: inhale_primed (piranha) → clk_fast domain.
    // Write-once flag: no handshake needed; metastability window << 1 µs << 211 µs.
    reg inhale_primed_r1, inhale_primed_r2;
    always @(posedge clk_fast or negedge rst_n) begin
        if (!rst_n) {inhale_primed_r2, inhale_primed_r1} <= 2'b00;
        else        {inhale_primed_r2, inhale_primed_r1} <= {inhale_primed_r1, inhale_primed};
    end
    wire inhale_primed_fast;
    assign inhale_primed_fast = inhale_primed_r2;

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
            mem_burst_done   <= 1'b0;
            int_mem          <= 832'h0;
            inhale_snap_done <= 1'b0;
            snap_inhale_done <= 1'b0;
        end else begin
            mem_burst_done <= mem_burst_rd | mem_burst_wr;

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

endmodule
