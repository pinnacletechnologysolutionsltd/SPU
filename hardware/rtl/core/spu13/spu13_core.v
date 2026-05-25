// SPU-13 Sovereign Core (v1.9.7 - TDM Math Optimized)
`include "spu_arch_defines.vh"

module spu13_core #(
    parameter DEVICE = "GW5A",
    parameter ENABLE_MATH = 1,
    parameter ENABLE_SEQUENCER = 1
)(
    input  wire clk, rst_n, phi_8, phi_13, phi_21,
    input  wire [23:0] prime_data, input wire [3:0] prime_addr, input wire prime_we, boot_done,
    output wire [31:0] quadrance_out, output reg hex_valid, output reg [15:0] hex_q, hex_r,
    output wire [3:0] current_axis_ptr,
    output wire seq_flash_cs, seq_flash_sck, seq_flash_mosi,
    input wire seq_flash_miso
);
    // 1. Manifold Axis Control
    reg [63:0] r_manifold [0:12]; reg [3:0] r_axis_ptr;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) r_axis_ptr <= 0;
        else if (phi_21) r_axis_ptr <= (r_axis_ptr == 12) ? 0 : r_axis_ptr + 1;
    end
    assign current_axis_ptr = r_axis_ptr;

    // 2. Scalar Rotor Math (Registered)
    wire [31:0] w_rotor_raw;
    spu_rotor_vault u_vault(.clk(clk), .reset(!rst_n), .axis_id(r_axis_ptr), .rot_en(phi_8), .rotor_out(w_rotor_raw));
    wire [63:0] w_rotor_q12 = {{16'b0, w_rotor_raw[31:16]}<<12, {16'b0, w_rotor_raw[15:0]}<<12};
    wire [63:0] w_q_prime;
    spu_cross_rotor #(.DEVICE(DEVICE)) u_rotor(.clk(clk), .reset(!rst_n), .q_axis(r_manifold[r_axis_ptr]), .r_rotor(w_rotor_q12), .q_prime(w_q_prime));

    // 3. Register File & Instruction Logic
    wire [63:0] qrf_rd_A, qrf_rd_B, qrf_rd_C, qrf_rd_D, qrf_wr_A, qrf_wr_B, qrf_wr_C, qrf_wr_D;
    reg qrf_wr_en; reg [3:0] qrf_wr_lane, r_src_lane;
    wire [63:0] inst_w; wire inst_v, inst_d;
    spu_sequencer #(.IMEM_DEPTH(32)) u_seq(.clk(clk), .rst_n(rst_n), .boot_done(boot_done), .inst_valid(inst_v), .inst_word(inst_w), .inst_done(inst_d), .flash_csn(seq_flash_cs), .flash_sck(seq_flash_sck), .flash_mosi(seq_flash_mosi), .flash_miso(seq_flash_miso));

    wire [7:0] op = inst_w[63:56]; wire [3:0] ds = inst_w[55:48]%13, sr = inst_w[47:40]%13;
    wire [3:0] rd_l = (inst_v && (op==8'h1C || op==8'h16)) ? sr : r_src_lane;
    
    // QLDI Data (Combinatorial for same-cycle setup)
    wire [63:0] qlA = {32'd0, {{24{inst_w[39]}}, inst_w[39:32]}};
    wire [63:0] qlB = {32'd0, {{24{inst_w[31]}}, inst_w[31:24]}};
    wire [63:0] qlC = {32'd0, {{24{inst_w[23]}}, inst_w[23:16]}};
    wire [63:0] qlD = {32'd0, {{24{inst_w[15]}}, inst_w[15:8]}};

    spu_quadray_regfile u_qrf(.clk(clk), .rst_n(rst_n), .rd_lane(rd_l), .rd_A(qrf_rd_A), .rd_B(qrf_rd_B), .rd_C(qrf_rd_C), .rd_D(qrf_rd_D), .wr_en(qrf_wr_en), .wr_lane(qrf_wr_lane), .wr_A(qrf_wr_A), .wr_B(qrf_wr_B), .wr_C(qrf_wr_C), .wr_D(qrf_wr_D));

    // 4. Quadray Rotor Logic
    reg rote_en; reg [5:0] r_angle; wire r_d; wire [63:0] rwA, rwB, rwC, rwD, rAi, rBi, rCi, rDi;
    wire [1:0] ps = (r_angle<6)?0:(r_angle<8)?1:(r_angle<10)?2:3;
    spu_quadray_permute u_pf(.perm_sel(ps), .A_in(qrf_rd_A), .B_in(qrf_rd_B), .C_in(qrf_rd_C), .D_in(qrf_rd_D), .A_out(rAi), .B_out(rBi), .C_out(rCi), .D_out(rDi));
    
    wire signed [63:0] rF, rG, rH;
    assign rF = (r_angle==0)?1:(r_angle==1)?2:(r_angle==2)?-1:(r_angle==3)?-1:(r_angle==4)?2:(r_angle==5)?2:(r_angle<12)?2:1;
    assign rG = (r_angle==0)?0:(r_angle==1)?2:(r_angle==2)?2:(r_angle==3)?-1:(r_angle==4)?-1:(r_angle==5)?2:(r_angle<12)?2:0;
    assign rH = (r_angle==0)?0:(r_angle==1)?-1:(r_angle==2)?2:(r_angle==3)?-1:(r_angle==4)?2:(r_angle==5)?-1:(r_angle<12)?2:0;

    spu13_rotor_core_tdm u_rot(.clk(clk), .rst_n(rst_n), .start(rote_en), .done(r_d), .A_in(rAi), .B_in(rBi), .C_in(rCi), .D_in(rDi), .F(rF), .G(rG), .H(rH), .field_sel(2'b00), .bypass_p5(r_angle==2), .A_out(rwA), .B_out(rwB), .C_out(rwC), .D_out(rwD));
    spu_quadray_permute u_pi(.perm_sel((ps==1)?3:(ps==3)?1:ps), .A_in(rwA), .B_in(rwB), .C_in(rwC), .D_in(rwD), .A_out(qrf_wr_A), .B_out(qrf_wr_B), .C_out(qrf_wr_C), .D_out(qrf_wr_D));

    // 5. Main Execution FSM
    reg r_done, r_active; assign inst_d = r_done;
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            r_done<=0; r_active<=0; rote_en<=0; qrf_wr_en<=0; hex_valid<=0; r_src_lane<=0;
            for (i=0; i<13; i=i+1) r_manifold[i] <= 64'h0000200000000000;
        end else begin
            r_done<=0; rote_en<=0; qrf_wr_en<=0; hex_valid<=0;
            if (phi_21) r_manifold[r_axis_ptr] <= w_q_prime;
            if (inst_v && !r_active) begin
                case(op)
                    8'h1D: begin qrf_wr_en<=1; qrf_wr_lane<=ds; r_manifold[ds]<=qlA; r_done<=1; end // Direct QLDI commit
                    8'h1C: begin r_src_lane<=sr; qrf_wr_lane<=ds; r_angle<=inst_w[29:24]; rote_en<=1; r_active<=1; end
                    8'h16: begin r_src_lane<=sr; hex_q<=qrf_rd_A[15:0]-qrf_rd_D[15:0]; hex_r<=qrf_rd_B[15:0]-qrf_rd_D[15:0]; hex_valid<=1; r_done<=1; end
                    default: r_done<=1;
                endcase
            end else if (r_active && r_d) begin
                qrf_wr_en<=1; r_active<=0; r_done<=1;
            end
        end
    end
    davis_gate_dsp u_gate(.clk(clk), .rst_n(rst_n), .q_vector(w_q_prime), .quadrance(quadrance_out));
endmodule
