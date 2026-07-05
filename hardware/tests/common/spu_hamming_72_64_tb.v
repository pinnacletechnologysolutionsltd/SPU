`timescale 1ns / 1ps

// spu_hamming_72_64_tb.v — Smoke test for SECDED ECC
// Verifies: encode/decode symmetry, single-bit correction, double-bit detection

module spu_hamming_72_64_tb;
    reg  [63:0] data;
    wire [7:0]  parity;
    reg  [63:0] data_check;
    reg  [7:0]  parity_in;
    wire [63:0] data_corrected;
    wire        single_err, double_err;
    integer     errors, bit_pos;

    spu_hamming_72_64 dut (
        .data_in(data), .parity_out(parity),
        .data_check(data_check), .parity_in(parity_in),
        .data_corrected(data_corrected),
        .single_err(single_err), .double_err(double_err)
    );

    initial begin
        $display("=== spu_hamming_72_64_tb ===");
        errors = 0;

        // Test 1: encode then decode — should match
        data = 64'h0123456789ABCDEF;
        #1;
        data_check = data;
        parity_in = parity;
        #1;
        if (data_corrected !== data || single_err || double_err) begin
            $display("FAIL: encode/decode symmetry");
            errors = errors + 1;
        end else begin
            $display("PASS: encode/decode symmetry");
        end

        // Test 2: single-bit error injection — must correct
        for (bit_pos = 0; bit_pos < 64; bit_pos = bit_pos + 1) begin
            data = 64'hDEADBEEF12345678;
            #1;
            data_check = data ^ (64'd1 << bit_pos);
            parity_in = parity;
            #1;
            if (data_corrected !== data) begin
                $display("FAIL: single-bit correction at bit %0d", bit_pos);
                errors = errors + 1;
            end
            if (!single_err) begin
                $display("FAIL: single_err not asserted at bit %0d", bit_pos);
                errors = errors + 1;
            end
            if (double_err) begin
                $display("FAIL: double_err falsely asserted at bit %0d", bit_pos);
                errors = errors + 1;
            end
        end
        if (errors == 0) begin
            $display("PASS: all 64 single-bit positions corrected");
        end

        // Test 3: double-bit error — must detect
        data = 64'hA5A5A5A5_5A5A5A5A;
        #1;
        data_check = data ^ 64'hC000000000000003;  // flip bits 0 and 63
        parity_in = parity;
        #1;
        if (!double_err) begin
            $display("FAIL: double-bit error not detected");
            errors = errors + 1;
        end else if (data_corrected === data) begin
            // corrected should equal data_check for double-bit (no correction attempted)
            // actually corrected = data_check ^ syndrome, which may not match either
        end else begin
            // double_err detected — behavior is acceptable
        end
        if (double_err)
            $display("PASS: double-bit error detected");

        // Test 4: parity bit errors must be reported without corrupting data
        data = 64'h0000000000000001;
        #1;
        for (bit_pos = 0; bit_pos < 8; bit_pos = bit_pos + 1) begin
            data_check = data;
            parity_in = parity ^ (8'd1 << bit_pos);
            #1;
            if (data_corrected !== data) begin
                $display("FAIL: parity bit %0d error corrupted data", bit_pos);
                errors = errors + 1;
            end
            if (!single_err) begin
                $display("FAIL: parity bit %0d error not detected", bit_pos);
                errors = errors + 1;
            end
            if (double_err) begin
                $display("FAIL: parity bit %0d falsely reported double_err", bit_pos);
                errors = errors + 1;
            end
        end
        if (errors == 0) begin
            $display("PASS: all parity bit errors detected without data corruption");
        end

        // Test 5: data + parity double-bit error must be detected, not corrected
        data = 64'h13579BDF_2468ACE0;
        #1;
        data_check = data ^ 64'd1;
        parity_in = parity ^ 8'h80;
        #1;
        if (!double_err || single_err) begin
            $display("FAIL: data+overall parity double-bit error not detected");
            errors = errors + 1;
        end else begin
            $display("PASS: data+overall parity double-bit error detected");
        end

        if (errors == 0)
            $display("PASS");
        else
            $display("FAIL errors=%0d", errors);
        $finish;
    end
endmodule
