// Directed equivalence checks for fpga_chain_arith.vh abs_bitlen semantics.
module fpga_chain_abs_bitlen_tb;
    reg [31:0] value;
    integer errors = 0;
    integer i;
    reg [31:0] state;
    fpga_chain dut(.clk(1'b0), .rst_n(1'b0));

    function [4:0] reference_abs_bitlen;
        input [31:0] v;
        reg [31:0] magnitude;
        integer bits;
        begin
            magnitude = v[31] ? (~v + 32'd1) : v;
            bits = 0;
            while (magnitude != 0) begin
                bits = bits + 1;
                magnitude = magnitude >> 1;
            end
            reference_abs_bitlen = (bits == 0) ? 5'd1 : bits[4:0];
        end
    endfunction

    task check_value;
        input [31:0] v;
        input [4:0] expected;
        reg [4:0] got;
        begin
            got = dut.abs_bitlen(v);
            if (got !== expected) begin
                errors = errors + 1;
                $display("FAIL value=%08x expected=%0d got=%0d", v, expected, got);
            end
            if (got !== reference_abs_bitlen(v)) begin
                errors = errors + 1;
                $display("FAIL reference mismatch value=%08x expected=%0d got=%0d",
                         v, reference_abs_bitlen(v), got);
            end
        end
    endtask

    initial begin
        check_value(32'h00000000, 5'd1); // historical zero behavior
        check_value(32'h00000001, 5'd1);
        check_value(32'hffffffff, 5'd1);  // magnitude of -1
        check_value(32'h00000002, 5'd2);
        check_value(32'hfffffffe, 5'd2);  // magnitude of -2
        check_value(32'h7fffffff, 5'd31); // signed maximum
        // The 32-bit magnitude has bit length 32, which truncates to 0 in
        // the function's historical 5-bit return value.
        check_value(32'h80000000, 5'd0);

        // Exercise every magnitude bit boundary from bit 0 through bit 30,
        // on both signs, including values immediately below and above it.
        for (i = 0; i <= 30; i = i + 1) begin
            check_value(32'h00000001 << i, i + 1);
            check_value((~(32'h00000001 << i)) + 1'b1, i + 1);
            if (i > 0) begin
                check_value((32'h00000001 << i) - 1'b1, i);
                check_value((~((32'h00000001 << i) - 1'b1)) + 1'b1, i);
            end
        end

        // Deterministic representative signed words; the independent oracle
        // computes the magnitude width by repeated shifts.
        state = 32'h6d2b79f5;
        for (i = 0; i < 4096; i = i + 1) begin
            state = state ^ (state << 13);
            state = state ^ (state >> 17);
            state = state ^ (state << 5);
            check_value(state, reference_abs_bitlen(state));
        end

        if (errors == 0) $display("PASS: fpga_chain_abs_bitlen_tb");
        else $display("FAIL: fpga_chain_abs_bitlen_tb errors=%0d", errors);
        $finish;
    end
endmodule
