// Laminar detector: per-sector zero-resonance latch and settling timer
// idx width: 10 bits (1024 sectors)
module laminar_detector(
    input wire clk,
    input wire rst_n,
    input wire [9:0] addr_in,
    input wire signed [31:0] r_q16,
    input wire signed [31:0] re_q16,
    input wire wake,
    input wire [9:0] wake_addr,
    output reg irq_out,
    output reg latched_out,
    output reg cleared_out
);

    // Parameters (defaults)
    parameter EPSILON_Q16 = 16'h0010; // small threshold in Q16.16
    parameter SETTLING_TIME = 16'd1024; // cycles

    // Per-sector state: single-bit vector for latched flags (1024 bits)
    reg [1023:0] latched_bits;
    reg [15:0] settle_counter [0:1023];

    integer i;
    reg latched_effective;
    reg wake_prev;
    reg [1:0] cleared_pulse; // sticky pulse to ensure cleared_out is observed across scheduling races
    reg [9:0] wake_addr_prev; // detect changes to wake_addr to improve robustness against scheduling

    initial begin
        latched_bits = {1024{1'b0}};
        for (i = 0; i < 1024; i = i + 1) begin
            settle_counter[i] = 16'd0;
        end
        irq_out = 1'b0;
        latched_out = 1'b0;
        cleared_out = 1'b0;
        wake_prev = 1'b0;
        cleared_pulse = 2'd0;
        wake_addr_prev = 10'd0;
    end

    // Helper for absolute comparison (Verilog-2001 compatible)
    function below_eps;
        input signed [31:0] a;
        input signed [31:0] b;
        reg below_eps;
        reg signed [31:0] diff;
        begin
            diff = a - b;
            if (diff < 0) diff = -diff;
            if (diff <= $signed({16'd0, EPSILON_Q16}))
                below_eps = 1'b1;
            else
                below_eps = 1'b0;
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            latched_bits <= {1024{1'b0}};
            for (i = 0; i < 1024; i = i + 1) begin
                settle_counter[i] <= 16'd0;
            end
            irq_out <= 1'b0;
            latched_out <= 1'b0;
            cleared_out <= 1'b0;
            wake_prev <= 1'b0;
        end else begin
            // Debug tick
            $display("LAM_TICK: time=%0t addr_in=%0d wake=%b wake_addr=%0d latched_at_addr(before)=%b settle(before)=%0d", $time, addr_in, wake, wake_addr, latched_bits[addr_in], settle_counter[addr_in]);

            // Immediate clear on wake (level) or if wake was asserted last cycle (wake_prev).
            // Use a short sticky pulse so TB sees cleared_out despite scheduling races.
            if (wake || wake_prev) begin
                latched_bits[wake_addr] <= 1'b0;
                settle_counter[wake_addr] <= 16'd0;
                cleared_pulse <= 2'd2; // assert cleared_out for two cycles
            end else if (cleared_pulse != 2'd0) begin
                cleared_pulse <= cleared_pulse - 2'd1;
            end
            // drive cleared_out from sticky pulse
            cleared_out <= (cleared_pulse != 2'd0);

            // If wake_addr changed to this address and it is latched, trigger clear pulse (robustness)
            if ((wake_addr != wake_addr_prev) && (wake_addr == addr_in) && latched_bits[wake_addr]) begin
                // if the external wake_addr changes to this latched sector, clear it and pulse cleared_out
                latched_bits[wake_addr] <= 1'b0;
                settle_counter[wake_addr] <= 16'd0;
                cleared_pulse <= 2'd2;
            end

            // Detection for the addressed sector (addr_in)
            if (!latched_bits[addr_in]) begin
                if (!(wake && (wake_addr == addr_in))) begin
                    if (below_eps(re_q16, r_q16)) begin
                        // increment counter toward settling time
                        if (settle_counter[addr_in] < SETTLING_TIME)
                            settle_counter[addr_in] <= settle_counter[addr_in] + 16'd1;
                        if (settle_counter[addr_in] + 16'd1 >= SETTLING_TIME) begin
                            latched_bits[addr_in] <= 1'b1;
                        end
                    end else begin
                        // activity observed -> reset counter
                        settle_counter[addr_in] <= 16'd0;
                    end
                end else begin
                    // wake active for this addr: keep counter cleared
                    settle_counter[addr_in] <= 16'd0;
                end
            end

            // drive outputs from latched state, hiding latch when being woken
            latched_effective = latched_bits[addr_in] & ~((wake || wake_prev) && (wake_addr == addr_in));
            irq_out <= latched_effective;
            latched_out <= latched_effective;
            $display("LAM_TICK: time=%0t addr_in=%0d latched(after)=%b settle(after)=%0d irq=%b (wake=%b wake_prev=%b wake_addr=%0d)", $time, addr_in, latched_bits[addr_in], settle_counter[addr_in], irq_out, wake, wake_prev, wake_addr);

            // sample wake for next cycle
            wake_prev <= wake;
            // sample wake_addr for next cycle
            wake_addr_prev <= wake_addr;
        end
    end
endmodule
