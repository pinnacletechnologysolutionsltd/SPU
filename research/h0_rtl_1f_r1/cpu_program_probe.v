// Experimental single-clock programmable CPU. Not a qualified reset boundary.
module h0_cpu_program_probe(
 input wire clk,raw_rst_n,start,begin_load,write_valid,validate,
 input wire [3:0] write_addr,input wire [63:0] write_data,input wire [31:0] expected_crc,
 output wire active_valid,loading,checking,bank_accept,bank_reject,promoted,
 output reg owned,complete,fault, output reg [3:0] pc,
 output reg [191:0] result,output reg [5:0] result_valid,
 output reg [31:0] run_id,output wire cpu_rst_n
);
 localparam IDLE=0,INIT=1,RELEASE=2,WAIT_BOOT=3,FETCH=4,FETCH_WAIT=5,
            ISSUE=6,WAIT_RETIRE=7,REARM=8,FAILED=9;
 reg [3:0] state;reg sampled;reg [63:0] held_word;
 wire [63:0] fetched;
 wire start_ok=start && state==IDLE && active_valid && !loading && !checking &&
               !begin_load && !write_valid && !validate;
 wire bank_owned=owned || start_ok;
 h0_program_banks_v2 banks(.clk(clk),.raw_rst_n(raw_rst_n),.run_owned(bank_owned),
  .begin_load(begin_load),.write_valid(write_valid),.write_addr(write_addr),.write_data(write_data),
  .validate(validate),.expected_crc(expected_crc),.active_valid(active_valid),.loading(loading),
  .checking(checking),.accepted(bank_accept),.rejected(bank_reject),.promoted(promoted),
  .fetch_addr(pc),.fetch_data(fetched));
 wire boot,ready,busy,retire,we,rd;wire [3:0] status;wire [2:0] dst;wire [31:0] data;
 wire valid=(state==ISSUE) && owned && cpu_rst_n && !retire;
 assign cpu_rst_n=raw_rst_n && state!=INIT && state!=IDLE;
 task accept_retirement; begin
  if(status!=0 || ((held_word[63:56]==8'h72) != rd) ||
     (we != (held_word[63:56]==8'h71 || held_word[63:56]==8'h73))) begin
   fault<=1;state<=FAILED;
  end else begin
   if(rd)begin result[32*held_word[42:40] +: 32]<=data;result_valid[held_word[42:40]]<=1;end
   state<=REARM;
  end
 end endtask
 always @(posedge clk or negedge raw_rst_n) begin
  if(!raw_rst_n)begin state<=IDLE;sampled<=0;owned<=0;complete<=0;fault<=0;pc<=0;
    held_word<=0;result<=0;result_valid<=0;run_id<=0;end
  else case(state)
   IDLE: if(start_ok) begin owned<=1;complete<=0;fault<=0;pc<=0;result<=0;result_valid<=0;
     held_word<=0;run_id<=run_id+1'b1;sampled<=0;state<=INIT;end
   INIT: if(!sampled)sampled<=1;else begin sampled<=0;state<=RELEASE;end
   RELEASE: state<=WAIT_BOOT;
   WAIT_BOOT: if(retire)begin fault<=1;state<=FAILED;end
              else if(boot && !busy)state<=FETCH;
   FETCH: if(retire)begin fault<=1;state<=FAILED;end else state<=FETCH_WAIT;
   FETCH_WAIT: if(retire)begin fault<=1;state<=FAILED;end else begin held_word<=fetched;state<=ISSUE;end
   // This selected core registers retirement after acceptance; a pre-existing
   // retirement on the acceptance edge cannot belong to the new instruction.
   ISSUE: if(retire)begin fault<=1;state<=FAILED;end
          else if(ready)state<=WAIT_RETIRE;
   WAIT_RETIRE: if(retire)accept_retirement();
   REARM: if(retire)begin fault<=1;state<=FAILED;end
          else if(pc==13)begin
           if(result_valid==6'h3f)begin complete<=1;owned<=0;pc<=14;state<=IDLE;end
           else begin fault<=1;state<=FAILED;end
          end else begin pc<=pc+1'b1;state<=FETCH;end
   FAILED: begin owned<=0;complete<=0;state<=IDLE;end
   default: begin fault<=1;owned<=0;complete<=0;state<=IDLE;end
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
 .mem_rd_manifold(832'd0),.mem_burst_done(1'b0),.inst_valid(valid),.inst_word(held_word),
 .boot_ready(boot),.surd_issue_ready(ready),.surd_busy(busy),.surd_retire_valid(retire),
 .surd_write_valid(we),.surd_read_valid(rd),.surd_status(status),.surd_retire_dst(dst),.surd_read_data(data),
 .rplu_pade_mult_r0(32'd0),.rplu_pade_mult_r1(32'd0),.rplu_pade_mult_r2(32'd0),
 .rplu_pade_mult_r3(32'd0),.rplu_pade_mult_done(1'b0),.rplu_pade_mult_busy(1'b0),
 .rplu_pade_mult_rns_error(1'b0));
endmodule
