`timescale 1ns / 1ps

// Full-width v2 acceptance bench. The committed oracle corpus is evaluated by
// historical v1, v2/shared-parallel, and v2/sequential implementations. Value
// equivalence is checked at each implementation's own done edge; latency is
// separately pinned per unit/singular outcome class.
module spu13_fp4_inverter_structured_tb;
    localparam MAX_WORDS = 1 + 25 * 9;

    reg clk, rst_n, start;
    reg [31:0] z0, z1, z2, z3;
    integer cycle_count;
    integer failures;
    integer vector_index;
    integer base;
    reg [31:0] golden [0:MAX_WORDS-1];

    wire [31:0] v1_inv0, v1_inv1, v1_inv2, v1_inv3;
    wire v1_done, v1_busy, v1_flags_v;
    wire v1_mult_start;
    wire [31:0] v1_a0, v1_a1, v1_a2, v1_a3;
    wire [31:0] v1_b0, v1_b1, v1_b2, v1_b3;
    wire [31:0] v1_r0, v1_r1, v1_r2, v1_r3;
    wire v1_mdone, v1_mbusy, v1_rns_error;
    wire v1_accept;

    wire [31:0] p_inv0, p_inv1, p_inv2, p_inv3;
    wire p_done, p_busy, p_flags_v;
    wire p_mult_start;
    wire [2:0] p_mult_op;
    wire [31:0] p_a0, p_a1, p_a2, p_a3;
    wire [31:0] p_b0, p_b1, p_b2, p_b3;
    wire [31:0] p_r0, p_r1, p_r2, p_r3;
    wire p_mdone, p_mbusy, p_rns_error;
    wire [4:0] p_products;
    wire p_accept;

    wire [31:0] s_inv0, s_inv1, s_inv2, s_inv3;
    wire s_done, s_busy, s_flags_v;
    wire s_mult_start;
    wire [2:0] s_mult_op;
    wire [31:0] s_a0, s_a1, s_a2, s_a3;
    wire [31:0] s_b0, s_b1, s_b2, s_b3;
    wire [31:0] s_r0, s_r1, s_r2, s_r3;
    wire s_mdone, s_mbusy, s_rns_error;
    wire [4:0] s_products;
    wire s_accept;

    integer p_unit_latency, p_singular_latency;
    integer s_unit_latency, s_singular_latency;

    always #5 clk = ~clk;
    always @(posedge clk)
        cycle_count <= cycle_count + 1;

    spu13_fp4_inverter u_v1 (
        .clk(clk), .rst_n(rst_n), .start(start),
        .z0(z0), .z1(z1), .z2(z2), .z3(z3),
        .inv0(v1_inv0), .inv1(v1_inv1), .inv2(v1_inv2), .inv3(v1_inv3),
        .done(v1_done), .busy(v1_busy), .flags_v(v1_flags_v),
        .mult_start(v1_mult_start),
        .mult_a0(v1_a0), .mult_a1(v1_a1), .mult_a2(v1_a2), .mult_a3(v1_a3),
        .mult_b0(v1_b0), .mult_b1(v1_b1), .mult_b2(v1_b2), .mult_b3(v1_b3),
        .mult_r0(v1_r0), .mult_r1(v1_r1), .mult_r2(v1_r2), .mult_r3(v1_r3),
        .mult_done(v1_mdone), .mult_busy(v1_mbusy),
        .debug_state(), .debug_start_accept(v1_accept)
    );
    spu13_m31_multiplier u_v1_multiplier (
        .clk(clk), .rst_n(rst_n), .start(v1_mult_start),
        .a0(v1_a0), .a1(v1_a1), .a2(v1_a2), .a3(v1_a3),
        .b0(v1_b0), .b1(v1_b1), .b2(v1_b2), .b3(v1_b3),
        .r0(v1_r0), .r1(v1_r1), .r2(v1_r2), .r3(v1_r3),
        .done(v1_mdone), .busy(v1_mbusy), .rns_error(v1_rns_error)
    );

    spu13_fp4_inverter_structured u_parallel (
        .clk(clk), .rst_n(rst_n), .start(start),
        .z0(z0), .z1(z1), .z2(z2), .z3(z3),
        .inv0(p_inv0), .inv1(p_inv1), .inv2(p_inv2), .inv3(p_inv3),
        .done(p_done), .busy(p_busy), .flags_v(p_flags_v),
        .mult_start(p_mult_start), .mult_op(p_mult_op),
        .mult_a0(p_a0), .mult_a1(p_a1), .mult_a2(p_a2), .mult_a3(p_a3),
        .mult_b0(p_b0), .mult_b1(p_b1), .mult_b2(p_b2), .mult_b3(p_b3),
        .mult_r0(p_r0), .mult_r1(p_r1), .mult_r2(p_r2), .mult_r3(p_r3),
        .mult_done(p_mdone), .mult_busy(p_mbusy),
        .debug_state(), .debug_start_accept(p_accept)
    );
    spu13_m31_multiplier_structured u_parallel_multiplier (
        .clk(clk), .rst_n(rst_n), .start(p_mult_start), .op(p_mult_op),
        .a0(p_a0), .a1(p_a1), .a2(p_a2), .a3(p_a3),
        .b0(p_b0), .b1(p_b1), .b2(p_b2), .b3(p_b3),
        .r0(p_r0), .r1(p_r1), .r2(p_r2), .r3(p_r3),
        .done(p_mdone), .busy(p_mbusy), .rns_error(p_rns_error),
        .logical_products(p_products)
    );

    spu13_fp4_inverter_structured u_sequential (
        .clk(clk), .rst_n(rst_n), .start(start),
        .z0(z0), .z1(z1), .z2(z2), .z3(z3),
        .inv0(s_inv0), .inv1(s_inv1), .inv2(s_inv2), .inv3(s_inv3),
        .done(s_done), .busy(s_busy), .flags_v(s_flags_v),
        .mult_start(s_mult_start), .mult_op(s_mult_op),
        .mult_a0(s_a0), .mult_a1(s_a1), .mult_a2(s_a2), .mult_a3(s_a3),
        .mult_b0(s_b0), .mult_b1(s_b1), .mult_b2(s_b2), .mult_b3(s_b3),
        .mult_r0(s_r0), .mult_r1(s_r1), .mult_r2(s_r2), .mult_r3(s_r3),
        .mult_done(s_mdone), .mult_busy(s_mbusy),
        .debug_state(), .debug_start_accept(s_accept)
    );
    spu13_m31_multiplier_seq_structured u_sequential_multiplier (
        .clk(clk), .rst_n(rst_n), .start(s_mult_start), .op(s_mult_op),
        .a0(s_a0), .a1(s_a1), .a2(s_a2), .a3(s_a3),
        .b0(s_b0), .b1(s_b1), .b2(s_b2), .b3(s_b3),
        .r0(s_r0), .r1(s_r1), .r2(s_r2), .r3(s_r3),
        .done(s_mdone), .busy(s_mbusy), .rns_error(s_rns_error),
        .logical_products(s_products)
    );

    task run_vector;
        input integer case_index;
        input integer inject_busy_start;
        integer start_cycle;
        integer elapsed;
        integer p_product_total, s_product_total;
        integer p_request_count, s_request_count;
        integer v1_latency, p_latency, s_latency;
        reg got_v1, got_p, got_s;
        reg [127:0] v1_value, p_value, s_value;
        reg v1_flag, p_flag, s_flag;
        reg expected_flag;
        begin
            base = 1 + case_index * 9;
            @(negedge clk);
            z0 = golden[base+0]; z1 = golden[base+1];
            z2 = golden[base+2]; z3 = golden[base+3];
            start = 1'b1;
            #1;
            if (!v1_accept || !p_accept || !s_accept) begin
                $display("FAIL vector=%0d start was not accepted by every inverter", case_index);
                failures = failures + 1;
            end
            @(posedge clk);
            #1;
            start_cycle = cycle_count;
            p_product_total = p_mult_start ? p_products : 0;
            s_product_total = s_mult_start ? s_products : 0;
            p_request_count = p_mult_start ? 1 : 0;
            s_request_count = s_mult_start ? 1 : 0;
            @(negedge clk);
            start = 1'b0;

            got_v1 = 0; got_p = 0; got_s = 0;
            elapsed = 0;
            while (!(got_v1 && got_p && got_s) && elapsed < 500) begin
                @(posedge clk);
                #1;
                elapsed = elapsed + 1;
                if (p_mult_start) begin
                    p_product_total = p_product_total + p_products;
                    p_request_count = p_request_count + 1;
                end
                if (s_mult_start) begin
                    s_product_total = s_product_total + s_products;
                    s_request_count = s_request_count + 1;
                end
                if (v1_rns_error || p_rns_error || s_rns_error) begin
                    $display("FAIL vector=%0d unexpected RNS error", case_index);
                    failures = failures + 1;
                end
                if (v1_done && !got_v1) begin
                    got_v1 = 1;
                    v1_latency = cycle_count - start_cycle;
                    v1_value = {v1_inv3, v1_inv2, v1_inv1, v1_inv0};
                    v1_flag = v1_flags_v;
                end
                if (p_done && !got_p) begin
                    got_p = 1;
                    p_latency = cycle_count - start_cycle;
                    p_value = {p_inv3, p_inv2, p_inv1, p_inv0};
                    p_flag = p_flags_v;
                end
                if (s_done && !got_s) begin
                    got_s = 1;
                    s_latency = cycle_count - start_cycle;
                    s_value = {s_inv3, s_inv2, s_inv1, s_inv0};
                    s_flag = s_flags_v;
                end

                if (inject_busy_start && elapsed == 3) begin
                    @(negedge clk);
                    z0 = 32'h12345678; z1 = 32'h23456789;
                    z2 = 32'h3456789A; z3 = 32'h456789AB;
                    start = 1'b1;
                end else if (inject_busy_start && elapsed == 4) begin
                    @(negedge clk);
                    start = 1'b0;
                end
            end
            start = 1'b0;

            if (!(got_v1 && got_p && got_s)) begin
                $display("FAIL vector=%0d timeout v1=%0d parallel=%0d sequential=%0d",
                         case_index, got_v1, got_p, got_s);
                failures = failures + 1;
            end else begin
                expected_flag = golden[base+8][0];
                if (v1_flag !== expected_flag || p_flag !== expected_flag ||
                    s_flag !== expected_flag) begin
                    $display("FAIL vector=%0d flags expected=%0d v1=%0d p=%0d s=%0d",
                             case_index, expected_flag, v1_flag, p_flag, s_flag);
                    failures = failures + 1;
                end
                if (p_value !== v1_value || s_value !== v1_value) begin
                    $display("FAIL vector=%0d implementation value mismatch", case_index);
                    $display("  v1=%h parallel=%h sequential=%h", v1_value, p_value, s_value);
                    failures = failures + 1;
                end
                if (!expected_flag &&
                    v1_value !== {golden[base+7], golden[base+6],
                                  golden[base+5], golden[base+4]}) begin
                    $display("FAIL vector=%0d oracle value mismatch expected=%h got=%h",
                             case_index,
                             {golden[base+7], golden[base+6], golden[base+5], golden[base+4]},
                             v1_value);
                    failures = failures + 1;
                end

                if (expected_flag) begin
                    if (v1_latency != 7) begin
                        $display("FAIL vector=%0d historical singular latency=%0d", case_index, v1_latency);
                        failures = failures + 1;
                    end
                    if (p_singular_latency < 0) p_singular_latency = p_latency;
                    if (s_singular_latency < 0) s_singular_latency = s_latency;
                    if (p_latency != p_singular_latency || s_latency != s_singular_latency) begin
                        $display("FAIL vector=%0d singular latency variance p=%0d/%0d s=%0d/%0d",
                                 case_index, p_latency, p_singular_latency,
                                 s_latency, s_singular_latency);
                        failures = failures + 1;
                    end
                    if (p_latency > 7 || s_latency > 35 ||
                        p_product_total != 8 || s_product_total != 8 ||
                        p_request_count != 2 || s_request_count != 2) begin
                        $display("FAIL vector=%0d singular gates p_lat=%0d s_lat=%0d p_prod=%0d s_prod=%0d p_req=%0d s_req=%0d",
                                 case_index, p_latency, s_latency,
                                 p_product_total, s_product_total,
                                 p_request_count, s_request_count);
                        failures = failures + 1;
                    end
                end else begin
                    if (v1_latency != 83) begin
                        $display("FAIL vector=%0d historical unit latency=%0d", case_index, v1_latency);
                        failures = failures + 1;
                    end
                    if (p_unit_latency < 0) p_unit_latency = p_latency;
                    if (s_unit_latency < 0) s_unit_latency = s_latency;
                    if (p_latency != p_unit_latency || s_latency != s_unit_latency) begin
                        $display("FAIL vector=%0d unit latency variance p=%0d/%0d s=%0d/%0d",
                                 case_index, p_latency, p_unit_latency,
                                 s_latency, s_unit_latency);
                        failures = failures + 1;
                    end
                    if (p_latency > 77 || s_latency > 160 ||
                        p_product_total != 20 || s_product_total != 20 ||
                        p_request_count != 4 || s_request_count != 4) begin
                        $display("FAIL vector=%0d unit gates p_lat=%0d s_lat=%0d p_prod=%0d s_prod=%0d p_req=%0d s_req=%0d",
                                 case_index, p_latency, s_latency,
                                 p_product_total, s_product_total,
                                 p_request_count, s_request_count);
                        failures = failures + 1;
                    end
                end
            end

            @(negedge clk);
        end
    endtask

    initial begin
        $readmemh("hardware/tests/spu13/spu13_fp4_inverter_golden.mem", golden);
        clk = 0;
        rst_n = 0;
        start = 0;
        z0 = 0; z1 = 0; z2 = 0; z3 = 0;
        cycle_count = 0;
        failures = 0;
        p_unit_latency = -1; p_singular_latency = -1;
        s_unit_latency = -1; s_singular_latency = -1;
        repeat (3) @(negedge clk);
        rst_n = 1;

        if (golden[0] !== 25) begin
            $display("FAIL golden vector count expected=25 got=%0d", golden[0]);
            failures = failures + 1;
        end

        for (vector_index = 0; vector_index < 25; vector_index = vector_index + 1)
            run_vector(vector_index, vector_index == 0);

        $display("MEASURED v2 shared-parallel: unit=%0d singular=%0d", p_unit_latency, p_singular_latency);
        $display("MEASURED v2 sequential:      unit=%0d singular=%0d", s_unit_latency, s_singular_latency);
        if (failures == 0)
            $display("PASS: spu13_fp4_inverter_structured_tb (25 vectors, own-done equivalence, deterministic latency, handshake, 20 products)");
        else
            $display("FAIL: spu13_fp4_inverter_structured_tb (%0d failures)", failures);
        $finish;
    end
endmodule
