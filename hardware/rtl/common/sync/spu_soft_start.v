// SPU Soft Start Controller (v1.0)
// Hardened for "Laminar Purity" (Zero-Branch Logic).
// Objective: Fibonacci-stepped intensity ramp for Sovereign Blooming.

module spu_soft_start (
    input  wire       clk,
    input  wire       rst_n, // Sovereign-standard active-low reset
    output reg [7:0]  bloom_intensity,
    output wire       bloom_complete
);

    reg [15:0] timer;
    reg [2:0]  fib_idx; // 0..7 for the 8 Fibonacci steps
    
    // Fibonacci sequence for stepping (8, 13, 21, 34, 55, 89, 144, 233)
    wire [15:0] fib_threshold = 
        ({16{fib_idx == 3'd0}} & 16'd8)   |
        ({16{fib_idx == 3'd1}} & 16'd13)  |
        ({16{fib_idx == 3'd2}} & 16'd21)  |
        ({16{fib_idx == 3'd3}} & 16'd34)  |
        ({16{fib_idx == 3'd4}} & 16'd55)  |
        ({16{fib_idx == 3'd5}} & 16'd89)  |
        ({16{fib_idx == 3'd6}} & 16'd144) |
        ({16{fib_idx == 3'd7}} & 16'd233);

    wire is_max;
    assign is_max = (bloom_intensity == 8'hFF);
    wire step_reached;
    assign step_reached = (timer >= fib_threshold);
    
    // Next-state logic (Laminar Muxes)
    wire [15:0] next_timer = 
        ({16{is_max}} & timer) |
        ({16{!is_max && step_reached}} & 16'h0) |
        ({16{!is_max && !step_reached}} & (timer + 16'h1));
        
    wire [7:0] next_intensity = 
        ({8{is_max}} & 8'hFF) |
        ({8{!is_max && step_reached}} & (bloom_intensity + 8'h1)) |
        ({8{!is_max && !step_reached}} & bloom_intensity);
        
    wire [2:0] next_fib_idx = 
        ({3{is_max}} & fib_idx) |
        ({3{!is_max && step_reached}} & (fib_idx + 3'h1)) |
        ({3{!is_max && !step_reached}} & fib_idx);

    always @(posedge clk) begin
        if (!rst_n) begin
            bloom_intensity <= 8'h00;
            timer <= 16'h0;
            fib_idx <= 3'h0;
        end else begin
            bloom_intensity <= next_intensity;
            timer <= next_timer;
            fib_idx <= next_fib_idx;
        end
    end

    assign bloom_complete = is_max;

endmodule
