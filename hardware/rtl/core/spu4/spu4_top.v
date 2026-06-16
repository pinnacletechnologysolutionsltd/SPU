// spu4_top.v
// Top-level SPU-4 Euclidean Processor (v1.0)
// Integrates Decoder, RegFile, and ALU into a 24-bit ISA datapath.
// Hardened for "Laminar Purity" (Zero-Branch & Strictly Bitwise).

module spu4_top #(
    parameter ENABLE_RPLU_BRAM = 1,
    parameter [2:0] MY_ID = 3'd0
) (
    input clk,
    input rst_n,
    
    // runtime config inputs (piranha domain)
    input         rplu_cfg_wr_en,
    input [2:0]   rplu_cfg_sel,
    input [7:0]   rplu_cfg_material,
    input [9:0]   rplu_cfg_addr,
    input [63:0]  rplu_cfg_data,
    
    // Program Memory Interface
    input [23:0] inst_data,
    output [9:0] pc,
    
    // Status/IO
    input         sentinel_mode,
    input         piranha_pulse,
    input         bank_sel,       // RPLU mode: 0=Smooth(Q3) 1=Turbulent(Q5)
    output snap_alert,
    output whisper_tx,
    output [1:0]  state_out,      // Exported for telemetry
    output [63:0] debug_reg_r0
);

    reg [9:0] pc_reg;
    assign pc = pc_reg;

    // 1. Decoder (Fetch -> Decode)
    wire [3:0] alu_op;
    wire [2:0] reg_dest, reg_src;
    wire [7:0] imm;
    wire use_imm, snap_en, whisper_en;

    spu4_decoder u_decoder (
        .inst_word(inst_data),
        .alu_op(alu_op),
        .reg_dest(reg_dest),
        .reg_src(reg_src),
        .immediate(imm),
        .use_imm(use_imm),
        .snap_en(snap_en),
        .whisper_en(whisper_en)
    );

    // 2. Register File
    wire [63:0] reg_dout_a, reg_dout_b;
    wire [63:0] reg_din;
    wire [63:0] reg_r0;
    wire reg_we;

    spu4_regfile u_regfile (
        .clk(clk),
        .rst_n(rst_n),
        .we(reg_we),
        .addr_a(reg_dest),
        .addr_b(reg_src),
        .din(reg_din),
        .dout_a(reg_dout_a),
        .dout_b(reg_dout_b),
        .r0_out(reg_r0)
    );

    // 3. ALU Dispatcher
    wire [15:0] rot_a, rot_b, rot_c, rot_d;
    wire rot_done;
    wire rot_start;

    spu4_euclidean_alu u_qrot_alu (
        .clk(clk),
        .reset(!rst_n),
        .start(rot_start),
        .bloom_intensity(8'hFF), 
        .mode_autonomous(1'b0),
        .A_in(reg_dout_a[63:48]), 
        .B_in(reg_dout_a[47:32]), 
        .C_in(reg_dout_a[31:16]), 
        .D_in(reg_dout_a[15:0]),
        .F(16'h00CC), 
        .G(16'h0019), 
        .H(16'h0019), 
        .A_out(rot_a), .B_out(rot_b), .C_out(rot_c), .D_out(rot_d),
        .done(rot_done),
        .henosis_pulse()
    );


    // 4. Control State Transitions (Gestalt Logic)
    // 0: FETCH, 1: EXEC, 2: WAIT_ALU, 3: WRITEBACK
    reg [1:0] state; 
    assign state_out = state;
    
    wire is_fetch;
    assign is_fetch = (state == 2'd0);
    wire is_exec;
    assign is_exec = (state == 2'd1);
    wire is_wait_alu;
    assign is_wait_alu = (state == 2'd2);
    wire is_writeback;
    assign is_writeback = (state == 2'd3);

    wire is_qrot_op;
    assign is_qrot_op = (alu_op == 4'h3);

    // Calculate Next State
    wire [1:0] ns_exec_choice;
    assign ns_exec_choice = ({2{is_qrot_op}} & 2'd2) | ({2{!is_qrot_op}} & 2'd3);
    wire [1:0] ns_wait_choice;
    assign ns_wait_choice = ({2{rot_done}}   & 2'd3) | ({2{!rot_done}}   & 2'd2);
    
    wire [1:0] next_state = 
        ({2{is_fetch}}      & 2'd1) |
        ({2{is_exec}}       & ns_exec_choice) |
        ({2{is_wait_alu}}   & ns_wait_choice) |
        ({2{is_writeback}}  & 2'd0);

    // Register Write Enable & Data Input selection
    wire state_we;
    assign state_we = (is_exec && !is_qrot_op) || (is_wait_alu && rot_done);
    
    wire [63:0] qldi_val;
    assign qldi_val = { {8'h0, imm}, 48'h0 };
    wire [63:0] qadd_val;
    assign qadd_val = reg_dout_a + reg_dout_b;
    wire [63:0] qrot_val;
    assign qrot_val = {rot_a, rot_b, rot_c, rot_d};

    wire [63:0] inst_din = 
        ({64{alu_op == 4'h1}} & qldi_val) |
        ({64{alu_op == 4'h2}} & qadd_val) |
        ({64{is_wait_alu}}    & qrot_val);

    // Pulse-locked Manifold registers
    reg [63:0] core_din;
    reg core_we;
    reg core_rot_start;
    
    assign reg_din   = core_din;
    assign reg_we    = core_we;
    assign rot_start = core_rot_start;

    always @(posedge clk) begin
        state          <= ({2{rst_n}} & next_state);
        
        // PLC Sentinel Mode: Reset PC on piranha pulse
        if (rst_n && sentinel_mode && piranha_pulse) begin
            pc_reg <= 10'd0;
        end else begin
            pc_reg <= ({10{rst_n && is_writeback}} & (pc_reg + 10'd1)) | ({10{rst_n && !is_writeback}} & pc_reg);
        end

        core_din       <= ({64{rst_n && state_we}} & inst_din) | ({64{rst_n && !state_we}} & core_din);
        core_we        <= (rst_n && state_we);
        core_rot_start <= (rst_n && is_exec && is_qrot_op);
    end

    assign snap_alert = snap_en;
    assign whisper_tx = whisper_en;
    // RPLU BRAM: optional instantiation controlled by ENABLE_RPLU_BRAM
    reg [9:0] target_rplu_addr;
    always @(posedge clk) begin
        if (!rst_n) begin
            target_rplu_addr <= 10'd0;
        end else if (rplu_cfg_wr_en && (rplu_cfg_sel == 7 || rplu_cfg_sel == MY_ID)) begin
            target_rplu_addr <= rplu_cfg_addr;
        end
    end

    wire [5:0] rplu_addr;
    assign rplu_addr = target_rplu_addr[5:0];
    wire [63:0] rplu_data;

    generate
        if (ENABLE_RPLU_BRAM) begin : gen_rplu_bram
            spu4_bram_ip #(
                .ADDR_WIDTH(6),
                .DATA_WIDTH(64),
                .MEM_FILE("hardware/rtl/arch/rplu_dual_bank.mem")
            ) u_rplu_bram (
                .clk(clk),
                .bank_sel(bank_sel),
                .addr(rplu_addr),
                .data_out(rplu_data)
            );
        end else begin
            // Tie off when disabled to avoid generating I/O cells
            assign rplu_data = 64'd0;
        end
    endgenerate

    // Export R0 for telemetry; XOR with rplu_data so rplu_bram is used by synthesis
    assign debug_reg_r0 = reg_r0 ^ rplu_data;

endmodule
