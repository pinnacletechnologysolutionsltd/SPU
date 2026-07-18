// spu_a7_top.v — SPU-13 Artix-7 Unified Top-Level (v1.1)
//
// Copyright 2026 John Curley
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// Spin selection via SPIN parameter — no need to manually toggle ENABLE_*:
//
//   SPIN = "MULTIMEDIA"  — MATH + GPU + RPLU2 + I2S  (gaming, visualisation, audio)
//   SPIN = "INTELLIGENCE" — SOM + GATEKEEPER + RPLU2  (synthetic intelligence, clustering)
//   SPIN = "ROBOTICS"    — MATH + GATEKEEPER          (kinematics, avionics, simulation)
//   SPIN = "LUCAS"       — SPI-visible Lucas MAC sidecar proof
//   SPIN = "SU3"         — SPI-visible SU3 matrix sidecar proof
//   SPIN = "SU3SHARE"    — core + RPLU2 cfg + SU3 using top-level M31 multiplier
//   SPIN = "RPLUCFG"     — SPI-visible RPLU config telemetry proof
//   SPIN = "RPLU2CORE"   — SPI + core + RPLU2 config/QR bring-up
//   SPIN = "RPLU2"       — SPI + core + RPLU2 pipeline bring-up, shared Padé/inverter M31
//   SPIN = "RPLU2LIVE"   — SPI-visible coreless RPLU2 live evaluator proof
//   SPIN = "RPLU2PADE"   — SPI-visible coreless Padé evaluator proof
//   SPIN = "IROTC"       — SPI + core + IROTC typestate/engine proof
//   SPIN = "FULL"        — everything                  (development, 100T/200T)
//   SPIN = "SENSOR"      — MATH only, minimal          (medical wearables, iCESugar)
//   SPIN = "CUSTOM"      — use individual ENABLE_* parameters
//
// RP2350 Southbridge: SPI slave Mode 0, 2 MHz.
//   CMD 0xA0 → read manifold burst (32 bytes)
//   CMD 0xAC → read status / sticky RPLU ratio flags
//   CMD 0xAE → read last QR commit
//   CMD 0xAF → read sticky HEX result
//   CMD 0xA5 → write RPLU config chord pair
//   CMD 0xB1 → write + pulse 64-bit instruction word
//      LUCAS spin sidecar opcodes: D0=PSCALE, D1=PCHIRAL, D2=PMUL, D3=PINV
//      SU3 spin sidecar opcodes: E8=LOAD_A, E9=LOAD_B, EA=START, EB=READ

