// Five shared 64-bit products for exact Surd MUL and aligned ADD/SUB.
module surd_cpu_products (
    input wire aligned, input wire subtract,
    input wire [63:0] a,b,d,c,e,f,u,v,
    output wire signed [129:0] raw_a,raw_b,
    output wire [127:0] raw_d
);
    wire [63:0] x0=a, y0=aligned ? u:c;
    wire [63:0] x1=aligned ? c:b, y1=aligned ? v:e;
    wire [63:0] x2=aligned ? b:a, y2=aligned ? u:e;
    wire [63:0] x3=aligned ? e:b, y3=aligned ? v:c;
    wire [63:0] y4=aligned ? u:f;
    wire [127:0] p0=x0*y0, p1=x1*y1, p2=x2*y2, p3=x3*y3;
    assign raw_d=d*y4;
    function [127:0] corrected;
        input [127:0] product;
        input [63:0] x,y;
        input sign_y;
        reg [127:0] t;
        begin
            t=product;
            if(x[63]) t=t-({64'd0,y}<<64);
            if(sign_y && y[63]) t=t-({64'd0,x}<<64);
            corrected=t;
        end
    endfunction
    wire [127:0] q0=corrected(p0,x0,y0,!aligned);
    wire [127:0] q1=corrected(p1,x1,y1,!aligned);
    wire [127:0] q2=corrected(p2,x2,y2,!aligned);
    wire [127:0] q3=corrected(p3,x3,y3,!aligned);
    wire signed [129:0] z0={{2{q0[127]}},q0};
    wire signed [129:0] z1={{2{q1[127]}},q1};
    wire signed [129:0] z2={{2{q2[127]}},q2};
    wire signed [129:0] z3={{2{q3[127]}},q3};
    assign raw_a=aligned ? (subtract ? z0-z1:z0+z1) : z0+(z1<<<1)+z1;
    assign raw_b=aligned ? (subtract ? z2-z3:z2+z3) : z2+z3;
endmodule
