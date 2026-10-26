// One in-flight operation, five product lanes, one shared exact normalizer.
module spu13_surd_arith (
    input wire clk,rst,start, input wire [2:0] op,
    input wire [191:0] lhs,rhs,
    output reg done, output reg [3:0] status,
    output reg [191:0] result,
    output wire [3:0] phase,
    output wire rescue_request,normalization_start
);
    localparam IDLE=0,ALIGN_START=1,ALIGN_WAIT=2,PRODUCT=3,CHECK=4,
               NORM_START=5,NORM_WAIT=6;
    reg [3:0] state;
    reg [2:0] held_op;
    reg [191:0] x,y;
    reg [63:0] u,v;
    reg signed [129:0] raw_a,raw_b;
    reg [127:0] raw_d;
    wire signed [129:0] prod_a,prod_b;
    wire [127:0] prod_d;
    wire aligned=(held_op==4 || held_op==5);
    wire fits_a=raw_a[129:64]=={66{raw_a[63]}};
    wire fits_b=raw_b[129:64]=={66{raw_b[63]}};
    wire fits_d=raw_d[127:64]==0 && raw_d[63:0]!=0;
    wire n_done,n_valid,n_invalid,n_fault,n_fit,n_busy;
    wire signed [129:0] n_a,n_b;
    wire [129:0] n_d;
    wire aligning=(state==ALIGN_START || state==ALIGN_WAIT);
    wire signed [129:0] n_in_a=aligning ? {66'd0,x[191:128]}:raw_a;
    wire signed [129:0] n_in_b=aligning ? 130'd0:raw_b;
    wire [127:0] n_in_d=aligning ? {64'd0,y[191:128]}:raw_d;
    assign phase=state;
    assign normalization_start=(state==ALIGN_START || state==NORM_START);
    assign rescue_request=(state==CHECK && !(fits_a&&fits_b&&fits_d));
    surd_cpu_products products (.aligned(aligned),.subtract(held_op==5),
        .a(x[63:0]),.b(x[127:64]),.d(x[191:128]),
        .c(y[63:0]),.e(y[127:64]),.f(y[191:128]),.u(u),.v(v),
        .raw_a(prod_a),.raw_b(prod_b),.raw_d(prod_d));
    surd_normalize_unit #(.W(64)) normalizer (
        .clk(clk),.rst(rst),.start(normalization_start),
        .value_a(n_in_a),.value_b(n_in_b),.value_d(n_in_d),
        .busy(n_busy),.done(n_done),.valid(n_valid),.invalid(n_invalid),
        .fault(n_fault),.fits_W(n_fit),.norm_a(n_a),.norm_b(n_b),.norm_d(n_d));
    task finish;
        input [3:0] code;
        begin status<=code;done<=1;state<=IDLE;end
    endtask
    always @(posedge clk) begin
        if(rst) begin
            state<=IDLE;held_op<=0;done<=0;status<=0;result<={64'd1,128'd0};
            x<=0;y<=0;u<=0;v<=0;raw_a<=0;raw_b<=0;raw_d<=1;
        end else begin
            done<=0;
            case(state)
                IDLE: if(start) begin
                    x<=lhs;y<=rhs;held_op<=op;
                    if(lhs[191:128]==0 || (op!=6 && rhs[191:128]==0)) finish(1);
                    else if(op==6) begin
                        raw_a<={{66{lhs[63]}},lhs[63:0]};
                        raw_b<={{66{lhs[127]}},lhs[127:64]};
                        raw_d<={64'd0,lhs[191:128]};state<=NORM_START;
                    end else if(op==4 || op==5) state<=ALIGN_START;
                    else state<=PRODUCT;
                end
                ALIGN_START: state<=ALIGN_WAIT;
                ALIGN_WAIT: if(n_done) begin
                    if(n_fault || !n_valid || n_a[129:64]!=0 || n_d[129:64]!=0 ||
                       n_a[63:0]==0 || n_d[63:0]==0) finish(3);
                    else begin v<=n_a[63:0];u<=n_d[63:0];state<=PRODUCT;end
                end
                PRODUCT: begin raw_a<=prod_a;raw_b<=prod_b;raw_d<=prod_d;state<=CHECK;end
                CHECK: if(fits_a&&fits_b&&fits_d) begin
                    result<={raw_d[63:0],raw_b[63:0],raw_a[63:0]};finish(0);
                end else state<=NORM_START;
                NORM_START: state<=NORM_WAIT;
                NORM_WAIT: if(n_done) begin
                    if(n_invalid) finish(1);
                    else if(n_fault || !n_valid) finish(3);
                    else if(!n_fit) finish(2);
                    else begin result<={n_d[63:0],n_b[63:0],n_a[63:0]};finish(0);end
                end
                default: finish(3);
            endcase
        end
    end
endmodule
