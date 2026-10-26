// Standalone Artix-7 mapping/timing wrapper for the exact Surd multiply unit.
// Pseudo-random internal operands keep the arithmetic datapath observable
// without consuming package pins for a wide operand/result bus.
module surd_smul_bench_top #(
    parameter integer W = 16,
    parameter integer LANES = 2
) (
    input wire sys_clk,
    input wire rst_n,
    output wire uart_tx
);
    reg [W-1:0] rng_a, rng_b;
    reg signed [W-1:0] op_a, op_b, op_c, op_e;
    reg [W-1:0] op_d, op_f;
    reg start;
    wire rst = ~rst_n;
    wire signed [W-1:0] a = op_a;
    wire signed [W-1:0] b = op_b;
    wire signed [W-1:0] c = op_c;
    wire signed [W-1:0] e = op_e;
    wire [W-1:0] d = op_d;
    wire [W-1:0] f = op_f;
    wire signed [W-1:0] result_a, result_b;
    wire [W-1:0] result_d;
    wire busy, done, overflow, invalid, norm_req;
    wire signed [2*W+1:0] raw_a, raw_b;
    wire [2*W-1:0] raw_d;

    surd_smul_unit #(.W(W),.LANES(LANES)) dut (
        .clk(sys_clk),.rst(rst),.start(start),
        .a_in(a),.b_in(b),.d_in(d),.c_in(c),.e_in(e),.f_in(f),
        .dst_a(result_a),.dst_b(result_b),.dst_d(result_d),
        .result_a(result_a),.result_b(result_b),.result_d(result_d),
        .busy(busy),.done(done),.overflow(overflow),.invalid(invalid),
        .norm_req(norm_req),.raw_a(raw_a),.raw_b(raw_b),.raw_d(raw_d),
        .norm_valid(norm_req),.norm_a(raw_a),.norm_b(raw_b),.norm_d(raw_d)
    );

    always @(posedge sys_clk) begin
        if (rst) begin
            rng_a <= {{(W-1){1'b0}},1'b1};
            rng_b <= {{(W-2){1'b0}},2'b11};
            op_a <= 0; op_b <= 0; op_c <= 0; op_e <= 0;
            op_d <= 1; op_f <= 1;
            start <= 0;
        end else begin
            rng_a <= {rng_a[W-2:0],rng_a[W-1]^rng_a[W-2]^rng_a[W-4]^rng_a[W-5]};
            rng_b <= {rng_b[W-2:0],rng_b[W-1]^rng_b[W-3]^rng_b[W-4]^rng_b[W-6]};
            start <= !busy && !norm_req && !start;
            if (!busy && !norm_req && !start) begin
                op_a <= rng_a; op_b <= {rng_a[W-2:0],rng_a[W-1]};
                op_c <= rng_b ^ {W{1'b1}}; op_e <= {rng_b[W-2:0],rng_b[W-1]};
                op_d <= rng_a | {{(W-1){1'b0}},1'b1};
                op_f <= rng_b | {{(W-1){1'b0}},1'b1};
            end
        end
    end
    assign uart_tx = result_a[0] ^ result_b[0] ^ result_d[0] ^ overflow ^ invalid;
endmodule
