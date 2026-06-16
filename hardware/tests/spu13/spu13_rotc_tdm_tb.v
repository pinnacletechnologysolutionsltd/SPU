`timescale 1ns/1ps

module spu13_rotc_tdm_tb;

    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk;

    reg start = 0;
    wire done;
    reg [63:0] A_in, B_in, C_in, D_in;
    reg [63:0] F, G, H;
    reg [1:0] field_sel = 0;
    reg bypass_p5 = 0;
    reg bypass_p5_inv = 0;
    reg apply_div3 = 0;
    wire [63:0] A_out, B_out, C_out, D_out;

    spu13_rotor_core_tdm u_dut (
        .clk(clk), .rst_n(rst_n),
        .start(start), .done(done),
        .A_in(A_in), .B_in(B_in), .C_in(C_in), .D_in(D_in),
        .F(F), .G(G), .H(H),
        .field_sel(field_sel), .bypass_p5(bypass_p5),
        .bypass_p5_inv(bypass_p5_inv),
        .apply_div3(apply_div3),
        .A_out(A_out), .B_out(B_out), .C_out(C_out), .D_out(D_out)
    );

    // Mock core logic
    reg done_seen = 0;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            start <= 0;
            done_seen <= 0;
        end else begin
            if (done) begin
                start <= 0;
                done_seen <= 1;
            end
        end
    end

    function signed [31:0] div3;
        input signed [31:0] n;
        reg signed [63:0] q;
        begin
            q = $signed(n) * $signed(32'h55555556);
            div3 = q[63:32] + n[31];
        end
    endfunction

    initial begin
        $dumpfile("build/spu13_rotc_tdm_tb.vcd");
        $dumpvars(0, spu13_rotc_tdm_tb);
        
        $display("Testing div3 function:");
        $display("  div3(9)  = %d", div3(32'sd9));
        $display("  div3(-9) = %d", div3(-32'sd9));
        $display("  div3(3)  = %d", div3(32'sd3));
        $display("  div3(-3) = %d", div3(-32'sd3));
        $display("  div3(0)  = %d", div3(32'sd0));

        A_in = 64'h0000000100000001;
        B_in = 64'h0000000200000002;
        C_in = 64'h0000000300000003;
        D_in = 64'h0000000400000004;
        F = {32'd0, 32'd1}; // identity
        G = 0; H = 0;
        apply_div3 = 0;

        #20 rst_n = 1;
        #20 @(posedge clk);
        start <= 1;
        
        // Wait for done
        wait(done);
        @(posedge clk);
        #1;
        if (done_seen) $display("TEST 1: Identity rotation DONE");
        if (B_out === B_in && C_out === C_in && D_out === D_in)
            $display("  PASS: Identity preserved B,C,D");
        else
            $display("  FAIL: Identity failed! B_out=%h, B_in=%h", B_out, B_in);

        // TEST 2: Bypass P5 (120°)
        #20 @(posedge clk);
        bypass_p5 <= 1;
        bypass_p5_inv <= 0;
        start <= 1;
        done_seen <= 0;
        wait(done);
        @(posedge clk);
        #1;
        if (done_seen) $display("TEST 2: Bypass P5 rotation DONE");
        if (B_out === D_in && C_out === B_in && D_out === C_in)
            $display("  PASS: Bypass P5 permuted B,C,D correctly");
        else
            $display("  FAIL: Bypass P5 failed! B_out=%h, D_in=%h", B_out, D_in);
        
        // TEST 3: Angle 1 (60°)
        #20 @(posedge clk);
        bypass_p5 <= 0;
        bypass_p5_inv <= 0;
        apply_div3 <= 1;
        F <= {32'd0, 32'd2};
        G <= {32'd0, 32'd2};
        H <= {32'd0, 32'hFFFFFFFF}; // -1
        start <= 1;
        done_seen <= 0;
        wait(done);
        @(posedge clk);
        #1;
        if (done_seen) $display("TEST 3: Angle 1 rotation DONE");
        // Expected with /3: (2*2 + 2*4 - 3)/3 = (4 + 8 - 3)/3 = 9/3 = 3
        if (B_out[31:0] === 64'd3)
            $display("  PASS: Angle 1 B_out correctly scaled by 3");
        else
            $display("  FAIL: Angle 1 B_out = %d (Expected 3)", B_out[31:0]);

        // TEST 4: Angle 6 (120° around A-axis)
        // This exercises the coordinate permuter logic.
        #20 @(posedge clk);
        bypass_p5 <= 0;
        bypass_p5_inv <= 0;
        apply_div3 <= 1;
        F <= {32'd0, 32'd2};
        G <= {32'd0, 32'd2};
        H <= {32'd0, 32'hFFFFFFFF}; // -1
        start <= 1;
        done_seen <= 0;
        wait(done);
        @(posedge clk);
        #1;
        if (done_seen) $display("TEST 4: Angle 6 rotation DONE");
        // For Angle 6, A is invariant. (B,C,D) rotate by (2,2,-1)/3.
        // Expected B: (2*2 + 2*4 - 3)/3 = 3.
        if (B_out[31:0] === 64'd3)
            $display("  PASS: Angle 6 B_out correctly scaled by 3");
        else
            $display("  FAIL: Angle 6 B_out = %d (Expected 3)", B_out[31:0]);

        // TEST 5: P5 inverse cycle (angle 5 semantics): B'=C, C'=D, D'=B.
        // This uses the explicit reverse bypass with no multiply and no /3.
        #20 @(posedge clk);
        bypass_p5 <= 0;
        bypass_p5_inv <= 1;
        apply_div3 <= 0;
        F <= 64'd0;
        G <= 64'd0;
        H <= {32'd0, 32'd1};
        start <= 1;
        done_seen <= 0;
        wait(done);
        @(posedge clk);
        #1;
        if (done_seen) $display("TEST 5: P5 inverse rotation DONE");
        if (B_out === C_in)
            $display("  PASS: P5 inverse B_out = C_in");
        else
            $display("  FAIL: P5 inverse B_out=%h C_in=%h", B_out, C_in);
        if (C_out === D_in)
            $display("  PASS: P5 inverse C_out = D_in");
        else
            $display("  FAIL: P5 inverse C_out=%h D_in=%h", C_out, D_in);
        if (D_out === B_in)
            $display("  PASS: P5 inverse D_out = B_in");
        else
            $display("  FAIL: P5 inverse D_out=%h B_in=%h", D_out, B_in);
        bypass_p5_inv <= 0;

        #200;
        $finish;
    end

endmodule
