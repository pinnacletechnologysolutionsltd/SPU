// spu13_m31_multiplier_seq.v — Sequential M31 multiplier (area-optimised)
//
// Single 32×32 multiplier iterated 16 times with explicit DSP wait.
// ~52-cycle latency.  Intended for Tang 25K / Gowin targets.

module spu13_m31_multiplier_seq #(
    parameter DEVICE = "SIM"
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,
    input  wire [31:0]  a0, a1, a2, a3,
    input  wire [31:0]  b0, b1, b2, b3,
    output reg  [31:0]  r0, r1, r2, r3,
    output reg          done,
    output reg          busy,
    output wire         rns_error
);
    localparam [31:0] P    = 32'h7FFFFFFF;
    localparam N_PRODS     = 16;

    // ── Shared multiplier ────────────────────────────────────────────
    reg  [31:0] mul_a, mul_b;
    reg  [63:0] prod_captured;
    wire [63:0] product;

    generate
        if (DEVICE == "GW5A" || DEVICE == "GOWIN") begin : gen_gowin
            wire signed [35:0] p_raw;
            spu_gowin_multiplier #(.DEVICE(DEVICE)) u_mul (
                .clk(clk), .a(mul_a), .b(mul_b), .p(p_raw)
            );
            assign product = p_raw;
        end else begin : gen_sim
            // Combinational product — available immediately.
            // We still register it to match the Gowin pipeline timing.
            assign product = mul_a * mul_b;
        end
    endgenerate

    // ── Operands ─────────────────────────────────────────────────────
    wire [31:0] av [0:3]; wire [31:0] bv [0:3];
    assign av[0]=a0; assign av[1]=a1; assign av[2]=a2; assign av[3]=a3;
    assign bv[0]=b0; assign bv[1]=b1; assign bv[2]=b2; assign bv[3]=b3;

    // ── Schedule ROM ─────────────────────────────────────────────────
    wire [7:0] sched [0:N_PRODS-1];
    assign sched[0]  = {2'd0, 2'd0, 2'd0, 2'd0};  assign sched[1]  = {2'd0, 2'd1, 2'd1, 2'd1};
    assign sched[2]  = {2'd0, 2'd2, 2'd2, 2'd2};  assign sched[3]  = {2'd0, 2'd3, 2'd3, 2'd3};
    assign sched[4]  = {2'd1, 2'd0, 2'd1, 2'd0};  assign sched[5]  = {2'd1, 2'd1, 2'd0, 2'd0};
    assign sched[6]  = {2'd1, 2'd2, 2'd3, 2'd2};  assign sched[7]  = {2'd1, 2'd3, 2'd2, 2'd2};
    assign sched[8]  = {2'd2, 2'd0, 2'd2, 2'd0};  assign sched[9]  = {2'd2, 2'd1, 2'd3, 2'd1};
    assign sched[10] = {2'd2, 2'd2, 2'd0, 2'd0};  assign sched[11] = {2'd2, 2'd3, 2'd1, 2'd1};
    assign sched[12] = {2'd3, 2'd0, 2'd3, 2'd0};  assign sched[13] = {2'd3, 2'd1, 2'd2, 2'd0};
    assign sched[14] = {2'd3, 2'd2, 2'd1, 2'd0};  assign sched[15] = {2'd3, 2'd3, 2'd0, 2'd0};

    // ── Scale function ───────────────────────────────────────────────
    function [71:0] scale72;
        input [63:0] prod; input [1:0] sc;
        begin
            case (sc)
                2'd0: scale72 = {8'd0, prod};
                2'd1: scale72 = {7'd0, prod, 1'b0} + {8'd0, prod};
                2'd2: scale72 = {6'd0, prod, 2'b0} + {8'd0, prod};
                2'd3: scale72 = {4'd0, prod, 4'b0} - {8'd0, prod};
                default: scale72 = 72'd0;
            endcase
        end
    endfunction

    // ── Mersenne reduction ───────────────────────────────────────────
    function [31:0] m31_reduce;
        input [71:0] z;
        reg [32:0] sa;
        begin
            sa = z[30:0] + z[61:31] + {21'd0, z[71:62]};
            if (sa >= P) sa = sa - P;
            if (sa >= P) sa = sa - P;
            m31_reduce = sa[31:0];
        end
    endfunction

    // ── FSM (2 cycles per product: issue + capture) ──────────────────
    localparam S_IDLE    = 3'd0;
    localparam S_ISSUE   = 3'd1;
    localparam S_CAPTURE = 3'd2;
    localparam S_FINAL   = 3'd3;
    localparam S_DONE    = 3'd4;
    reg [2:0]  state;
    reg [4:0]  idx;
    reg [71:0] acc0, acc1, acc2, acc3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE; idx <= 5'd0;
            acc0 <= 72'd0; acc1 <= 72'd0; acc2 <= 72'd0; acc3 <= 72'd0;
            r0 <= 32'd0; r1 <= 32'd0; r2 <= 32'd0; r3 <= 32'd0;
            done <= 1'b0; busy <= 1'b0;
            mul_a <= 32'd0; mul_b <= 32'd0; prod_captured <= 64'd0;
        end else begin
            done <= 1'b0;

            case (state)
                S_IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        idx <= 5'd0; acc0 <= 72'd0; acc1 <= 72'd0; acc2 <= 72'd0; acc3 <= 72'd0;
                        busy <= 1'b1;
                        mul_a <= av[sched[0][5:4]];
                        mul_b <= bv[sched[0][3:2]];
                        state <= S_CAPTURE;
                    end
                end

                S_ISSUE: begin
                    prod_captured <= product;
                    if (idx < N_PRODS) begin
                        mul_a <= av[sched[idx][5:4]];
                        mul_b <= bv[sched[idx][3:2]];
                    end
                    state <= S_CAPTURE;
                end

                S_CAPTURE: begin
                    if (idx > 0) begin
                        case (sched[idx-1][7:6])
                            2'd0: acc0 <= acc0 + scale72(prod_captured, sched[idx-1][1:0]);
                            2'd1: acc1 <= acc1 + scale72(prod_captured, sched[idx-1][1:0]);
                            2'd2: acc2 <= acc2 + scale72(prod_captured, sched[idx-1][1:0]);
                            2'd3: acc3 <= acc3 + scale72(prod_captured, sched[idx-1][1:0]);
                        endcase
                    end
                    if (idx < N_PRODS - 1) begin
                        idx <= idx + 5'd1;
                        state <= S_ISSUE;
                    end else if (idx == N_PRODS - 1) begin
                        // Last product: need one more S_ISSUE to capture it
                        idx <= idx + 5'd1;
                        state <= S_ISSUE;
                    end else begin
                        // idx == N_PRODS: last product already accumulated above
                        state <= S_DONE;
                    end
                end

                S_FINAL: begin
                    // idx is N_PRODS. prod_captured holds the last product (from
                    // the S_ISSUE that captured the product issued for sched[N_PRODS-1]).
                    case (sched[N_PRODS-1][7:6])
                        2'd0: acc0 <= acc0 + scale72(prod_captured, sched[N_PRODS-1][1:0]);
                        2'd1: acc1 <= acc1 + scale72(prod_captured, sched[N_PRODS-1][1:0]);
                        2'd2: acc2 <= acc2 + scale72(prod_captured, sched[N_PRODS-1][1:0]);
                        2'd3: acc3 <= acc3 + scale72(prod_captured, sched[N_PRODS-1][1:0]);
                    endcase
                    state <= S_DONE;
                end

                S_DONE: begin
                    r0   <= m31_reduce(acc0);
                    r1   <= m31_reduce(acc1);
                    r2   <= m31_reduce(acc2);
                    r3   <= m31_reduce(acc3);
                    done <= 1'b1;
                    busy <= 1'b0;
                    state <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

    assign rns_error = 1'b0;

endmodule
