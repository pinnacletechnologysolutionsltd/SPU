// Multi-cycle [4/4] Padé evaluator (Q32 coefficients, Q32 x -> Q16 exp out)
module pade_eval_4_4(
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire signed [63:0] x_q32,
    input wire cfg_wr_en,
    input wire [2:0] cfg_wr_sel,
    input wire [2:0] cfg_wr_addr,
    input wire [63:0] cfg_wr_data,
    output reg signed [31:0] exp_q16,
    output reg done,
    output reg busy
);

    // coefficient memories (Q32)
    reg signed [63:0] num_coef [0:4];
    reg signed [63:0] den_coef [0:4];
    initial begin
        $readmemh("hardware/common/rtl/gpu/pade_num_4_4_q32.mem", num_coef);
        $readmemh("hardware/common/rtl/gpu/pade_den_4_4_q32.mem", den_coef);
    end

    // runtime write interface for coefficients (synchronous)
    always @(posedge clk) begin
        if (cfg_wr_en) begin
            if (cfg_wr_sel == 3'd1) begin
                num_coef[cfg_wr_addr] <= $signed(cfg_wr_data);
            end else if (cfg_wr_sel == 3'd2) begin
                den_coef[cfg_wr_addr] <= $signed(cfg_wr_data);
            end
        end
    end

    // FSM states (Verilog-2001)
    localparam IDLE=0, NUM0=1, NUM1=2, NUM2=3, NUM3=4, DEN0=5, DEN1=6, DEN2=7, DEN3=8, DIV=9, DONE=10;
    reg [3:0] state, next_state;

    reg signed [127:0] acc_num;
    reg signed [127:0] acc_den;
    reg signed [191:0] mult_tmp;
    reg signed [127:0] numer_reg;
    reg signed [127:0] quot_reg;
    // temporaries to compute division in one cycle
    reg signed [127:0] tmp_numer;
    reg signed [127:0] tmp_quot;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            busy <= 1'b0;
            done <= 1'b0;
            exp_q16 <= 32'sd0;
        end else begin
            state <= next_state;
            // simulation debug removed
            case (state)
                IDLE: begin
                    done <= 1'b0;
                    busy <= 1'b0;
                    if (start) begin
                        // initialize accumulators with highest-order coef
                        acc_num <= num_coef[4];
                        acc_den <= den_coef[4];
                        busy <= 1'b1;
                        next_state <= NUM0;
                        // start observed (debug removed)
                    end else next_state <= IDLE;
                end
                NUM0: begin
                    mult_tmp <= acc_num * x_q32;
                    acc_num <= (mult_tmp >> 32) + num_coef[3];
                    next_state <= NUM1;
                end
                NUM1: begin
                    mult_tmp <= acc_num * x_q32;
                    acc_num <= (mult_tmp >> 32) + num_coef[2];
                    next_state <= NUM2;
                end
                NUM2: begin
                    mult_tmp <= acc_num * x_q32;
                    acc_num <= (mult_tmp >> 32) + num_coef[1];
                    next_state <= NUM3;
                end
                NUM3: begin
                    mult_tmp <= acc_num * x_q32;
                    acc_num <= (mult_tmp >> 32) + num_coef[0];
                    // start denominator sequence
                    next_state <= DEN0;
                end
                DEN0: begin
                    mult_tmp <= acc_den * x_q32;
                    acc_den <= (mult_tmp >> 32) + den_coef[3];
                    next_state <= DEN1;
                end
                DEN1: begin
                    mult_tmp <= acc_den * x_q32;
                    acc_den <= (mult_tmp >> 32) + den_coef[2];
                    next_state <= DEN2;
                end
                DEN2: begin
                    mult_tmp <= acc_den * x_q32;
                    acc_den <= (mult_tmp >> 32) + den_coef[1];
                    next_state <= DEN3;
                end
                DEN3: begin
                    mult_tmp <= acc_den * x_q32;
                    acc_den <= (mult_tmp >> 32) + den_coef[0];
                    next_state <= DIV;
                end
                DIV: begin
                    // DIV debug removed
                    if (acc_den == 0) begin
                        exp_q16 <= 32'sd0;
                    end else begin
                        // compute and assign tmp_quot combinationally to avoid using numer_reg assigned in same cycle
                        tmp_numer = acc_num << 16;
                        tmp_quot = tmp_numer / acc_den;
                        quot_reg <= tmp_quot;
                        exp_q16 <= tmp_quot[31:0];
                    end
                    next_state <= DONE;
                end
                DONE: begin
                    done <= 1'b1;
                    busy <= 1'b0;
                    // done debug removed
                    next_state <= IDLE;
                end
                default: next_state <= IDLE;
            endcase
        end
    end
endmodule
