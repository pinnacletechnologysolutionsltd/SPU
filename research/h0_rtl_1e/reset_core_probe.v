// Simulation-only controlled-reset probe. Not a production reset implementation.
module h0_reset_core_probe(
 input wire clk, raw_rst_n, init_req, cmd_valid, input wire [63:0] cmd_word,
 output wire cpu_rst_n, init_done, cmd_ready, busy, retire, rd, we,
 output wire [3:0] status, output wire [31:0] data,
 output reg [191:0] results, output reg [5:0] result_valid, output reg complete
);
 localparam RESET=0, RELEASE=1, WAIT_BOOT=2, READY=3;
 reg [1:0] state; reg sampled, pending; reg [2:0] slice;
 reg [4:0] retired_count; reg [1:0] kind;
 wire boot, issue_ready, valid;
 wire [2:0] dst;
 assign cpu_rst_n=raw_rst_n && state!=RESET;
 assign init_done=raw_rst_n && state==READY && !init_req;
 assign cmd_ready=init_done && !pending && issue_ready && !retire && !complete;
 assign valid=cmd_valid && cmd_ready;
 always @(posedge clk or negedge raw_rst_n) begin
  if(!raw_rst_n) begin
   state<=RESET; sampled<=0; pending<=0; slice<=0; kind<=0;
   retired_count<=0; results<=0; result_valid<=0; complete<=0;
  end else if(init_req) begin
   state<=RESET; sampled<=0; pending<=0; slice<=0; kind<=0;
   retired_count<=0; results<=0; result_valid<=0; complete<=0;
  end else case(state)
   RESET: if(!sampled) sampled<=1; else begin sampled<=0;state<=RELEASE;end
   RELEASE: state<=WAIT_BOOT;
   WAIT_BOOT: if(boot && !busy && !retire) state<=READY;
   READY: begin
    if(valid) begin pending<=1; slice<=cmd_word[42:40];
      kind<=cmd_word[63:56]==8'h72 ? 2 : (cmd_word[63:56]==8'h71 || cmd_word[63:56]==8'h73) ? 1 : 0; end
    if(retire && pending) begin
     pending<=0;
     if(status==0 && ((kind==2 && rd && !we) || (kind==1 && !rd && we) || (kind==0 && !rd && !we))) begin
      retired_count<=retired_count+1'b1;
      if(kind==2) begin results[32*slice +: 32]<=data;result_valid[slice]<=1;end
      if(retired_count==13 && kind==2 && slice==5 && result_valid==6'b011111) complete<=1;
     end
    end
   end
   default: state<=RESET;
  endcase
 end
 spu13_core #(.DEVICE("SIM"),.ENABLE_SURD_CPU(1),.ENABLE_SEQUENCER(0),.ENABLE_RPLU(0),
 .ENABLE_LATTICE(0),.ENABLE_MATH(0),.ENABLE_CORE_SOM(0),.ENABLE_CORE_RPLU_V2(0),
 .ENABLE_CORE_RPLU_V2_PIPELINE(0),.ENABLE_CORE_RPLU_V2_EXTENSIONS(0),.ENABLE_REGEN(0),
 .ENABLE_IROTC(0),.ENABLE_TORUS(0)) core (
 .clk(clk),.rst_n(cpu_rst_n),.phi_8(1'b0),.phi_13(1'b0),.phi_21(1'b0),
 .dec_fast_cfg_wr_en(1'b0),.dec_fast_cfg_sel(3'd0),.dec_fast_cfg_material(8'd0),
 .dec_fast_cfg_addr(10'd0),.dec_fast_cfg_data(64'd0),.phinary_cfg(16'd0),
 .prime_data(24'd0),.prime_addr(4'd0),.prime_we(1'b0),.boot_done(1'b1),
 .pell_data(32'd0),.pell_addr(3'd0),.pell_we(1'b0),.manual_rotor_en(1'b0),
 .manual_rotor_data(64'd0),.regen_dphi_cfg(8'd0),.mem_ready(1'b1),
 .mem_rd_manifold(832'd0),.mem_burst_done(1'b0),.inst_valid(valid),.inst_word(cmd_word),
 .boot_ready(boot),.surd_issue_ready(issue_ready),.surd_busy(busy),
 .surd_retire_valid(retire),.surd_write_valid(we),.surd_read_valid(rd),
 .surd_status(status),.surd_retire_dst(dst),.surd_read_data(data),
 .rplu_pade_mult_r0(32'd0),.rplu_pade_mult_r1(32'd0),.rplu_pade_mult_r2(32'd0),
 .rplu_pade_mult_r3(32'd0),.rplu_pade_mult_done(1'b0),.rplu_pade_mult_busy(1'b0),
 .rplu_pade_mult_rns_error(1'b0));
endmodule
