// Isolated partial experiment: no CPU start or reset-barrier implementation.
module h0_program_banks(
 input wire clk, raw_rst_n, run_owned,
 input wire begin_load, write_valid, input wire [3:0] write_addr,
 input wire [63:0] write_data, input wire validate,
 output reg active_valid, output reg loading, output reg checking,
 output reg accepted, rejected, promoted,
 input wire [3:0] fetch_addr, output reg [63:0] fetch_data
);
 reg [63:0] bank0[0:13], bank1[0:13];
 reg active_sel;
 reg [4:0] count;
 reg [3:0] check_index;
 reg bad, denom_nonzero;
 wire [63:0] check_word = active_sel ? bank0[check_index] : bank1[check_index];
 wire [7:0] index_byte = {4'b0, check_index};
 wire word_ok = check_index<6 ?
    (check_word[63:40] == {8'h70,8'h00,index_byte} && check_word[7:0]==0) :
    check_index==6 ? check_word==64'h7100000000000000 :
    check_index==7 ? check_word==64'h7300000000000000 :
    check_index<14 && check_word == (64'h7200000000000000 | ((check_index-4'd8)*64'h10000000000));
 always @(posedge clk) begin
  if (fetch_addr<14 && active_valid)
   fetch_data <= active_sel ? bank1[fetch_addr] : bank0[fetch_addr];
  else fetch_data <= 0;
 end
 always @(posedge clk or negedge raw_rst_n) begin
  if(!raw_rst_n) begin
   active_valid<=0; active_sel<=0; loading<=0; checking<=0; count<=0;
   check_index<=0; bad<=0; denom_nonzero<=0;
   accepted<=0; rejected<=0; promoted<=0;
  end else begin
   accepted<=0; rejected<=0; promoted<=0;
   if (checking) begin
    if (begin_load || write_valid || validate) rejected<=1;
    if (run_owned) begin checking<=0; rejected<=1; end
    else begin
     if (!word_ok) bad<=1;
     if ((check_index==4 || check_index==5) && check_word[39:8]!=0)
      denom_nonzero<=1;
     if (check_index==13) begin
      checking<=0;
      if (!bad && word_ok && denom_nonzero) begin
       active_sel<=!active_sel; active_valid<=1; promoted<=1;
      end else rejected<=1;
     end else check_index<=check_index+1'b1;
    end
   end else if (begin_load || write_valid || validate) begin
    if (run_owned || (begin_load && write_valid) || (begin_load && validate) ||
        (write_valid && validate)) rejected<=1;
    else if (begin_load) begin loading<=1; count<=0; accepted<=1; end
    else if (write_valid) begin
     if (!loading || count>=14 || write_addr!=count) begin loading<=0; rejected<=1; end
     else begin
      if (active_sel) bank0[write_addr]<=write_data;
      else bank1[write_addr]<=write_data;
      count<=count+1'b1; accepted<=1;
     end
    end else if (!loading || count!=14) begin loading<=0; rejected<=1; end
    else begin loading<=0; checking<=1; check_index<=0; bad<=0; denom_nonzero<=0; accepted<=1; end
   end
  end
 end
endmodule
