// Three-operand unsigned GCD using two bounded Stein binary-GCD phases.
module surd_binary_gcd3 #(
    parameter integer N = 34
) (
    input wire clk, input wire rst, input wire start,
    input wire [N-1:0] value_a, input wire [N-1:0] value_b,
    input wire [N-1:0] value_d,
    output reg busy, output reg done, output reg fault,
    output reg [N-1:0] gcd_value
);
    localparam integer MAX_ITER = N*N + 3*N + 1;
    localparam integer COUNT_W = $clog2(MAX_ITER+1);
    localparam [2:0] IDLE=0, INIT_AB=1, COMMON_AB=2, LOOP_AB=3,
                     INIT_GD=4, COMMON_GD=5, LOOP_GD=6;
    reg [2:0] state;
    reg [N-1:0] u, v, original_d;
    reg [COUNT_W-1:0] iter_count;
    reg [$clog2(N+1)-1:0] scale_shift;

    always @(posedge clk) begin
        if (rst) begin
            state <= IDLE; busy <= 0; done <= 0; fault <= 0;
            gcd_value <= 0; u <= 0; v <= 0; original_d <= 0;
            scale_shift <= 0; iter_count <= 0;
        end else begin
            done <= 0; fault <= 0;
            case (state)
                IDLE: if (start) begin
                    u <= value_a; v <= value_b; original_d <= value_d;
                    scale_shift <= 0; iter_count <= 0;
                    busy <= 1; state <= INIT_AB;
                end
                INIT_AB: begin
                    iter_count <= 0; scale_shift <= 0;
                    if (u == 0) begin u <= v; v <= original_d; state <= INIT_GD; end
                    else if (v == 0) begin u <= u; v <= original_d; state <= INIT_GD; end
                    else if (!u[0] && !v[0]) state <= COMMON_AB;
                    else state <= LOOP_AB;
                end
                COMMON_AB: begin
                    if (u[0] || v[0]) state <= LOOP_AB;
                    else if (iter_count == MAX_ITER) begin
                        fault <= 1; done <= 1; busy <= 0; state <= IDLE;
                    end else begin
                        u <= u >> 1; v <= v >> 1;
                        scale_shift <= scale_shift + 1'b1;
                        iter_count <= iter_count + 1'b1;
                    end
                end
                LOOP_AB: begin
                    if (u == v) begin
                        u <= u << scale_shift; v <= original_d;
                        scale_shift <= 0; iter_count <= 0;
                        state <= INIT_GD;
                    end else if (!(|u)) begin u <= v; v <= original_d; state <= INIT_GD; end
                    else if (!(|v)) begin u <= u; v <= original_d; state <= INIT_GD; end
                    else if (iter_count == MAX_ITER) begin
                        fault <= 1; done <= 1; busy <= 0; state <= IDLE;
                    end else if (!u[0]) begin
                        u <= u >> 1; iter_count <= iter_count + 1'b1;
                    end else if (!v[0]) begin
                        v <= v >> 1; iter_count <= iter_count + 1'b1;
                    end else if (u > v) begin
                        u <= (u-v) >> 1; iter_count <= iter_count + 1'b1;
                    end else begin
                        v <= (v-u) >> 1; iter_count <= iter_count + 1'b1;
                    end
                end
                INIT_GD: begin
                    scale_shift <= 0;
                    if (u == 0) begin gcd_value <= original_d; done <= 1; busy <= 0; state <= IDLE; end
                    else if (original_d == 0) begin gcd_value <= u; done <= 1; busy <= 0; state <= IDLE; end
                    else begin
                        v <= original_d; iter_count <= 0;
                        if (!u[0] && !original_d[0]) state <= COMMON_GD;
                        else state <= LOOP_GD;
                    end
                end
                COMMON_GD: begin
                    if (u[0] || v[0]) state <= LOOP_GD;
                    else if (iter_count == MAX_ITER) begin
                        fault <= 1; done <= 1; busy <= 0; state <= IDLE;
                    end else begin
                        u <= u >> 1; v <= v >> 1;
                        scale_shift <= scale_shift + 1'b1;
                        iter_count <= iter_count + 1'b1;
                    end
                end
                LOOP_GD: begin
                    if (u == v) begin
                        gcd_value <= u << scale_shift; done <= 1; busy <= 0; state <= IDLE;
                    end else if (!(|u)) begin gcd_value <= v << scale_shift; done <= 1; busy <= 0; state <= IDLE; end
                    else if (!(|v)) begin gcd_value <= u << scale_shift; done <= 1; busy <= 0; state <= IDLE; end
                    else if (iter_count == MAX_ITER) begin
                        fault <= 1; done <= 1; busy <= 0; state <= IDLE;
                    end else if (!u[0]) begin
                        u <= u >> 1; iter_count <= iter_count + 1'b1;
                    end else if (!v[0]) begin
                        v <= v >> 1; iter_count <= iter_count + 1'b1;
                    end else if (u > v) begin
                        u <= (u-v) >> 1; iter_count <= iter_count + 1'b1;
                    end else begin
                        v <= (v-u) >> 1; iter_count <= iter_count + 1'b1;
                    end
                end
                default: begin state <= IDLE; busy <= 0; fault <= 1; done <= 1; end
            endcase
        end
    end
endmodule
