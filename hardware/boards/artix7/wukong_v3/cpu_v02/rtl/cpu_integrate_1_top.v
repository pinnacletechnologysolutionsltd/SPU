// Isolated logical integration; no board pin or physical timing claim.
module cpu_integrate_1_top(
 input wire sys_clk,raw_rst_n,
 output wire cpu_clk,cpu_rst_n,reset_ack,complete,halted,fault,
 output wire [3:0] pc,state,
 output wire [191:0] result,output wire [5:0] result_valid
);
 wire hold,pending,latched,valid,boot,ready,busy,done,retire,we,rd;
 wire [63:0] word;wire [3:0] status;wire [2:0] dst;wire [31:0] data;

 cpu_rst_1b_supervisor s(.sys_clk(sys_clk),.raw_rst_n(raw_rst_n),.test_pause(1'b0),.halted(halted),.fault(fault),.result_valid(result_valid),.cpu_clk(cpu_clk),.cpu_rst_n(cpu_rst_n),.reset_ack(reset_ack),.result_complete(complete),.reset_hold(hold),.request_pending(pending),.completion_latched(latched));
 cpu_fetch_1b f(.clk(cpu_clk),.rst_n(cpu_rst_n),.boot_ready(boot),.issue_ready(ready),.retire_valid(retire),.retire_status(status),.read_valid(rd),.read_data(data),.write_valid(we),.inst_valid(valid),.inst_word(word),.pc(pc),.halted(halted),.fault(fault),.result(result),.result_valid(result_valid),.state(state));
spu13_core #(.DEVICE("SIM"),.ENABLE_SURD_CPU(1),.ENABLE_SEQUENCER(0),.ENABLE_RPLU(0),.ENABLE_LATTICE(0),.ENABLE_MATH(0),.ENABLE_CORE_SOM(0),.ENABLE_CORE_RPLU_V2(0),.ENABLE_CORE_RPLU_V2_PIPELINE(0),.ENABLE_CORE_RPLU_V2_EXTENSIONS(0),.ENABLE_REGEN(0),.ENABLE_IROTC(0),.ENABLE_TORUS(0)) dut (
.clk(cpu_clk),.rst_n(cpu_rst_n),.phi_8(1'b0),.phi_13(1'b0),.phi_21(1'b0),.dec_fast_cfg_wr_en(1'b0),.dec_fast_cfg_sel(3'd0),.dec_fast_cfg_material(8'd0),.dec_fast_cfg_addr(10'd0),.dec_fast_cfg_data(64'd0),.phinary_cfg(16'd0),.prime_data(24'd0),.prime_addr(4'd0),.prime_we(1'b0),.boot_done(1'b1),.pell_data(32'd0),.pell_addr(3'd0),.pell_we(1'b0),.manual_rotor_en(1'b0),.manual_rotor_data(64'd0),.regen_dphi_cfg(8'd0),.mem_ready(1'b1),.mem_rd_manifold(832'd0),.mem_burst_done(1'b0),.inst_valid(valid),.inst_word(word),.inst_done(done),.boot_ready(boot),.surd_issue_ready(ready),.surd_busy(busy),.surd_retire_valid(retire),.surd_write_valid(we),.surd_read_valid(rd),.surd_status(status),.surd_retire_dst(dst),.surd_read_data(data),
.rplu_pade_mult_r0(32'd0),.rplu_pade_mult_r1(32'd0),.rplu_pade_mult_r2(32'd0),.rplu_pade_mult_r3(32'd0),
.rplu_pade_mult_done(1'b0),.rplu_pade_mult_busy(1'b0),.rplu_pade_mult_rns_error(1'b0));
endmodule
