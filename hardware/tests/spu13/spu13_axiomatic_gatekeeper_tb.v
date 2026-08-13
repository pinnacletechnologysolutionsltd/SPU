`timescale 1ns/1ps

module spu13_axiomatic_gatekeeper_tb;
    localparam [1:0] RCA0 = 2'b00;
    localparam [1:0] WKL0 = 2'b01;
    localparam [1:0] ACA0 = 2'b10;
    localparam [1:0] OFF  = 2'b11;
    localparam [1:0] NONE = 2'b00;
    localparam [1:0] OVERFLOW = 2'b01;
    localparam [1:0] FRACTIONAL = 2'b10;

    reg clk = 1'b0;
    reg rst_n = 1'b1;
    reg [1:0] axiomatic_level = RCA0;
    reg signed [17:0] quadrance_a = 18'sd0;
    reg signed [17:0] quadrance_b = 18'sd0;
    reg accum_overflow = 1'b0;
    reg pipeline_valid = 1'b0;
    wire axiomatic_fault;
    wire [1:0] fault_type;
    wire [15:0] fault_count;

    integer checks = 0;
    integer failures = 0;

    always #5 clk = ~clk;

    spu13_axiomatic_gatekeeper dut (
        .clk(clk), .rst_n(rst_n), .axiomatic_level(axiomatic_level),
        .quadrance_a(quadrance_a), .quadrance_b(quadrance_b),
        .accum_overflow(accum_overflow), .pipeline_valid(pipeline_valid),
        .axiomatic_fault(axiomatic_fault), .fault_type(fault_type),
        .fault_count(fault_count)
    );

    task check_expect;
        input exp_fault;
        input [1:0] exp_type;
        input [15:0] exp_count;
        input [255:0] label;
        begin
            checks = checks + 1;
            if (axiomatic_fault !== exp_fault || fault_type !== exp_type ||
                fault_count !== exp_count) begin
                failures = failures + 1;
                $display("FAIL %0s: fault=%b/%b count=%0d expected=%b/%b count=%0d",
                    label, axiomatic_fault, fault_type, fault_count,
                    exp_fault, exp_type, exp_count);
            end
        end
    endtask

    task tick;
        begin
            @(posedge clk);
            #1;
        end
    endtask

    initial begin
        // Reset is asynchronous and clears all state.
        #1 rst_n = 1'b0;
        #1;
        check_expect(1'b0, NONE, 16'd0, "reset");
        rst_n = 1'b1;

        // RCA0: valid integer result is clean; overflow faults.
        axiomatic_level = RCA0; pipeline_valid = 1'b1; accum_overflow = 1'b0;
        tick; check_expect(1'b0, NONE, 16'd0, "RCA0 clean");
        accum_overflow = 1'b1;
        tick; check_expect(1'b1, OVERFLOW, 16'd1, "RCA0 overflow");
        accum_overflow = 1'b0;
        tick; check_expect(1'b0, NONE, 16'd1, "RCA0 clears following cycle");

        // The fractional path is currently unreachable: integer inputs do not
        // matter because is_fractional is a constant zero in the DUT.
        quadrance_a = 18'sd1; quadrance_b = -18'sd3;
        tick; check_expect(1'b0, NONE, 16'd1, "RCA0 fractional path unreachable");

        // WKL0 also traps overflow, but tolerates the reserved fractional path.
        axiomatic_level = WKL0; accum_overflow = 1'b1;
        tick; check_expect(1'b1, OVERFLOW, 16'd2, "WKL0 overflow");
        accum_overflow = 1'b0;
        tick; check_expect(1'b0, NONE, 16'd2, "WKL0 clears and count holds");

        // ACA0 and OFF never fault on the only implemented fault input.
        axiomatic_level = ACA0; accum_overflow = 1'b1;
        tick; check_expect(1'b0, NONE, 16'd2, "ACA0 overflow suppressed");
        axiomatic_level = OFF;
        tick; check_expect(1'b0, NONE, 16'd2, "OFF overflow suppressed");

        // pipeline_valid gates every level, including RCA0.
        axiomatic_level = RCA0; pipeline_valid = 1'b0;
        tick; check_expect(1'b0, NONE, 16'd2, "invalid pipeline suppressed");

        // Consecutive faults increment once per valid overflowing result.
        pipeline_valid = 1'b1; accum_overflow = 1'b1;
        tick; check_expect(1'b1, OVERFLOW, 16'd3, "RCA0 consecutive overflow 1");
        tick; check_expect(1'b1, OVERFLOW, 16'd4, "RCA0 consecutive overflow 2");

        pipeline_valid = 1'b0; accum_overflow = 1'b0;
        tick; check_expect(1'b0, NONE, 16'd4, "final clear");

        if (failures == 0)
            $display("PASS: %0d checks (%0d failures)", checks, failures);
        else
            $display("FAIL: %0d checks (%0d failures)", checks, failures);
        $finish;
    end
endmodule
