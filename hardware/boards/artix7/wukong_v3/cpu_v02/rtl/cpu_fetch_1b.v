module cpu_fetch_1b(
 input wire clk, rst_n, boot_ready, issue_ready,
 input wire retire_valid, input wire [3:0] retire_status,
 input wire read_valid, input wire [31:0] read_data, input wire write_valid,
 output wire inst_valid, output wire [63:0] inst_word,
 output reg [3:0] pc, output reg halted, fault,
 output reg [191:0] result, output reg [5:0] result_valid,
 output reg [3:0] state
);
 localparam BOOT=0,FETCH=1,FETCH_WAIT=2,ISSUE=3,WAIT_RETIRE=4,REARM=5,HALT=6,FAULT=7;
 (* ram_style="block" *) reg [63:0] rom[0:15]; reg [63:0] rom_data,held_word;
 initial begin
  rom[0]=64'h7000000000000100; rom[1]=64'h7000010000000000;
  rom[2]=64'h7000020000000200; rom[3]=64'h7000030000000000;
  rom[4]=64'h7000040000000300; rom[5]=64'h7000050000000000;
  rom[6]=64'h7100000000000000; rom[7]=64'h7300000000000000;
  rom[8]=64'h7200000000000000; rom[9]=64'h7200010000000000;
  rom[10]=64'h7200020000000000;rom[11]=64'h7200030000000000;
  rom[12]=64'h7200040000000000;rom[13]=64'h7200050000000000;
  rom[14]=0;rom[15]=0;
 end
 always @(posedge clk) if(state==FETCH) rom_data<=rom[pc];
 assign inst_valid=(state==ISSUE); assign inst_word=held_word;
 wire is_read=(held_word[63:56]==8'h72);
 wire expects_write=(held_word[63:56]==8'h71 || held_word[63:56]==8'h73);
 wire encoding_ok=(rom_data[63:56]==8'h70 && rom_data[55:48]==0 && rom_data[47:40]<6 && rom_data[7:0]==0) ||
                  (rom_data==64'h7100000000000000) || (rom_data==64'h7300000000000000) ||
                  (rom_data[63:56]==8'h72 && rom_data[55:48]==0 && rom_data[47:40]<6 && rom_data[39:0]==0);
 task retire; begin
  if(retire_status!=0 || (is_read && !read_valid) || (!is_read && read_valid) ||
     (write_valid != expects_write)) begin fault<=1;state<=FAULT;end
  else begin
   if(is_read) begin result[32*held_word[42:40] +: 32]<=read_data;result_valid[held_word[42:40]]<=1;end
   state<=REARM;
  end
 end endtask
 always @(posedge clk) begin
  if(!rst_n) begin pc<=0;halted<=0;fault<=0;result<=0;result_valid<=0;state<=BOOT;held_word<=0;end
  else if(retire_valid && !((state==ISSUE && issue_ready) || state==WAIT_RETIRE)) begin fault<=1;state<=FAULT;halted<=0;end
  else case(state)
   BOOT: if(boot_ready) state<=FETCH;
   FETCH: state<=FETCH_WAIT;
   FETCH_WAIT: if(!encoding_ok) begin fault<=1;state<=FAULT;end else begin held_word<=rom_data;state<=ISSUE;end
   ISSUE: if(issue_ready) begin if(retire_valid) retire; else state<=WAIT_RETIRE; end
   WAIT_RETIRE: if(retire_valid) retire;
   REARM: if(pc==13) begin pc<=pc+1'b1;halted<=1;state<=HALT;end else begin pc<=pc+1'b1;state<=FETCH;end
   HALT: state<=HALT;
   FAULT: state<=FAULT;
   default: begin fault<=1;state<=FAULT;end
  endcase
 end
endmodule
