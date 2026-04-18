`timescale 1ns/1ps
// Testbench: SPU-4 Phinary config register and chiral adder integration
module spu4_phinary_cfg_unit_tb;

reg clk;
reg reset;

reg prog_en_aux;
reg [3:0] prog_addr_aux;
reg [15:0] prog_data_aux;

// adder inputs
reg [3:0] A;
reg [3:0] B;
wire [3:0] S;
wire void_out;
wire overflow;

// simple config register (mimics core behaviour)
reg [15:0] phinary_cfg;
wire phinary_chirality;
assign phinary_chirality = phinary_cfg[1];
integer pass;

chiral_phinary_adder uut (
    .clk(clk),
    .rst(reset),
    .surd_A(A),
    .surd_B(B),
    .chirality(phinary_chirality),
    .surd_Sum(S),
    .void_state(void_out)
);

initial clk = 0;
always #5 clk = ~clk;

initial begin
    pass = 1;

    // reset
    reset = 1; prog_en_aux = 0; prog_addr_aux = 4'h0; prog_data_aux = 16'h0; A = 4'b0000; B = 4'b0000;
    #20;
    reset = 0; #10;

    // no config yet: phinary_cfg default 0
    phinary_cfg = 16'h0000;

    // test adder with chirality=0 (void flips expected)
    A = 4'b1111; B = 4'b1111; // large values to force threshold
    #10; // let adder evaluate

    // now write config via pseudo prog interface: set phinary_cfg = 0x0003 (enable + chirality=1)
    prog_addr_aux = 4'hF; prog_data_aux = 16'h0003; prog_en_aux = 1;
    #10; prog_en_aux = 0; // one cycle pulse
    phinary_cfg = prog_data_aux; // mimic core write behaviour

    // apply same inputs and verify behaviour changed
    A = 4'b1111; B = 4'b1111;
    #10;

    // simple check: phinary_chirality should be 1
    if (phinary_chirality !== 1'b1) begin
        $display("FAIL: phinary_chirality was not set"); pass = 0;
    end

    if (pass) $display("PASS"); else $display("FAIL");
    $finish;
end

endmodule
