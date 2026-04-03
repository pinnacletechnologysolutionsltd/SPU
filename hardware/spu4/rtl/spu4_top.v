// spu4_top.v
// Top-level SPU-4 Euclidean Processor (v1.0)
// Integrates Decoder, RegFile, and ALU into a 24-bit ISA datapath.
// Hardened for "Laminar Purity" (Zero-Branch & Strictly Bitwise).

module spu4_top (
    input clk,
    input rst_n,
    
    // Program Memory Interface
    input [23:0] inst_data,
    output [9:0] pc,
    
    // Status/IO
    output snap_alert,
    output whisper_tx,
    output [63:0] debug_reg_r0 // Export R0 for telemetry
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
    wire reg_we;

    spu4_regfile u_regfile (
        .clk(clk),
        .rst_n(rst_n),
        .we(reg_we),
        .addr_a(reg_dest),
        .addr_b(reg_src),
        .din(reg_din),
        .dout_a(reg_dout_a),
        .dout_b(reg_dout_b)
    );

    // 3. ALU Dispatcher
    wire [15:0] rot_a, rot_b, rot_c, rot_d;
    wire rot_done;
    wire rot_start;

    spu_4_euclidean_alu u_qrot_alu (
        .clk(clk),
        .reset(!rst_n),
        .start(rot_start),
        .bloom_intensity(8'hFF), 
        .A_in(reg_dout_a[63:48]), 
        .B_in(reg_dout_a[47:32]), 
        .C_in(reg_dout_a[31:16]), 
        .D_in(reg_dout_a[15:0]),
        .F(16'h00CC), 
        .G(16'h0019), 
        .H(16'h0019), 
        .A_out(rot_a), .B_out(rot_b), .C_out(rot_c), .D_out(rot_d),
        .done(rot_done)
    );

    // 4. Control State Transitions (Gestalt Logic)
    // 0: FETCH, 1: EXEC, 2: WAIT_ALU, 3: WRITEBACK
    reg [1:0] state; 
    
    wire is_fetch     = (state == 2'd0);
    wire is_exec      = (state == 2'd1);
    wire is_wait_alu  = (state == 2'd2);
    wire is_writeback = (state == 2'd3);

    wire is_qrot_op   = (alu_op == 4'h3);

    // Calculate Next State
    wire [1:0] ns_exec_choice = ({2{is_qrot_op}} & 2'd2) | ({2{!is_qrot_op}} & 2'd3);
    wire [1:0] ns_wait_choice = ({2{rot_done}}   & 2'd3) | ({2{!rot_done}}   & 2'd2);
    
    wire [1:0] next_state = 
        ({2{is_fetch}}      & 2'd1) |
        ({2{is_exec}}       & ns_exec_choice) |
        ({2{is_wait_alu}}   & ns_wait_choice) |
        ({2{is_writeback}}  & 2'd0);

    // Register Write Enable & Data Input selection
    wire state_we = (is_exec && !is_qrot_op) || (is_wait_alu && rot_done);
    
    wire [63:0] qldi_val = { {8'h0, imm}, 48'h0 };
    wire [63:0] qadd_val = reg_dout_a + reg_dout_b;
    wire [63:0] qrot_val = {rot_a, rot_b, rot_c, rot_d};

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
        pc_reg         <= ({10{rst_n && is_writeback}} & (pc_reg + 10'd1)) | ({10{rst_n && !is_writeback}} & pc_reg);
        core_din       <= ({64{rst_n && state_we}} & inst_din) | ({64{rst_n && !state_we}} & core_din);
        core_we        <= (rst_n && state_we);
        core_rot_start <= (rst_n && is_exec && is_qrot_op);
    end

    assign snap_alert = snap_en;
    assign whisper_tx = whisper_en;
    assign debug_reg_r0 = u_regfile.rf[0];

endmodule
