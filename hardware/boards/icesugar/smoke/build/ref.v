module Test (
  output reg [2:0] io_led,
  input            clk,
  input            reset
);
  reg [31:0] status;
  always @ (*) begin
    io_led[0] = status[23];
    io_led[1] = status[25];
    io_led[2] = status[27];
  end
  always @ (posedge clk or posedge reset) begin
    if (reset) status <= 32'h0;
    else       status <= status + 32'h1;
  end
endmodule