module spu_a7_top #(
    parameter DEVICE            = "A7_100T",
    parameter SPIN              = "FULL",
    parameter ENABLE_MATH       = 1,
    parameter ENABLE_SOM        = 1,
    parameter ENABLE_GATEKEEPER = 1,
    parameter ENABLE_GPU        = 1,
    // Legacy Morse/Padé RPLU. Kept for regression only; RPLU2 is the forward path.
    parameter ENABLE_LEGACY_RPLU = 0,
    parameter ENABLE_RPLU_V2     = 0,
    parameter ENABLE_RPLU_V2_PIPELINE = ENABLE_RPLU_V2,
    parameter ENABLE_RPLU_V2_EXTENSIONS = 0,
    parameter ENABLE_LUCAS_MAC  = 0,
    parameter ENABLE_SU3        = 0,
    parameter ENABLE_IROTC      = 0,
    parameter ENABLE_I2S        = 0,
    parameter ENABLE_TORUS      = 0,
    parameter ENABLE_LATTICE    = 0,
    parameter ENABLE_SDRAM      = 0,
    // Bring-up divider for openXC7 timing-closure spins.
    // 0 = raw board clock; N > 0 = clk_100mhz / 2**N. build_a7.sh
    // defaults this per spin (0 for the coreless sidecar spins, 6
    // otherwise) mirroring the _CORE ternary below — keep both lists
    // in sync. This parameter has no default-safe value here: build_a7.sh
    // always passes it explicitly via chparam.
    parameter A7_CLK_DIV_LOG2   = 0,
    // TEMPORARY bring-up aid, default OFF: when 1, uart_tx carries a
    // free-running diagnostic line (heartbeat/CS-seen/cmd-seen/boot_ready)
    // instead of real hex telemetry. Only meaningful while chasing the
    // boot_ready/nextpnr regression (see AGENTS.md) -- real spins must not
    // ship with this on. Explicit opt-in only (build_a7.sh A7_UART_DIAG=1),
    // no spin defaults this to 1.
    parameter A7_UART_DIAG      = 0
)(
    input  wire        clk_100mhz,
    input  wire        rst_n,
    input  wire        spi_cs_n, spi_sck, spi_mosi,
    output wire        spi_miso,
    output wire        uart_tx,
    output wire [3:0]  hdmi_d_p, hdmi_d_n,
    output wire        hdmi_clk_p, hdmi_clk_n,
    output wire        i2s_bclk, i2s_lrclk, i2s_dout,
    input  wire [7:0]  sensor_in,
    output wire [3:0]  led_out,
    output wire        fault_led
);

    // ── Spin → parameter resolution ────────────────────────────
    localparam _M = (SPIN == "CUSTOM") ? ENABLE_MATH :
        (SPIN == "INTELLIGENCE" || SPIN == "LUCAS" ||
         SPIN == "SU3" || SPIN == "SU3SHARE" || SPIN == "RPLUCFG" ||
         SPIN == "RPLU2CORE" || SPIN == "RPLU2" ||
         SPIN == "RPLU2LIVE" || SPIN == "RPLU2PADE" ||
         SPIN == "IROTC") ? 0 : 1;
    localparam _S = (SPIN == "CUSTOM") ? ENABLE_SOM :
        (SPIN == "INTELLIGENCE" || SPIN == "FULL" || SPIN == "SOM") ? 1 : 0;
    localparam _K = (SPIN == "CUSTOM") ? ENABLE_GATEKEEPER :
        (SPIN == "SENSOR" || SPIN == "LUCAS" ||
         SPIN == "SU3" || SPIN == "SU3SHARE" || SPIN == "RPLUCFG" ||
         SPIN == "RPLU2CORE" || SPIN == "RPLU2" ||
         SPIN == "RPLU2LIVE" || SPIN == "RPLU2PADE") ? 0 : 1;
    localparam _G = (SPIN == "CUSTOM") ? ENABLE_GPU :
        (SPIN == "MULTIMEDIA" || SPIN == "FULL") ? 1 : 0;
    localparam _R_LEGACY = (SPIN == "CUSTOM") ? ENABLE_LEGACY_RPLU : 0;
    localparam _R2 = (SPIN == "CUSTOM") ? ENABLE_RPLU_V2 :
        (SPIN == "MULTIMEDIA" || SPIN == "INTELLIGENCE" ||
         SPIN == "SU3SHARE" || SPIN == "RPLU2CORE" ||
         SPIN == "RPLU2" || SPIN == "FULL") ? 1 : 0;
    localparam _R2_PIPELINE = (SPIN == "CUSTOM") ? ENABLE_RPLU_V2_PIPELINE :
        (SPIN == "RPLU2CORE" || SPIN == "SU3SHARE") ? 0 : _R2;
    localparam _R2_EXT = (SPIN == "CUSTOM") ? ENABLE_RPLU_V2_EXTENSIONS : 0;
    localparam _L = (SPIN == "CUSTOM") ? ENABLE_LUCAS_MAC :
        (SPIN == "LUCAS") ? 1 : 0;
    localparam _U = (SPIN == "CUSTOM") ? ENABLE_SU3 :
        (SPIN == "SU3" || SPIN == "SU3SHARE") ? 1 : 0;
    localparam _IROTC = (SPIN == "CUSTOM") ? ENABLE_IROTC :
        (SPIN == "IROTC") ? 1 : 0;
    localparam _R2_LIVE = (SPIN == "RPLU2LIVE") ? 1 : 0;
    localparam _R2_PADE = (SPIN == "RPLU2PADE") ? 1 : 0;
    localparam _SHARED_SU3_MULT = (SPIN == "SU3SHARE") ? 1 : 0;
    localparam _SHARED_RPLU2_MULT = (SPIN == "RPLU2") ? 1 : 0;
    // Keep this spin list in sync with build_a7.sh's A7_CLK_DIV_LOG2
    // default case statement — coreless spins here must match the
    // 0-default spins there, or clk_fast comes up undivided on a core
    // spin (silent QR telemetry corruption, no synth/sim warning).
    localparam _CORE = (SPIN == "LUCAS" || SPIN == "SU3" ||
                        SPIN == "RPLUCFG" || SPIN == "RPLU2LIVE" ||
                        SPIN == "RPLU2PADE") ? 0 : 1;
    localparam _I = (SPIN == "CUSTOM") ? ENABLE_I2S :
        (SPIN == "MULTIMEDIA" || SPIN == "FULL") ? 1 : 0;
    localparam _T = (SPIN == "CUSTOM") ? ENABLE_TORUS :
        (SPIN == "FULL") ? 1 : 0;

    reg [7:0] clk_div = 8'd0;
    wire clk_fast_pre;
    wire clk_fast;

    always @(posedge clk_100mhz or negedge rst_n) begin
        if (!rst_n)
            clk_div <= 8'd0;
        else
            clk_div <= clk_div + 8'd1;
    end

    // Diagnostic heartbeat — free-running off raw clk_100mhz, independent
    // of clk_fast/A7_CLK_DIV_LOG2, rst_n, and the boot FSM. If led_out[3]
    // isn't visibly blinking (~0.75 Hz at 100 MHz), clk_100mhz isn't
    // toggling or rst_n is stuck low; nothing downstream can be trusted.
    reg [26:0] heartbeat_ctr = 27'd0;
    always @(posedge clk_100mhz)
        heartbeat_ctr <= heartbeat_ctr + 27'd1;

    // Diagnostic sticky CS latch — independent 2-flop synchronizer on the
    // raw spi_cs_n pin (not spu_spi_slave's internal one), set permanently
    // once a falling edge (CS asserted) is ever seen, cleared only by
    // rst_n. Isolates "does a CS transition from the RP2350 even reach and
    // get recognized by this pin" from everything inside spu_spi_slave.
    reg [1:0] diag_cs_sync = 2'b11;
    reg       diag_cs_ever_seen = 1'b0;
    always @(posedge clk_100mhz or negedge rst_n) begin
        if (!rst_n) begin
            diag_cs_sync <= 2'b11;
            diag_cs_ever_seen <= 1'b0;
        end else begin
            diag_cs_sync <= {diag_cs_sync[0], spi_cs_n};
            if (diag_cs_sync == 2'b10)
                diag_cs_ever_seen <= 1'b1;
        end
    end

    // Diagnostic independent command-byte shifter — a from-scratch replica
    // of spu_spi_slave's own sck/cs/mosi synchronizer and S_CMD bit-shift,
    // built entirely separately (own registers, own clk_fast domain) so it
    // cannot share a bug with the real slave. Sticky-latches once an 8-bit
    // frame equal to 8'hAC (CMD status read) is seen while CS was active.
    // If this lights up, the physical bit-level link is provably fine and
    // the bug is inside spu_spi_slave's own FSM; if it never lights up,
    // the bug is upstream of command decode (signal integrity/framing).
    //
    // diag2_last_cmd_byte is NOT sticky-to-AC like diag2_cmd_ac_seen above:
    // it always holds whatever the most recently completed 8-bit frame
    // actually was. diag2_cmd_ac_seen only proves 0xAC was decoded *at
    // least once, ever* -- it can't catch an intermittent misdecode on a
    // later transaction. Printing diag2_last_cmd_byte on every diag line
    // lets the operator confirm the command byte is 0xAC on the *specific*
    // status read that shows a wrong/stale boot_ready bit, distinguishing
    // "SPI link genuinely misdecodes on this remapped-pin hardware" from
    // "the read landed fine and something else is stale."
    reg [2:0] diag2_sck_r = 3'b0;
    reg [2:0] diag2_cs_r  = 3'b111;
    reg [1:0] diag2_mosi_r = 2'b0;
    reg [2:0] diag2_bit_cnt = 3'd0;
    reg [7:0] diag2_cmd_byte = 8'd0;
    reg       diag2_cmd_ac_seen = 1'b0;
    reg [7:0] diag2_last_cmd_byte = 8'd0;
    wire diag2_sck_rise = (diag2_sck_r[2:1] == 2'b01);
    wire diag2_cs_active = !diag2_cs_r[1];
    wire diag2_cs_fall = (diag2_cs_r[2:1] == 2'b10);
    always @(posedge clk_fast or negedge rst_n) begin
        if (!rst_n) begin
            diag2_sck_r <= 3'b0;
            diag2_cs_r  <= 3'b111;
            diag2_mosi_r <= 2'b0;
            diag2_bit_cnt <= 3'd0;
            diag2_cmd_byte <= 8'd0;
            diag2_cmd_ac_seen <= 1'b0;
            diag2_last_cmd_byte <= 8'd0;
        end else begin
            diag2_sck_r  <= {diag2_sck_r[1:0], spi_sck};
            diag2_cs_r   <= {diag2_cs_r[1:0], spi_cs_n};
            diag2_mosi_r <= {diag2_mosi_r[0], spi_mosi};
            if (diag2_cs_fall)
                diag2_bit_cnt <= 3'd0;
            if (diag2_cs_active && diag2_sck_rise) begin
                diag2_cmd_byte <= {diag2_cmd_byte[6:0], diag2_mosi_r[1]};
                if (diag2_bit_cnt == 3'd7) begin
                    diag2_bit_cnt <= 3'd0;
                    diag2_last_cmd_byte <= {diag2_cmd_byte[6:0], diag2_mosi_r[1]};
                    if ({diag2_cmd_byte[6:0], diag2_mosi_r[1]} == 8'hAC)
                        diag2_cmd_ac_seen <= 1'b1;
                end else begin
                    diag2_bit_cnt <= diag2_bit_cnt + 3'd1;
                end
            end
        end
    end

    generate
        if (A7_CLK_DIV_LOG2 == 0) begin : gen_raw_clk
            BUFG u_clk_fast_buf (
                .I(clk_100mhz),
                .O(clk_fast)
            );
        end else begin : gen_div_clk
            assign clk_fast_pre = clk_div[A7_CLK_DIV_LOG2-1];
            // Pin the fabric-derived clock to the BUFG site used by the
            // silicon-proven /64 RPLU2CORE image. Unconstrained IROTC routes
            // selected X0Y23/X0Y25; both configured but produced a dead
            // clk_fast domain on the Wukong board with the openXC7 packer.
            BUFG u_clk_fast_buf (
                .I(clk_fast_pre),
                .O(clk_fast)
            );
        end
    endgenerate
    wire spi_inst_valid, core_inst_valid, core_inst_done, inst_done;
    wire [63:0] spi_inst_word;
    wire hex_valid;
    wire [15:0] hex_q, hex_r;
    wire qr_commit_valid;
    wire [3:0] qr_commit_lane;
    wire [63:0] qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D;
    wire lucas_inst_claimed;
    wire lucas_busy;
    wire lucas_error;
    wire lucas_norm_violation;
    wire lucas_qr_commit_valid;
    wire [3:0] lucas_qr_commit_lane;
    wire [63:0] lucas_qr_commit_A;
    wire [63:0] lucas_qr_commit_B;
    wire [63:0] lucas_qr_commit_C;
    wire [63:0] lucas_qr_commit_D;
    wire su3_inst_claimed;
    wire su3_busy;
    wire su3_error;
    wire su3_qr_commit_valid;
    wire [3:0] su3_qr_commit_lane;
    wire [63:0] su3_qr_commit_A;
    wire [63:0] su3_qr_commit_B;
    wire [63:0] su3_qr_commit_C;
    wire [63:0] su3_qr_commit_D;
    wire [7:0] su3_debug_status;
    wire [2:0] su3_debug_state;
    wire rplu2_sidecar_inst_claimed;
    wire rplu2_sidecar_busy;
    wire rplu2_sidecar_error;
    wire rplu2_sidecar_qr_commit_valid;
    wire [3:0] rplu2_sidecar_qr_commit_lane;
    wire [63:0] rplu2_sidecar_qr_commit_A;
    wire [63:0] rplu2_sidecar_qr_commit_B;
    wire [63:0] rplu2_sidecar_qr_commit_C;
    wire [63:0] rplu2_sidecar_qr_commit_D;
    wire [7:0] rplu2_sidecar_debug_status;
    wire [2:0] rplu2_sidecar_debug_state;
    wire        su3_ext_mult_start;
    wire [31:0] su3_ext_mult_a0, su3_ext_mult_a1, su3_ext_mult_a2, su3_ext_mult_a3;
    wire [31:0] su3_ext_mult_b0, su3_ext_mult_b1, su3_ext_mult_b2, su3_ext_mult_b3;
    wire [31:0] su3_ext_mult_r0, su3_ext_mult_r1, su3_ext_mult_r2, su3_ext_mult_r3;
    wire        su3_ext_mult_done, su3_ext_mult_busy;
    wire        core_rplu_pade_mult_start;
    wire [31:0] core_rplu_pade_mult_a0, core_rplu_pade_mult_a1;
    wire [31:0] core_rplu_pade_mult_a2, core_rplu_pade_mult_a3;
    wire [31:0] core_rplu_pade_mult_b0, core_rplu_pade_mult_b1;
    wire [31:0] core_rplu_pade_mult_b2, core_rplu_pade_mult_b3;
    wire [31:0] core_rplu_pade_mult_r0, core_rplu_pade_mult_r1;
    wire [31:0] core_rplu_pade_mult_r2, core_rplu_pade_mult_r3;
    wire        core_rplu_pade_mult_done;
    wire        core_rplu_pade_mult_busy;
    wire        core_rplu_pade_mult_rns_error;
    wire [31:0] shared_mult_r0, shared_mult_r1, shared_mult_r2, shared_mult_r3;
    wire        shared_mult_done, shared_mult_busy, shared_mult_rns_error;
    wire        shared_su3_owns = (_SHARED_SU3_MULT != 0) && su3_busy;
    wire        shared_mult_start = shared_su3_owns ?
        su3_ext_mult_start : core_rplu_pade_mult_start;
    wire [31:0] shared_mult_a0 = shared_su3_owns ?
        su3_ext_mult_a0 : core_rplu_pade_mult_a0;
    wire [31:0] shared_mult_a1 = shared_su3_owns ?
        su3_ext_mult_a1 : core_rplu_pade_mult_a1;
    wire [31:0] shared_mult_a2 = shared_su3_owns ?
        su3_ext_mult_a2 : core_rplu_pade_mult_a2;
    wire [31:0] shared_mult_a3 = shared_su3_owns ?
        su3_ext_mult_a3 : core_rplu_pade_mult_a3;
    wire [31:0] shared_mult_b0 = shared_su3_owns ?
        su3_ext_mult_b0 : core_rplu_pade_mult_b0;
    wire [31:0] shared_mult_b1 = shared_su3_owns ?
        su3_ext_mult_b1 : core_rplu_pade_mult_b1;
    wire [31:0] shared_mult_b2 = shared_su3_owns ?
        su3_ext_mult_b2 : core_rplu_pade_mult_b2;
    wire [31:0] shared_mult_b3 = shared_su3_owns ?
        su3_ext_mult_b3 : core_rplu_pade_mult_b3;
    wire spi_qr_commit_valid;
    wire [3:0] spi_qr_commit_lane;
    wire [63:0] spi_qr_commit_A, spi_qr_commit_B, spi_qr_commit_C, spi_qr_commit_D;
    wire signed [2:0] ratio_cmp_res;
    wire ratio_cmp_valid;
    wire [831:0] manifold_state;
    wire [51:0] scale_table;
    wire [12:0] scale_overflow;
    wire is_janus_point;
    wire [31:0] quadrance_out;
    wire [7:0] laminar_flow_index;
    wire rplu_cfg_wr_en;
    wire [2:0] rplu_cfg_sel;
    wire [7:0] rplu_cfg_material;
    wire [9:0] rplu_cfg_addr;
    wire [63:0] rplu_cfg_data;
    wire axiomatic_fault;
    wire [1:0] fault_type;
    wire [15:0] fault_count;
    wire rns_error;
    wire ecc_single_err, ecc_double_err;
    wire [15:0] core_rotc_debug_status;
    wire core_boot_ready;
    wire [1:0] core_boot_state_dbg; // bring-up only: 0=RESET 1=HYDRATING 2=READY 3=FAULT
    reg [7:0] debug_last_spi_opcode = 8'h00;
    reg [7:0] debug_last_core_opcode = 8'h00;
    reg [7:0] debug_active_core_opcode = 8'h00;
    reg       debug_core_done_seen = 1'b0;
    reg       debug_core_commit_seen = 1'b0;
    reg       debug_rotc_commit_seen = 1'b0;
    reg       debug_sidecar_claim_seen = 1'b0;
    reg       debug_sidecar_commit_seen = 1'b0;
    reg       debug_sidecar_error_seen = 1'b0;

    assign core_inst_valid = spi_inst_valid && !lucas_inst_claimed &&
                             !su3_inst_claimed && !rplu2_sidecar_inst_claimed;
    assign inst_done = core_inst_done || lucas_qr_commit_valid ||
                       su3_qr_commit_valid || rplu2_sidecar_qr_commit_valid;
    assign spi_qr_commit_valid = su3_qr_commit_valid ? 1'b1 :
                                 lucas_qr_commit_valid ? 1'b1 :
                                 rplu2_sidecar_qr_commit_valid ? 1'b1 :
                                 qr_commit_valid;
    assign spi_qr_commit_lane = su3_qr_commit_valid ? su3_qr_commit_lane :
                                lucas_qr_commit_valid ? lucas_qr_commit_lane :
                                rplu2_sidecar_qr_commit_valid ? rplu2_sidecar_qr_commit_lane :
                                qr_commit_lane;
    assign spi_qr_commit_A = su3_qr_commit_valid ? su3_qr_commit_A :
                             lucas_qr_commit_valid ? lucas_qr_commit_A :
                             rplu2_sidecar_qr_commit_valid ? rplu2_sidecar_qr_commit_A :
                             qr_commit_A;
    assign spi_qr_commit_B = su3_qr_commit_valid ? su3_qr_commit_B :
                             lucas_qr_commit_valid ? lucas_qr_commit_B :
                             rplu2_sidecar_qr_commit_valid ? rplu2_sidecar_qr_commit_B :
                             qr_commit_B;
    assign spi_qr_commit_C = su3_qr_commit_valid ? su3_qr_commit_C :
                             lucas_qr_commit_valid ? lucas_qr_commit_C :
                             rplu2_sidecar_qr_commit_valid ? rplu2_sidecar_qr_commit_C :
                             qr_commit_C;
    assign spi_qr_commit_D = su3_qr_commit_valid ? su3_qr_commit_D :
                             lucas_qr_commit_valid ? lucas_qr_commit_D :
                             rplu2_sidecar_qr_commit_valid ? rplu2_sidecar_qr_commit_D :
                             qr_commit_D;

    assign su3_ext_mult_r0 = shared_mult_r0;
    assign su3_ext_mult_r1 = shared_mult_r1;
    assign su3_ext_mult_r2 = shared_mult_r2;
    assign su3_ext_mult_r3 = shared_mult_r3;
    assign su3_ext_mult_done = shared_su3_owns ? shared_mult_done : 1'b0;
    assign su3_ext_mult_busy = shared_su3_owns ? shared_mult_busy : 1'b1;

    assign core_rplu_pade_mult_r0 = shared_mult_r0;
    assign core_rplu_pade_mult_r1 = shared_mult_r1;
    assign core_rplu_pade_mult_r2 = shared_mult_r2;
    assign core_rplu_pade_mult_r3 = shared_mult_r3;
    assign core_rplu_pade_mult_done = shared_su3_owns ? 1'b0 : shared_mult_done;
    assign core_rplu_pade_mult_busy = shared_su3_owns ? 1'b1 : shared_mult_busy;
    assign core_rplu_pade_mult_rns_error = shared_su3_owns ? 1'b0 : shared_mult_rns_error;

    // Bring-up breadcrumb exposed through CMD 0xAC:
    //   status[0] = ROTC debug flags
    //   status[1] = {rotor_state[3:0], rotc_angle[3:0]}
    // Flag bits: [0]=accepted, [1]=active consumed, [2]=start emitted,
    //            [3]=rotor done seen, [4]=writeback, [5]=commit, [6]=busy.
    always @(posedge clk_fast or negedge rst_n) begin
        if (!rst_n) begin
            debug_last_spi_opcode <= 8'h00;
            debug_last_core_opcode <= 8'h00;
            debug_active_core_opcode <= 8'h00;
            debug_core_done_seen <= 1'b0;
            debug_core_commit_seen <= 1'b0;
            debug_rotc_commit_seen <= 1'b0;
            debug_sidecar_claim_seen <= 1'b0;
            debug_sidecar_commit_seen <= 1'b0;
            debug_sidecar_error_seen <= 1'b0;
        end else begin
            if (spi_inst_valid) begin
                debug_last_spi_opcode <= spi_inst_word[63:56];
                debug_last_core_opcode <= 8'h00;
                debug_core_done_seen <= 1'b0;
                debug_core_commit_seen <= 1'b0;
                debug_rotc_commit_seen <= 1'b0;
                debug_sidecar_claim_seen <= 1'b0;
                debug_sidecar_commit_seen <= 1'b0;
                debug_sidecar_error_seen <= 1'b0;
            end
            if (core_inst_valid) begin
                debug_last_core_opcode <= spi_inst_word[63:56];
                debug_active_core_opcode <= spi_inst_word[63:56];
            end
            if (lucas_inst_claimed || su3_inst_claimed || rplu2_sidecar_inst_claimed)
                debug_sidecar_claim_seen <= 1'b1;
            if (lucas_qr_commit_valid || su3_qr_commit_valid ||
                rplu2_sidecar_qr_commit_valid)
                debug_sidecar_commit_seen <= 1'b1;
            if (lucas_error || lucas_norm_violation || su3_error ||
                rplu2_sidecar_error)
                debug_sidecar_error_seen <= 1'b1;
            if (core_inst_done)
                debug_core_done_seen <= 1'b1;
            if (qr_commit_valid) begin
                debug_core_commit_seen <= 1'b1;
                if (debug_active_core_opcode == 8'h1C)
                    debug_rotc_commit_seen <= 1'b1;
            end
        end
    end

    // ── RPLU Config Telemetry ─────────────────────────────────
    // Mirrors the proven Tang southbridge SPUC frame so the RP2350 can
    // verify CRC-gated CMD 0xA5 writes on Wukong J11.
    reg  [15:0] rplu_cfg_count = 16'd0;
    reg  [31:0] rplu_cfg_checksum = 32'd0;
    reg  [31:0] rplu2_cfg_sum_checksum = 32'd0;
    reg  [2:0]  rplu_cfg_sel_last = 3'd0;
    reg  [7:0]  rplu_cfg_material_last = 8'd0;
    reg  [9:0]  rplu_cfg_addr_last = 10'd0;
    reg  [63:0] rplu_cfg_data_last = 64'd0;
    reg  [31:0] rplu2_num0_c0 = 32'd1;
    reg  [31:0] rplu2_num0_c1 = 32'd0;
    reg  [31:0] rplu2_num0_c2 = 32'd0;
    reg  [31:0] rplu2_num0_c3 = 32'd0;
    reg  [31:0] rplu2_den0_c0 = 32'd1;
    reg  [31:0] rplu2_den0_c1 = 32'd0;
    reg  [31:0] rplu2_den0_c2 = 32'd0;
    reg  [31:0] rplu2_den0_c3 = 32'd0;
    reg  [31:0] rplu2_row1_c0 = 32'd0;
    reg  [31:0] rplu2_row1_c1 = 32'd0;
    reg  [31:0] rplu2_row1_c2 = 32'd0;
    reg  [31:0] rplu2_row1_c3 = 32'd0;
    reg  [31:0] rplu2_quadray_kappa = 32'd0;

    localparam [15:0] RPLU2_CONSUME_RECORDS = 16'd149;
    localparam [31:0] RPLU2_EXPECTED_SUM    = 32'h0AA480E7;
    localparam [31:0] RPLU2_CONSUME_PASS    = 32'hC02E0001;
    localparam [31:0] RPLU2_CONSUME_FAIL    = 32'hC02E0000;
    localparam [2:0]  RPLU2_CFG_PADE_NUM    = 3'd1;
    localparam [2:0]  RPLU2_CFG_PADE_DEN    = 3'd2;
    localparam [2:0]  RPLU2_CFG_BTU_ROW     = 3'd3;
    localparam [2:0]  RPLU2_CFG_KAPPA       = 3'd6;

    function [31:0] cfg_checksum_next;
        input [31:0] prev;
        input [2:0]  sel;
        input [7:0]  material;
        input [9:0]  addr;
        input [63:0] data;
        reg   [31:0] mixed_header;
        begin
            mixed_header = {8'hA5, 5'd0, sel, material, 6'd0, addr};
            cfg_checksum_next = {prev[30:0], prev[31]} ^
                                mixed_header ^
                                data[63:32] ^
                                data[31:0];
        end
    endfunction

    function [31:0] cfg_sum_checksum_next;
        input [31:0] prev;
        input [2:0]  sel;
        input [7:0]  material;
        input [9:0]  addr;
        input [63:0] data;
        reg   [63:0] header_word;
        begin
            header_word = {8'hA5, 5'd0, sel, material[3:0], addr, 34'd0};
            cfg_sum_checksum_next = prev +
                                    header_word[63:32] +
                                    header_word[31:0] +
                                    data[63:32] +
                                    data[31:0];
        end
    endfunction

    always @(posedge clk_fast or negedge rst_n) begin
        if (!rst_n) begin
            rplu_cfg_count <= 16'd0;
            rplu_cfg_checksum <= 32'd0;
            rplu2_cfg_sum_checksum <= 32'd0;
            rplu_cfg_sel_last <= 3'd0;
            rplu_cfg_material_last <= 8'd0;
            rplu_cfg_addr_last <= 10'd0;
            rplu_cfg_data_last <= 64'd0;
            rplu2_num0_c0 <= 32'd1;
            rplu2_num0_c1 <= 32'd0;
            rplu2_num0_c2 <= 32'd0;
            rplu2_num0_c3 <= 32'd0;
            rplu2_den0_c0 <= 32'd1;
            rplu2_den0_c1 <= 32'd0;
            rplu2_den0_c2 <= 32'd0;
            rplu2_den0_c3 <= 32'd0;
            rplu2_row1_c0 <= 32'd0;
            rplu2_row1_c1 <= 32'd0;
            rplu2_row1_c2 <= 32'd0;
            rplu2_row1_c3 <= 32'd0;
            rplu2_quadray_kappa <= 32'd0;
        end else if (rplu_cfg_wr_en) begin
            rplu_cfg_count <= rplu_cfg_count + 16'd1;
            rplu_cfg_checksum <= cfg_checksum_next(rplu_cfg_checksum,
                                                   rplu_cfg_sel,
                                                   rplu_cfg_material,
                                                   rplu_cfg_addr,
                                                   rplu_cfg_data);
            rplu2_cfg_sum_checksum <= cfg_sum_checksum_next(rplu2_cfg_sum_checksum,
                                                            rplu_cfg_sel,
                                                            rplu_cfg_material,
                                                            rplu_cfg_addr,
                                                            rplu_cfg_data);
            rplu_cfg_sel_last <= rplu_cfg_sel;
            rplu_cfg_material_last <= rplu_cfg_material;
            rplu_cfg_addr_last <= rplu_cfg_addr;
            rplu_cfg_data_last <= rplu_cfg_data;

            if (rplu_cfg_sel == RPLU2_CFG_PADE_NUM &&
                rplu_cfg_addr[2:0] == 3'd0) begin
                if (rplu_cfg_addr[3]) begin
                    rplu2_num0_c2 <= rplu_cfg_data[31:0];
                    rplu2_num0_c3 <= rplu_cfg_data[63:32];
                end else begin
                    rplu2_num0_c0 <= rplu_cfg_data[31:0];
                    rplu2_num0_c1 <= rplu_cfg_data[63:32];
                end
            end

            if (rplu_cfg_sel == RPLU2_CFG_PADE_DEN &&
                rplu_cfg_addr[2:0] == 3'd0) begin
                if (rplu_cfg_addr[3]) begin
                    rplu2_den0_c2 <= rplu_cfg_data[31:0];
                    rplu2_den0_c3 <= rplu_cfg_data[63:32];
                end else begin
                    rplu2_den0_c0 <= rplu_cfg_data[31:0];
                    rplu2_den0_c1 <= rplu_cfg_data[63:32];
                end
            end

            if (rplu_cfg_sel == RPLU2_CFG_BTU_ROW &&
                rplu_cfg_addr[5:0] == 6'd1) begin
                if (rplu_cfg_addr[6]) begin
                    rplu2_row1_c2 <= rplu_cfg_data[31:0];
                    rplu2_row1_c3 <= rplu_cfg_data[63:32];
                end else begin
                    rplu2_row1_c0 <= rplu_cfg_data[31:0];
                    rplu2_row1_c1 <= rplu_cfg_data[63:32];
                end
            end

            if (rplu_cfg_sel == RPLU2_CFG_KAPPA) begin
                rplu2_quadray_kappa <= rplu_cfg_data[31:0];
            end
        end
    end

    wire rplu2_row_kappa_match =
        (rplu2_row1_c0 == 32'd1) &&
        (rplu2_row1_c1 == 32'd0) &&
        (rplu2_row1_c2 == 32'd0) &&
        (rplu2_row1_c3 == 32'd0) &&
        (rplu2_quadray_kappa == 32'd3);

    wire [31:0] rplu2_quadray_delta =
        rplu2_row_kappa_match ? 32'd0 : 32'h7FFFFFFE;

    wire rplu2_consume_pass =
        (rplu_cfg_count == RPLU2_CONSUME_RECORDS) &&
        (rplu2_cfg_sum_checksum == RPLU2_EXPECTED_SUM) &&
        (rplu2_num0_c0 == 32'd2) &&
        (rplu2_num0_c1 == 32'd0) &&
        (rplu2_num0_c2 == 32'd0) &&
        (rplu2_num0_c3 == 32'd0) &&
        (rplu2_den0_c0 == 32'd1) &&
        (rplu2_den0_c1 == 32'd0) &&
        (rplu2_den0_c2 == 32'd0) &&
        (rplu2_den0_c3 == 32'd0) &&
        rplu2_row_kappa_match;

    wire [31:0] rplu2_consume_status =
        (rplu_cfg_count == RPLU2_CONSUME_RECORDS) ?
            (rplu2_consume_pass ? RPLU2_CONSUME_PASS : RPLU2_CONSUME_FAIL) :
            32'd0;

    wire [511:0] southbridge_telemetry = {
        32'h53505543,
        rplu_cfg_count,
        {5'd0, rplu_cfg_sel_last},
        rplu_cfg_material_last,
        {6'd0, rplu_cfg_addr_last},
        rplu_cfg_data_last[63:16],
        rplu_cfg_data_last[15:0],
        rplu_cfg_checksum,
        rplu2_cfg_sum_checksum,
        rplu2_consume_status,
        rplu2_num0_c0,
        rplu2_quadray_delta,
        rplu2_row1_c0,
        rplu2_quadray_kappa,
        144'd0
    };

    // ── Shared SU3/RPLU Padé M31 multiplier ───────────────────────
    generate
        if (_SHARED_SU3_MULT) begin : gen_shared_su3_mult
            spu13_m31_multiplier u_shared_m31_mult (
                .clk(clk_fast),
                .rst_n(rst_n),
                .start(shared_mult_start),
                .a0(shared_mult_a0),
                .a1(shared_mult_a1),
                .a2(shared_mult_a2),
                .a3(shared_mult_a3),
                .b0(shared_mult_b0),
                .b1(shared_mult_b1),
                .b2(shared_mult_b2),
                .b3(shared_mult_b3),
                .r0(shared_mult_r0),
                .r1(shared_mult_r1),
                .r2(shared_mult_r2),
                .r3(shared_mult_r3),
                .done(shared_mult_done),
                .busy(shared_mult_busy),
                .rns_error(shared_mult_rns_error)
            );
        end else begin : gen_no_shared_su3_mult
            assign shared_mult_r0 = 32'd0;
            assign shared_mult_r1 = 32'd0;
            assign shared_mult_r2 = 32'd0;
            assign shared_mult_r3 = 32'd0;
            assign shared_mult_done = 1'b0;
            assign shared_mult_busy = 1'b0;
            assign shared_mult_rns_error = 1'b0;
        end
    endgenerate

    // ── Sierpiński Floorplanner (Fibonacci 8/13/21 timing) ──
    wire phi_8, phi_13, phi_21, phi_heart;
    spu_sierpinski_clk u_floorplan (
        .clk(clk_fast), .rst_n(rst_n),
        .phi_8(phi_8), .phi_13(phi_13), .phi_21(phi_21),
        .heartbeat(phi_heart)
    );

    // ── SPU-13 Core ──────────────────────────────────────────
    // Sidecar proof spins do not need the core shell; dropping it keeps the
    // first Artix-7 bring-up route focused on the SPI adapter under test.
    generate
        if (_CORE) begin : gen_core
            spu13_core #(
                .DEVICE(DEVICE),
                .ENABLE_RPLU(_R_LEGACY),
                .ENABLE_LATTICE(ENABLE_LATTICE),
                .ENABLE_MATH(_M),
                .ENABLE_SEQUENCER(0),
                .ENABLE_CORE_SOM(_S),
                .ENABLE_CORE_RPLU_V2(_R2),
                .ENABLE_CORE_RPLU_V2_PIPELINE(_R2_PIPELINE),
                .ENABLE_CORE_RPLU_V2_EXTENSIONS(_R2_EXT),
                .ENABLE_IROTC(_IROTC),
                .EXTERNAL_RPLU_PADE_MULT(_SHARED_SU3_MULT),
                .SHARE_RPLU_PADE_INV_MULT(_SHARED_RPLU2_MULT),
                .ENABLE_TORUS(_T)
            ) u_core (
                .clk(clk_fast), .rst_n(rst_n),
                .phi_8(phi_8), .phi_13(phi_13), .phi_21(phi_21),
                .dec_fast_cfg_wr_en(rplu_cfg_wr_en),
                .dec_fast_cfg_sel(rplu_cfg_sel),
                .dec_fast_cfg_material(rplu_cfg_material),
                .dec_fast_cfg_addr(rplu_cfg_addr),
                .dec_fast_cfg_data(rplu_cfg_data),
                .phinary_cfg({12'd0, (_K ? 2'b00 : 2'b11)}),
                .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),
                .boot_done(1'b1),
                .pell_data(32'd0), .pell_addr(3'd0), .pell_we(1'b0),
                .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
                .mem_ready(1'b1), .mem_burst_rd(), .mem_burst_wr(),
                .mem_addr(), .mem_rd_manifold(832'd0), .mem_wr_manifold(),
                .mem_burst_done(1'b0),
                .artery_wr_en(), .artery_wr_data(),
                .current_axis_ptr(), .current_axis_data(),
                .qr_commit_valid(qr_commit_valid),
                .qr_commit_lane(qr_commit_lane),
                .qr_commit_A(qr_commit_A),
                .qr_commit_B(qr_commit_B),
                .qr_commit_C(qr_commit_C),
                .qr_commit_D(qr_commit_D),
                .inst_valid(core_inst_valid), .inst_word(spi_inst_word), .inst_done(core_inst_done),
                .ratio_cmp_res(ratio_cmp_res), .ratio_cmp_valid(ratio_cmp_valid),
                .manifold_out(manifold_state), .bloom_complete(),
                .scale_table_out(scale_table),
                .scale_overflow_out(scale_overflow),
                .is_janus_point(is_janus_point),
                .audio_mode(), .gasket_sum_out(), .quadrance_out(quadrance_out), .cycle_wrap(),
                .rplu_dissoc_out(), .rplu_dissoc_mask_out(), .rplu_addr_out(),
                .i2s_bclk(i2s_bclk), .i2s_lrclk(i2s_lrclk), .i2s_dout(i2s_dout),
                .laminar_flow_index_out(laminar_flow_index), .thermal_pressure_out(),
                .hex_valid(hex_valid), .hex_q(hex_q), .hex_r(hex_r),
                .audio_p_out(), .audio_q_out(),
                .axiomatic_fault(axiomatic_fault), .fault_type(fault_type),
                .fault_count(fault_count),
                .rns_error(rns_error),
                .ecc_single_err(ecc_single_err),
                .ecc_double_err(ecc_double_err),
                .rotc_debug_status(core_rotc_debug_status),
                .boot_ready(core_boot_ready),
                .boot_state_dbg(core_boot_state_dbg),
                .rplu_pade_mult_start(core_rplu_pade_mult_start),
                .rplu_pade_mult_a0(core_rplu_pade_mult_a0),
                .rplu_pade_mult_a1(core_rplu_pade_mult_a1),
                .rplu_pade_mult_a2(core_rplu_pade_mult_a2),
                .rplu_pade_mult_a3(core_rplu_pade_mult_a3),
                .rplu_pade_mult_b0(core_rplu_pade_mult_b0),
                .rplu_pade_mult_b1(core_rplu_pade_mult_b1),
                .rplu_pade_mult_b2(core_rplu_pade_mult_b2),
                .rplu_pade_mult_b3(core_rplu_pade_mult_b3),
                .rplu_pade_mult_r0(core_rplu_pade_mult_r0),
                .rplu_pade_mult_r1(core_rplu_pade_mult_r1),
                .rplu_pade_mult_r2(core_rplu_pade_mult_r2),
                .rplu_pade_mult_r3(core_rplu_pade_mult_r3),
                .rplu_pade_mult_done(core_rplu_pade_mult_done),
                .rplu_pade_mult_busy(core_rplu_pade_mult_busy),
                .rplu_pade_mult_rns_error(core_rplu_pade_mult_rns_error)
            );
        end else begin : gen_no_core
            assign qr_commit_valid = 1'b0;
            assign qr_commit_lane = 4'd0;
            assign qr_commit_A = 64'd0;
            assign qr_commit_B = 64'd0;
            assign qr_commit_C = 64'd0;
            assign qr_commit_D = 64'd0;
            assign core_inst_done = 1'b0;
            assign ratio_cmp_res = 3'sd0;
            assign ratio_cmp_valid = 1'b0;
            assign manifold_state = 832'd0;
            assign scale_table = 52'd0;
            assign scale_overflow = 13'd0;
            assign is_janus_point = 1'b0;
            assign quadrance_out = 32'd0;
            assign laminar_flow_index = 8'd0;
            assign hex_valid = 1'b0;
            assign hex_q = 16'd0;
            assign hex_r = 16'd0;
            assign axiomatic_fault = 1'b0;
            assign fault_type = 2'd0;
            assign fault_count = 16'd0;
            assign rns_error = 1'b0;
            assign ecc_single_err = 1'b0;
            assign ecc_double_err = 1'b0;
            assign core_rotc_debug_status = 16'd0;
            assign core_rplu_pade_mult_start = 1'b0;
            assign core_rplu_pade_mult_a0 = 32'd0;
            assign core_rplu_pade_mult_a1 = 32'd0;
            assign core_rplu_pade_mult_a2 = 32'd0;
            assign core_rplu_pade_mult_a3 = 32'd0;
            assign core_rplu_pade_mult_b0 = 32'd0;
            assign core_rplu_pade_mult_b1 = 32'd0;
            assign core_rplu_pade_mult_b2 = 32'd0;
            assign core_rplu_pade_mult_b3 = 32'd0;
            assign i2s_bclk = 1'b0;
            assign i2s_lrclk = 1'b0;
            assign i2s_dout = 1'b0;
        end
    endgenerate

    // ── Lucas/Phinary Sidecar ───────────────────────────────────
    generate
        if (_L) begin : gen_lucas_sidecar
            spu13_lucas_sidecar u_lucas_sidecar (
                .clk(clk_fast),
                .rst_n(rst_n),
                .inst_valid(spi_inst_valid),
                .inst_word(spi_inst_word),
                .inst_claimed(lucas_inst_claimed),
                .busy(lucas_busy),
                .error(lucas_error),
                .qr_commit_valid(lucas_qr_commit_valid),
                .qr_commit_lane(lucas_qr_commit_lane),
                .qr_commit_A(lucas_qr_commit_A),
                .qr_commit_B(lucas_qr_commit_B),
                .qr_commit_C(lucas_qr_commit_C),
                .qr_commit_D(lucas_qr_commit_D),
                .norm_violation(lucas_norm_violation)
            );
        end else begin : gen_no_lucas_sidecar
            assign lucas_inst_claimed = 1'b0;
            assign lucas_busy = 1'b0;
            assign lucas_error = 1'b0;
            assign lucas_norm_violation = 1'b0;
            assign lucas_qr_commit_valid = 1'b0;
            assign lucas_qr_commit_lane = 4'd0;
            assign lucas_qr_commit_A = 64'd0;
            assign lucas_qr_commit_B = 64'd0;
            assign lucas_qr_commit_C = 64'd0;
            assign lucas_qr_commit_D = 64'd0;
        end
    endgenerate

    // ── SU3 Matrix Sidecar ─────────────────────────────────────
    generate
        if (_U) begin : gen_su3_sidecar
            spu13_su3_sidecar #(
                .EXTERNAL_MULT(_SHARED_SU3_MULT)
            ) u_su3_sidecar (
                .clk(clk_fast),
                .rst_n(rst_n),
                .inst_valid(spi_inst_valid),
                .inst_word(spi_inst_word),
                .inst_claimed(su3_inst_claimed),
                .busy(su3_busy),
                .error(su3_error),
                .qr_commit_valid(su3_qr_commit_valid),
                .qr_commit_lane(su3_qr_commit_lane),
                .qr_commit_A(su3_qr_commit_A),
                .qr_commit_B(su3_qr_commit_B),
                .qr_commit_C(su3_qr_commit_C),
                .qr_commit_D(su3_qr_commit_D),
                .debug_status(su3_debug_status),
                .debug_state(su3_debug_state),
                .shared_mult_start(su3_ext_mult_start),
                .shared_mult_a0(su3_ext_mult_a0),
                .shared_mult_a1(su3_ext_mult_a1),
                .shared_mult_a2(su3_ext_mult_a2),
                .shared_mult_a3(su3_ext_mult_a3),
                .shared_mult_b0(su3_ext_mult_b0),
                .shared_mult_b1(su3_ext_mult_b1),
                .shared_mult_b2(su3_ext_mult_b2),
                .shared_mult_b3(su3_ext_mult_b3),
                .shared_mult_r0(su3_ext_mult_r0),
                .shared_mult_r1(su3_ext_mult_r1),
                .shared_mult_r2(su3_ext_mult_r2),
                .shared_mult_r3(su3_ext_mult_r3),
                .shared_mult_done(su3_ext_mult_done),
                .shared_mult_busy(su3_ext_mult_busy)
            );
        end else begin : gen_no_su3_sidecar
            assign su3_inst_claimed = 1'b0;
            assign su3_busy = 1'b0;
            assign su3_error = 1'b0;
            assign su3_qr_commit_valid = 1'b0;
            assign su3_qr_commit_lane = 4'd0;
            assign su3_qr_commit_A = 64'd0;
            assign su3_qr_commit_B = 64'd0;
            assign su3_qr_commit_C = 64'd0;
            assign su3_qr_commit_D = 64'd0;
            assign su3_debug_status = 8'd0;
            assign su3_debug_state = 3'd0;
            assign su3_ext_mult_start = 1'b0;
            assign su3_ext_mult_a0 = 32'd0;
            assign su3_ext_mult_a1 = 32'd0;
            assign su3_ext_mult_a2 = 32'd0;
            assign su3_ext_mult_a3 = 32'd0;
            assign su3_ext_mult_b0 = 32'd0;
            assign su3_ext_mult_b1 = 32'd0;
            assign su3_ext_mult_b2 = 32'd0;
            assign su3_ext_mult_b3 = 32'd0;
        end
    endgenerate

    // ── RPLU2 Live Evaluator Sidecar ─────────────────────────────
    generate
        if (_R2_LIVE) begin : gen_rplu2_sidecar
            spu13_rplu2_sidecar u_rplu2_sidecar (
                .clk(clk_fast),
                .rst_n(rst_n),
                .inst_valid(spi_inst_valid),
                .inst_word(spi_inst_word),
                .inst_claimed(rplu2_sidecar_inst_claimed),
                .busy(rplu2_sidecar_busy),
                .error(rplu2_sidecar_error),
                .cfg_wr_en(rplu_cfg_wr_en),
                .cfg_sel(rplu_cfg_sel),
                .cfg_addr(rplu_cfg_addr),
                .cfg_data(rplu_cfg_data),
                .qr_commit_valid(rplu2_sidecar_qr_commit_valid),
                .qr_commit_lane(rplu2_sidecar_qr_commit_lane),
                .qr_commit_A(rplu2_sidecar_qr_commit_A),
                .qr_commit_B(rplu2_sidecar_qr_commit_B),
                .qr_commit_C(rplu2_sidecar_qr_commit_C),
                .qr_commit_D(rplu2_sidecar_qr_commit_D),
                .debug_status(rplu2_sidecar_debug_status),
                .debug_state(rplu2_sidecar_debug_state)
            );
        end else begin : gen_rplu2_pade_or_none
            if (_R2_PADE) begin : gen_rplu2_pade_sidecar
                spu13_rplu2_pade_sidecar u_rplu2_pade_sidecar (
                    .clk(clk_fast),
                    .rst_n(rst_n),
                    .inst_valid(spi_inst_valid),
                    .inst_word(spi_inst_word),
                    .inst_claimed(rplu2_sidecar_inst_claimed),
                    .busy(rplu2_sidecar_busy),
                    .error(rplu2_sidecar_error),
                    .cfg_wr_en(rplu_cfg_wr_en),
                    .cfg_sel(rplu_cfg_sel),
                    .cfg_addr(rplu_cfg_addr),
                    .cfg_data(rplu_cfg_data),
                    .qr_commit_valid(rplu2_sidecar_qr_commit_valid),
                    .qr_commit_lane(rplu2_sidecar_qr_commit_lane),
                    .qr_commit_A(rplu2_sidecar_qr_commit_A),
                    .qr_commit_B(rplu2_sidecar_qr_commit_B),
                    .qr_commit_C(rplu2_sidecar_qr_commit_C),
                    .qr_commit_D(rplu2_sidecar_qr_commit_D),
                    .debug_status(rplu2_sidecar_debug_status),
                    .debug_state(rplu2_sidecar_debug_state)
                );
            end else begin : gen_no_rplu2_sidecar
                assign rplu2_sidecar_inst_claimed = 1'b0;
                assign rplu2_sidecar_busy = 1'b0;
                assign rplu2_sidecar_error = 1'b0;
                assign rplu2_sidecar_qr_commit_valid = 1'b0;
                assign rplu2_sidecar_qr_commit_lane = 4'd0;
                assign rplu2_sidecar_qr_commit_A = 64'd0;
                assign rplu2_sidecar_qr_commit_B = 64'd0;
                assign rplu2_sidecar_qr_commit_C = 64'd0;
                assign rplu2_sidecar_qr_commit_D = 64'd0;
                assign rplu2_sidecar_debug_status = 8'd0;
                assign rplu2_sidecar_debug_state = 3'd0;
            end
        end
    endgenerate

    // ── SPI Slave → Instruction Bridge ──────────────────────
    wire sidecar_status = (_L || _U || _R2_LIVE || _R2_PADE) ? 1'b1 : !_CORE;
    wire [7:0] sidecar_status_hi = (_R2_LIVE || _R2_PADE) ? rplu2_sidecar_debug_status :
                                   (_U ? su3_debug_status : 8'h5A);
    wire signed [2:0] spi_status_ratio_res = sidecar_status ?
        ((_R2_LIVE || _R2_PADE) ? rplu2_sidecar_debug_state : su3_debug_state) :
        ratio_cmp_res;
    wire spi_status_ratio_valid = sidecar_status ? 1'b1 : ratio_cmp_valid;
    wire [15:0] spi_status_index = sidecar_status ?
        {sidecar_status_hi, debug_last_spi_opcode} : core_rotc_debug_status;
    wire [3:0] spi_status_snaps = sidecar_status ?
        {1'b0, debug_sidecar_error_seen,
         debug_sidecar_claim_seen, debug_sidecar_commit_seen} :
        {3'd0, core_rotc_debug_status[0]};
    wire spi_status_janus = sidecar_status ?
        debug_sidecar_claim_seen : core_rotc_debug_status[1];
    wire spi_status_turbulence = sidecar_status ?
        debug_sidecar_error_seen :
        (core_rotc_debug_status[2] || debug_rotc_commit_seen ||
         axiomatic_fault || lucas_error ||
         lucas_norm_violation || su3_error ||
         rns_error || ecc_double_err);
    wire spi_status_mode = sidecar_status ?
        (lucas_busy || su3_busy || rplu2_sidecar_busy) : core_rotc_debug_status[3];

    spu_spi_slave u_spi (
        .clk(clk_fast), .rst_n(rst_n),
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck),
        .spi_mosi(spi_mosi), .spi_miso(spi_miso),
        .manifold_state(manifold_state),
        .satellite_snaps(spi_status_snaps),
        .is_janus_point(spi_status_janus),
        .dissonance(quadrance_out[15:0]),
        .scale_table(scale_table),
        .scale_overflow(scale_overflow),
        .qr_commit_valid(spi_qr_commit_valid),
        .qr_commit_lane(spi_qr_commit_lane),
        .qr_commit_A(spi_qr_commit_A),
        .qr_commit_B(spi_qr_commit_B),
        .qr_commit_C(spi_qr_commit_C),
        .qr_commit_D(spi_qr_commit_D),
        .hex_valid(hex_valid), .hex_q(hex_q), .hex_r(hex_r),
        .rplu_ratio_res(spi_status_ratio_res),
        .rplu_ratio_valid(spi_status_ratio_valid),
        .rplu_cfg_wr_en(rplu_cfg_wr_en),
        .rplu_cfg_sel(rplu_cfg_sel),
        .rplu_cfg_material(rplu_cfg_material),
        .rplu_cfg_addr(rplu_cfg_addr),
        .rplu_cfg_data(rplu_cfg_data),
        .inst_valid(spi_inst_valid), .inst_word(spi_inst_word),
        .fifo_full(1'b0),
        .laminar_index(spi_status_index),
        .turbulence(spi_status_turbulence),
        .rplu_mode(spi_status_mode),
        .boot_ready(core_boot_ready),
        .sentinel_telemetry(southbridge_telemetry)
    );

    // ── UART TX ─────────────────────────────────────────────
    generate
        if (A7_UART_DIAG == 0) begin : gen_uart_real
            surd_uart_tx #(.BAUD(115200), .CLK_HZ(50_000_000)) u_uart (
                .clk(clk_fast),
                .reset(!rst_n),
                .data_in({32'd0, hex_q, hex_r}),
                .start(hex_valid),
                .tx(uart_tx),
                .ready()
            );
        end else begin : gen_uart_diag
            // Free-running diagnostic line, clocked off clk_100mhz (not
            // clk_fast, so baud timing stays correct regardless of
            // A7_CLK_DIV_LOG2): "DIAG HB:x CS:x AC:x RDY:x\r\n" where each
            // x is the sticky/heartbeat bit latched at the start of that
            // message. HB toggling proves clk_100mhz/reset are healthy;
            // CS proves a CS falling edge physically reached this pin; AC
            // proves an independently-shifted 8-bit 0xAC frame was seen
            // while CS was active; RDY is core_boot_ready itself.
            localparam BAUD_DIV = 434; // 50MHz/115200, matches the probes
            localparam MSG_LEN = 39; // includes trailing \r\n in the array
            // Force plain FF/LUT implementation -- this array is tiny
            // (39x8 = 312 bits) and never needs a memory primitive. NOTE:
            // ruled out as the cause of the u_spi PnR timing failure below
            // (that failure reproduces identically on the pre-existing,
            // already-committed spu_a7_top.v with no LC: field at all --
            // it's the pre-existing "boot_ready/nextpnr regression"
            // mentioned above, not something this array introduced).
            // Kept anyway since forcing FF/LUT here is still correct.
            (* ram_style = "distributed" *) reg [7:0] msg [0:MSG_LEN-1];
            reg [15:0] baud_cnt = 16'd0;
            wire baud_tick = (baud_cnt == BAUD_DIV-1);
            reg [5:0] msg_idx = 6'd0;
            reg [9:0] shift_reg = 10'h3FF;
            reg [3:0] bits_rem = 4'd0;
            reg tx_r = 1'b1;
            reg [24:0] gap_cnt = 25'd0;
            reg gapping = 1'b0;

            assign uart_tx = tx_r;

            always @(posedge clk_100mhz) begin
                if (baud_tick)
                    baud_cnt <= 16'd0;
                else
                    baud_cnt <= baud_cnt + 16'd1;

                if (baud_tick) begin
                    if (gapping) begin
                        if (gap_cnt == 25'd115_200) begin
                            gapping <= 1'b0;
                            gap_cnt <= 25'd0;
                        end else begin
                            gap_cnt <= gap_cnt + 25'd1;
                        end
                    end else if (bits_rem == 4'd0) begin
                        if (msg_idx == 5'd0) begin
                            msg[0]  <= "D"; msg[1]  <= "I"; msg[2]  <= "A";
                            msg[3]  <= "G"; msg[4]  <= " "; msg[5]  <= "H";
                            msg[6]  <= "B"; msg[7]  <= ":";
                            msg[8]  <= heartbeat_ctr[26] ? "1" : "0";
                            msg[9]  <= " "; msg[10] <= "C"; msg[11] <= "S";
                            msg[12] <= ":";
                            msg[13] <= diag_cs_ever_seen ? "1" : "0";
                            msg[14] <= " "; msg[15] <= "A"; msg[16] <= "C";
                            msg[17] <= ":";
                            msg[18] <= diag2_cmd_ac_seen ? "1" : "0";
                            msg[19] <= " "; msg[20] <= "R"; msg[21] <= "D";
                            msg[22] <= "Y"; msg[23] <= ":";
                            msg[24] <= core_boot_ready ? "1" : "0";
                            msg[25] <= " "; msg[26] <= "B"; msg[27] <= "S";
                            msg[28] <= "T"; msg[29] <= ":";
                            // 0=RESET 1=HYDRATING 2=READY 3=FAULT
                            msg[30] <= 8'h30 + {6'd0, core_boot_state_dbg};
                            msg[31] <= " "; msg[32] <= "L"; msg[33] <= "C";
                            msg[34] <= ":";
                            // Last full 8-bit command frame diag2's own
                            // independent shifter decoded, live -- NOT
                            // sticky-to-AC like diag2_cmd_ac_seen above, so
                            // this catches an intermittent misdecode on a
                            // later transaction that a sticky flag can't.
                            msg[35] <= (diag2_last_cmd_byte[7:4] < 4'd10) ?
                                       (8'h30 + {4'd0, diag2_last_cmd_byte[7:4]}) :
                                       (8'h41 + {4'd0, diag2_last_cmd_byte[7:4]} - 8'd10);
                            msg[36] <= (diag2_last_cmd_byte[3:0] < 4'd10) ?
                                       (8'h30 + {4'd0, diag2_last_cmd_byte[3:0]}) :
                                       (8'h41 + {4'd0, diag2_last_cmd_byte[3:0]} - 8'd10);
                            msg[37] <= 8'h0d; // \r
                            msg[38] <= 8'h0a; // \n
                        end
                        // Only load+shift a real character while msg_idx is
                        // still in range; the out-of-range pass (msg_idx ==
                        // MSG_LEN) happens strictly after the last real
                        // character (msg[MSG_LEN-1], '\n') has *fully*
                        // shifted out over its own 10 bits_rem cycles, so
                        // gapping never preempts an in-progress character.
                        if (msg_idx < MSG_LEN) begin
                            shift_reg <= {1'b1, msg[msg_idx], 1'b0};
                            bits_rem <= 4'd10;
                            msg_idx <= msg_idx + 5'd1;
                        end else begin
                            msg_idx <= 5'd0;
                            gapping <= 1'b1;
                            tx_r <= 1'b1;
                        end
                    end else begin
                        tx_r <= shift_reg[0];
                        shift_reg <= {1'b1, shift_reg[9:1]};
                        bits_rem <= bits_rem - 4'd1;
                    end
                end
            end
        end
    endgenerate

    // led_out tied off, THIS UNIT ONLY: this Wukong's led_out bank
    // (V17/W21/Y21/V26) has shown abnormal voltage patterns even on
    // bitstreams with zero LED-related logic (see
    // a7-wukong-bringup-session notes / spu_a7_100t.xdc) -- not a
    // reliable witness for anything, diagnostic or otherwise, until that
    // anomaly is separately explained. Diagnostic bits (heartbeat,
    // diag_cs_ever_seen, core_boot_ready, diag2_cmd_ac_seen) still exist
    // above as regs for probing with a simulator/ILA; they're just not
    // routed to the pins. Don't restore this assignment on a
    // known-healthy board without revisiting -- LED status output itself
    // isn't the problem, this unit's bank is.
    assign led_out = 4'b0000;
    assign fault_led = axiomatic_fault || lucas_error || su3_error ||
                       rplu2_sidecar_error;
    assign hdmi_d_p = 4'd0;
    assign hdmi_d_n = 4'd0;
    assign hdmi_clk_p = 1'b0;
    assign hdmi_clk_n = 1'b0;

endmodule
