`timescale 1ns/1ps

// Fault/poison proof for the batch inverter.
//
// A zero-divisor in the batch product must not poison the unit lanes: the
// singular lane is reported with FLAGS.V and a zero result, while each unit
// lane receives its independent inverse.  The all-singular case must report
// every lane and terminate without emitting a non-singular result.
module spu13_batch_inverter_poison_tb #(
    parameter USE_STRUCTURED_INVERTER = 1,
    parameter STRUCTURED_INVERTER_SEQUENTIAL = 0
);
    reg clk = 0, rst_n = 0, start = 0, d_valid = 0, d_last = 0;
    reg [4:0] batch_size;
    reg [31:0] d0, d1, d2, d3;
    wire [31:0] inv0, inv1, inv2, inv3;
    wire inv_valid, inv_singular, done, busy;
    wire [3:0] debug_state;
    integer errors, timeout, out_count;
    reg [1:0] seen_singular;
    reg [31:0] seen_inv0 [0:1];

    always #5 clk = ~clk;

    spu13_batch_inverter #(
        .MAX_BATCH(16),
        .USE_STRUCTURED_INVERTER(USE_STRUCTURED_INVERTER),
        .STRUCTURED_INVERTER_SEQUENTIAL(STRUCTURED_INVERTER_SEQUENTIAL)
    ) dut (
        .clk(clk), .rst_n(rst_n), .start(start), .batch_size(batch_size),
        .d0(d0), .d1(d1), .d2(d2), .d3(d3),
        .d_valid(d_valid), .d_last(d_last),
        .inv0(inv0), .inv1(inv1), .inv2(inv2), .inv3(inv3),
        .inv_valid(inv_valid), .inv_singular(inv_singular),
        .done(done), .busy(busy), .debug_state(debug_state)
    );

    always @(posedge clk) begin
        if (inv_valid) begin
            if (out_count < 2) begin
                seen_singular[out_count] <= inv_singular;
                seen_inv0[out_count] <= inv0;
            end
            out_count <= out_count + 1;
        end
    end

    task send_lane;
        input [31:0] a0;
        input last;
        begin
            d0 = a0; d1 = 0; d2 = 0; d3 = 0;
            d_valid = 1; d_last = last;
            #10;
            d_valid = 0; d_last = 0;
        end
    endtask

    task send_zero_divisor;
        input last;
        begin
            d0 = 32'h5311DB4D; d1 = 0; d2 = 0; d3 = 1;
            d_valid = 1; d_last = last;
            #10;
            d_valid = 0; d_last = 0;
        end
    endtask

    task wait_done;
        begin
            timeout = 0;
            while (!done && timeout < 50000) begin
                @(posedge clk); timeout = timeout + 1;
            end
            if (timeout >= 50000) begin
                $display("FAIL: timeout state=%0d", debug_state);
                errors = errors + 1;
            end
            repeat (3) @(posedge clk);
        end
    endtask

    initial begin
        errors = 0; out_count = 0; seen_singular = 0;
        batch_size = 0; d0 = 0; d1 = 0; d2 = 0; d3 = 0;
        #20 rst_n = 1; #20;

        // sqrt(15) + sqrt(15)-basis element is a zero divisor in A31.
        // Mixed with scalar units 2 and 3, it is a direct poison test.
        batch_size = 3; start = 1; #10 start = 0;
        send_lane(32'd2, 0);
        d0 = 32'h5311DB4D; d1 = 0; d2 = 0; d3 = 1;
        d_valid = 1; d_last = 0; #10; d_valid = 0; d_last = 0;
        send_lane(32'd3, 1);
        wait_done;
        if (out_count != 3) begin
            $display("FAIL: mixed batch emitted %0d lanes, expected 3", out_count);
            errors = errors + 1;
        end
        if (seen_singular[0] || seen_inv0[0] !== 32'h40000000) begin
            $display("FAIL: unit lane 0 poisoned: V=%b inv=%h", seen_singular[0], seen_inv0[0]);
            errors = errors + 1;
        end
        if (!seen_singular[1] || seen_inv0[1] !== 0) begin
            $display("FAIL: singular lane not poisoned: V=%b inv=%h", seen_singular[1], seen_inv0[1]);
            errors = errors + 1;
        end

        // All-singular batch: every output must carry FLAGS.V.
        out_count = 0; seen_singular = 0;
        batch_size = 2; start = 1; #10 start = 0;
        send_zero_divisor(0);
        send_zero_divisor(1);
        wait_done;
        if (out_count != 2 || !seen_singular[0] || !seen_singular[1]) begin
            $display("FAIL: all-singular poison V=%b%b count=%0d", seen_singular[1], seen_singular[0], out_count);
            errors = errors + 1;
        end

        if (errors == 0)
            $display("BATCH_POISON: PASS mixed/all-singular isolation");
        else
            $display("BATCH_POISON: FAIL errors=%0d", errors);
        $finish;
    end
endmodule
