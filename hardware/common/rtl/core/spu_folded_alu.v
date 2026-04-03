// SPU-13 Folded Tetrahedral ALU (v1.0)
// Target: iCE40LP1K (Nano Sentinel)
// Objective: Resource Folding via Time-Division Multiplexing (TDM).
// Logic: One high-speed circuit cycling through {a,b,c,d} at 48 MHz.

module spu_folded_alu (
    input  wire         clk_48mhz, // Master high-speed clock
    input  wire         reset,
    input  wire [127:0] reg_in,    // 4D Quadray Input
    input  wire [2:0]   opcode,
    output reg  [127:0] reg_out,   // 4D Quadray Output
    output reg          done
);

    // TDM Counter (Cycles 00->01->10->11 for A,B,C,D)
    reg [1:0] axis_ptr;
    
    // Internal Accumulators
    reg signed [31:0] acc_a, acc_b, acc_c, acc_d;
    
    // The "Single" ALU Logic
    wire signed [31:0] current_axis_in = (axis_ptr == 2'b00) ? reg_in[31:0] :
                                         (axis_ptr == 2'b01) ? reg_in[63:32] :
                                         (axis_ptr == 2'b10) ? reg_in[95:64] :
                                                               reg_in[127:96];
                                                               
    reg signed [31:0] result_pipe;

    always @(posedge clk_48mhz or posedge reset) begin
        if (reset) begin
            axis_ptr <= 0;
            acc_a <= 0; acc_b <= 0; acc_c <= 0; acc_d <= 0;
            done <= 0;
        end else begin
            case (axis_ptr)
                2'b00: begin acc_a <= current_axis_in + 32'h100; axis_ptr <= 2'b01; done <= 0; end
                2'b01: begin acc_b <= current_axis_in + 32'h100; axis_ptr <= 2'b10; end
                2'b10: begin acc_c <= current_axis_in + 32'h100; axis_ptr <= 2'b11; end
                2'b11: begin 
                    acc_d <= current_axis_in + 32'h100; 
                    axis_ptr <= 2'b00; 
                    reg_out <= {acc_d + 32'h100, acc_c, acc_b, acc_a}; 
                    done <= 1; 
                end
            endcase
        end
    end

endmodule
