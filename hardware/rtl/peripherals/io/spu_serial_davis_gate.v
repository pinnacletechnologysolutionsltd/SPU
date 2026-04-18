// SPU-13 Serial Davis Gate (v1.0 Ephemeralized)
// Objective: Monitor Lattice Tension using bit-serial multipliers.
// Feature: Drastically reduced LUT usage for iCE40LP1K.

module spu_serial_davis_gate #(
    parameter [31:0] TAU_Q = 32'h0400 
)(
    input  wire        clk,
    input  wire        reset,
    input  wire [15:0] a, b, c, d,
    input  wire        start,
    output wire        over_curvature,
    output wire        ready
);

    reg [1:0] axis_ptr;
    reg [31:0] q_sum;
    wire [15:0] current_axis = (axis_ptr == 0) ? a :
                               (axis_ptr == 1) ? b :
                               (axis_ptr == 2) ? c : d;
                               
    wire [31:0] product;
    wire mul_ready;
    reg  mul_start;
    
    spu_serial_multiplier u_mul (
        .clk(clk), .reset(reset),
        .a(current_axis), .b(current_axis),
        .start(mul_start),
        .product(product), .ready(mul_ready)
    );

    localparam IDLE=0, MUL=1, NEXT=2, DONE=3;
    reg [1:0] state;

    assign ready = (state == DONE);
    assign over_curvature = (q_sum > TAU_Q);

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= IDLE;
            q_sum <= 0;
            axis_ptr <= 0;
            mul_start <= 0;
        end else begin
            case (state)
                IDLE: begin
                    if (start) begin
                        q_sum <= 0;
                        axis_ptr <= 0;
                        mul_start <= 1;
                        state <= MUL;
                    end
                end
                
                MUL: begin
                    mul_start <= 0;
                    if (mul_ready) begin
                        q_sum <= q_sum + product;
                        if (axis_ptr == 3) state <= DONE;
                        else begin
                            axis_ptr <= axis_ptr + 1;
                            state <= NEXT;
                        end
                    end
                end
                
                NEXT: begin
                    mul_start <= 1;
                    state <= MUL;
                end
                
                DONE: state <= IDLE;
            endcase
        end
    end

endmodule
