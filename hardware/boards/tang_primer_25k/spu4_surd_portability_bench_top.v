// Isolated W-bit Surd multiplier + shared normalizer mapping wrapper.
// This is a synthesis workload; it does not change the SPU-4 core or ABI.
module spu4_surd_portability_bench_top #(
    parameter integer W = 16,
    parameter integer LANES = 1
) (
    input wire sys_clk,
    output wire [2:0] led,
    output wire uart_tx
);
    reg [7:0] reset_count = 0;
    wire rst = reset_count != 8'hff;
    always @(posedge sys_clk) if (rst) reset_count <= reset_count + 1'b1;

    reg [W-1:0] rng_a, rng_b;
    reg signed [W-1:0] op_a, op_b, op_c, op_e;
    reg [W-1:0] op_d, op_f;
    reg start;
    wire signed [W-1:0] result_a, result_b;
    wire [W-1:0] result_d;
    wire busy, done, overflow, invalid, norm_req;
    wire signed [2*W+1:0] raw_a, raw_b, norm_a, norm_b;
    wire [2*W-1:0] raw_d;
    wire [2*W+1:0] norm_d;
    wire norm_busy, norm_done, norm_valid, norm_invalid, norm_fault, norm_fits;
    wire norm_start = norm_req && !norm_busy && !norm_valid;

    surd_smul_unit #(.W(W),.LANES(LANES)) multiplier (
        .clk(sys_clk),.rst(rst),.start(start),
        .a_in(op_a),.b_in(op_b),.d_in(op_d),.c_in(op_c),.e_in(op_e),.f_in(op_f),
        .dst_a(result_a),.dst_b(result_b),.dst_d(result_d),
        .result_a(result_a),.result_b(result_b),.result_d(result_d),
        .busy(busy),.done(done),.overflow(overflow),.invalid(invalid),
        .norm_req(norm_req),.raw_a(raw_a),.raw_b(raw_b),.raw_d(raw_d),
        .norm_valid(norm_valid),.norm_a(norm_a),.norm_b(norm_b),.norm_d(norm_d[2*W-1:0])
    );

    surd_normalize_unit #(.W(W)) normalizer (
        .clk(sys_clk),.rst(rst),.start(norm_start),
        .value_a(raw_a),.value_b(raw_b),.value_d(raw_d),
        .busy(norm_busy),.done(norm_done),.valid(norm_valid),
        .invalid(norm_invalid),.fault(norm_fault),.fits_W(norm_fits),
        .norm_a(norm_a),.norm_b(norm_b),.norm_d(norm_d)
    );

    always @(posedge sys_clk) begin
        if (rst) begin
            rng_a <= {{(W-1){1'b0}},1'b1};
            rng_b <= {{(W-2){1'b0}},2'b11};
            op_a <= 0; op_b <= 0; op_c <= 0; op_e <= 0;
            op_d <= 1; op_f <= 1; start <= 0;
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

    assign led = {overflow, norm_req, done};
    assign uart_tx = result_a[0] ^ result_b[0] ^ result_d[0] ^ overflow ^ invalid ^ norm_fault;
endmodule
