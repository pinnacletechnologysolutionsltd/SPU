`timescale 1ns/1ps

module spu13_rotc_feedback_tb;

    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk;

    reg start = 0;
    wire done;

    // Feedback registers
    reg [63:0] A_reg, B_reg, C_reg, D_reg;

    reg [63:0] F, G, H;
    reg [1:0] field_sel = 0;
    reg bypass_p5 = 0;
    reg bypass_p5_inv = 0;
    reg apply_div3 = 0;

    wire [63:0] A_out, B_out, C_out, D_out;

    spu13_rotor_core_tdm u_dut (
        .clk(clk), .rst_n(rst_n),
        .start(start), .done(done),
        .A_in(A_reg), .B_in(B_reg), .C_in(C_reg), .D_in(D_reg),
        .F(F), .G(G), .H(H),
        .field_sel(field_sel),
        .bypass_p5(bypass_p5),
        .bypass_p5_inv(bypass_p5_inv),
        .apply_div3(apply_div3),
        .A_out(A_out), .B_out(B_out), .C_out(C_out), .D_out(D_out)
    );

    // Track state
    reg done_seen = 0;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            done_seen <= 0;
        end else begin
            if (done) begin
                done_seen <= 1;
            end
        end
    end

    // Initial canonical coordinates (non-symmetric to detect permutation and scale errors)
    // Format: {surd_part (32 bits), rational_part (32 bits)}
    // Using Q12-like scaling or simple integers. Let's use simple integers to prevent overflow:
    // A = 1 + 1*sqrt(3)
    // B = 2 - 3*sqrt(3)
    // C = 5 + 4*sqrt(3)
    // D = -4 + 5*sqrt(3)
    // The thirds rotors require B+C+D to be divisible by 3 component-wise
    // so repeated feedback remains in the integer RTL lattice.
    localparam [63:0] A_INIT = {32'sd1,  32'sd1};
    localparam [63:0] B_INIT = {-32'sd3, 32'sd2};
    localparam [63:0] C_INIT = {32'sd4,  32'sd5};
    localparam [63:0] D_INIT = {32'sd5, -32'sd4};

    integer i, step;
    reg failed = 0;

    task run_rotation_step;
        begin
            start <= 1;
            @(posedge clk);
            start <= 0;
            done_seen <= 0;
            wait(done);
            @(posedge clk);
            #1; // Wait for propagation to registers
            A_reg = A_out;
            B_reg = B_out;
            C_reg = C_out;
            D_reg = D_out;
        end
    endtask

    initial begin
        $dumpfile("build/spu13_rotc_feedback_tb.vcd");
        $dumpvars(0, spu13_rotc_feedback_tb);

        #20 rst_n = 1;
        #20 @(posedge clk);

        // ==========================================
        // TEST 1: Angle 1 (thirds period-6 rotor)
        // Period = 6. Applying it 6 times should return to exact start.
        // We will run this for 20 complete periods (120 steps).
        // ==========================================
        $display("[ROTC FEEDBACK] Starting Test 1: Angle 1 (Period 6) - 20 periods");
        A_reg = A_INIT;
        B_reg = B_INIT;
        C_reg = C_INIT;
        D_reg = D_INIT;

        bypass_p5 = 0;
        bypass_p5_inv = 0;
        apply_div3 = 1;
        F = {32'd0, 32'd2};
        G = {32'd0, 32'd2};
        H = {32'd0, 32'hFFFFFFFF}; // -1/3 (with div3 enabled)

        for (i = 0; i < 20; i = i + 1) begin
            for (step = 0; step < 6; step = step + 1) begin
                run_rotation_step();
            end
            // After 6 steps, check if we are back to initial state
            if (A_reg !== A_INIT || B_reg !== B_INIT || C_reg !== C_INIT || D_reg !== D_INIT) begin
                $display("[ROTC FEEDBACK] FAIL: Test 1 (Angle 1) drifted at period %d", i);
                $display("  Expected: A=%h B=%h C=%h D=%h", A_INIT, B_INIT, C_INIT, D_INIT);
                $display("  Got:      A=%h B=%h C=%h D=%h", A_reg, B_reg, C_reg, D_reg);
                failed = 1;
                $finish;
            end
        end
        $display("[ROTC FEEDBACK] PASS: Test 1 (Angle 1) completed 120 steps with 0 drift.");

        // ==========================================
        // TEST 2: Angle 2 (P5 forward cycle)
        // Period = 3. Pure permutation bypass.
        // We will run this for 50 complete periods (150 steps).
        // ==========================================
        $display("[ROTC FEEDBACK] Starting Test 2: Angle 2 (Period 3) - 50 periods");
        A_reg = A_INIT;
        B_reg = B_INIT;
        C_reg = C_INIT;
        D_reg = D_INIT;

        bypass_p5 = 1;
        bypass_p5_inv = 0;
        apply_div3 = 0;
        F = 64'd0; G = 64'd0; H = 64'd0;

        for (i = 0; i < 50; i = i + 1) begin
            for (step = 0; step < 3; step = step + 1) begin
                run_rotation_step();
            end
            if (A_reg !== A_INIT || B_reg !== B_INIT || C_reg !== C_INIT || D_reg !== D_INIT) begin
                $display("[ROTC FEEDBACK] FAIL: Test 2 (Angle 2) drifted at period %d", i);
                $display("  Expected: A=%h B=%h C=%h D=%h", A_INIT, B_INIT, C_INIT, D_INIT);
                $display("  Got:      A=%h B=%h C=%h D=%h", A_reg, B_reg, C_reg, D_reg);
                failed = 1;
                $finish;
            end
        end
        $display("[ROTC FEEDBACK] PASS: Test 2 (Angle 2) completed 150 steps with 0 drift.");

        // ==========================================
        // TEST 3: Angle 3 (thirds period-2)
        // Period = 2.
        // We will run this for 50 complete periods (100 steps).
        // ==========================================
        $display("[ROTC FEEDBACK] Starting Test 3: Angle 3 (Period 2) - 50 periods");
        A_reg = A_INIT;
        B_reg = B_INIT;
        C_reg = C_INIT;
        D_reg = D_INIT;

        bypass_p5 = 0;
        bypass_p5_inv = 0;
        apply_div3 = 1;
        F = {32'd0, 32'hFFFFFFFF}; // -1
        G = {32'd0, 32'd2};
        H = {32'd0, 32'd2};

        for (i = 0; i < 50; i = i + 1) begin
            for (step = 0; step < 2; step = step + 1) begin
                run_rotation_step();
            end
            if (A_reg !== A_INIT || B_reg !== B_INIT || C_reg !== C_INIT || D_reg !== D_INIT) begin
                $display("[ROTC FEEDBACK] FAIL: Test 3 (Angle 3) drifted at period %d", i);
                $display("  Expected: A=%h B=%h C=%h D=%h", A_INIT, B_INIT, C_INIT, D_INIT);
                $display("  Got:      A=%h B=%h C=%h D=%h", A_reg, B_reg, C_reg, D_reg);
                failed = 1;
                $finish;
            end
        end
        $display("[ROTC FEEDBACK] PASS: Test 3 (Angle 3) completed 100 steps with 0 drift.");

        // ==========================================
        // TEST 4: Angle 4 (thirds period-6 inverse)
        // Period = 6.
        // We will run this for 20 complete periods (120 steps).
        // ==========================================
        $display("[ROTC FEEDBACK] Starting Test 4: Angle 4 (Period 6) - 20 periods");
        A_reg = A_INIT;
        B_reg = B_INIT;
        C_reg = C_INIT;
        D_reg = D_INIT;

        bypass_p5 = 0;
        bypass_p5_inv = 0;
        apply_div3 = 1;
        F = {32'd0, 32'd2};
        G = {32'd0, 32'hFFFFFFFF}; // -1
        H = {32'd0, 32'd2};

        for (i = 0; i < 20; i = i + 1) begin
            for (step = 0; step < 6; step = step + 1) begin
                run_rotation_step();
            end
            if (A_reg !== A_INIT || B_reg !== B_INIT || C_reg !== C_INIT || D_reg !== D_INIT) begin
                $display("[ROTC FEEDBACK] FAIL: Test 4 (Angle 4) drifted at period %d", i);
                $display("  Expected: A=%h B=%h C=%h D=%h", A_INIT, B_INIT, C_INIT, D_INIT);
                $display("  Got:      A=%h B=%h C=%h D=%h", A_reg, B_reg, C_reg, D_reg);
                failed = 1;
                $finish;
            end
        end
        $display("[ROTC FEEDBACK] PASS: Test 4 (Angle 4) completed 120 steps with 0 drift.");

        // ==========================================
        // TEST 5: Angle 5 (P5 inverse cycle)
        // Period = 3. Pure permutation bypass.
        // We will run this for 50 complete periods (150 steps).
        // ==========================================
        $display("[ROTC FEEDBACK] Starting Test 5: Angle 5 (Period 3) - 50 periods");
        A_reg = A_INIT;
        B_reg = B_INIT;
        C_reg = C_INIT;
        D_reg = D_INIT;

        bypass_p5 = 0;
        bypass_p5_inv = 1;
        apply_div3 = 0;
        F = 64'd0; G = 64'd0; H = 64'd0;

        for (i = 0; i < 50; i = i + 1) begin
            for (step = 0; step < 3; step = step + 1) begin
                run_rotation_step();
            end
            if (A_reg !== A_INIT || B_reg !== B_INIT || C_reg !== C_INIT || D_reg !== D_INIT) begin
                $display("[ROTC FEEDBACK] FAIL: Test 5 (Angle 5) drifted at period %d", i);
                $display("  Expected: A=%h B=%h C=%h D=%h", A_INIT, B_INIT, C_INIT, D_INIT);
                $display("  Got:      A=%h B=%h C=%h D=%h", A_reg, B_reg, C_reg, D_reg);
                failed = 1;
                $finish;
            end
        end
        $display("[ROTC FEEDBACK] PASS: Test 5 (Angle 5) completed 150 steps with 0 drift.");

        if (!failed) begin
            $display("PASS: All ROTC period closure feedback tests passed successfully!");
        end else begin
            $display("FAIL: Some tests failed.");
        end

        #20;
        $finish;
    end

endmodule
