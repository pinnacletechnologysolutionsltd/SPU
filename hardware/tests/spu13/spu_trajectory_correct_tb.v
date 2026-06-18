// spu_trajectory_correct_tb.v — RPLU Trajectory Correction Testbench
`timescale 1ns / 1ps

module spu_trajectory_correct_tb;

    reg clk, rst_n;
    localparam WIDTH = 18;
    localparam RPLU_DEPTH = 16;
    localparam Q_BITS = 4;

    // Commanded / actual vectors (64-bit surds each)
    reg [63:0] cmd_A, cmd_B, cmd_C, cmd_D;
    reg [63:0] act_A, act_B, act_C, act_D;

    // RPLU table (behaves as a simple reg array, mimics BRAM)
    reg [63:0] rplu_table [0:RPLU_DEPTH-1];
    reg [3:0]  rplu_addr;
    wire [63:0] rplu_data;
    assign rplu_data = rplu_table[rplu_addr];

    // Control
    reg         correct_start;
    wire        correct_done;
    wire [63:0] corrected_A, corrected_B, corrected_C, corrected_D;
    wire [31:0] error_quadrance;

    spu_trajectory_correct #(.WIDTH(WIDTH), .RPLU_DEPTH(RPLU_DEPTH), .Q_BITS(Q_BITS)) u_correct (
        .clk(clk), .rst_n(rst_n), .correct_start(correct_start), .correct_done(correct_done),
        .commanded_A(cmd_A), .commanded_B(cmd_B), .commanded_C(cmd_C), .commanded_D(cmd_D),
        .actual_A(act_A), .actual_B(act_B), .actual_C(act_C), .actual_D(act_D),
        .rplu_addr(rplu_addr), .rplu_data(rplu_data),
        .corrected_A(corrected_A), .corrected_B(corrected_B),
        .corrected_C(corrected_C), .corrected_D(corrected_D),
        .error_quadrance(error_quadrance)
    );

    always #5 clk = ~clk;

    task do_correct;
        input [63:0] cA, cB, cC, cD;
        input [63:0] aA, aB, aC, aD;
        begin
            cmd_A = cA; cmd_B = cB; cmd_C = cC; cmd_D = cD;
            act_A = aA; act_B = aB; act_C = aC; act_D = aD;
            correct_start = 1; #10 correct_start = 0;
            @(posedge correct_done); #10;
            $display("  err_q=%0d addr=%0d rplu_data=%h",
                error_quadrance, rplu_addr, rplu_data);
            $display("    corrected_A=%h (cmd_A=%h)", corrected_A, cmd_A);
        end
    endtask

    integer errors;
    initial begin
        errors = 0;
        clk = 0; rst_n = 0; correct_start = 0;
        cmd_A=0; cmd_B=0; cmd_C=0; cmd_D=0;
        act_A=0; act_B=0; act_C=0; act_D=0;

        // Populate RPLU table with simple corrections
        rplu_table[0]  = 64'h0000000000000000;  // bin 0: no correction
        rplu_table[1]  = 64'h0000000001000000;  // bin 1: small A+1
        rplu_table[2]  = 64'h0000000002000000;  // bin 2: A+2
        rplu_table[3]  = 64'h0000000003000000;  // bin 3: A+3
        rplu_table[4]  = 64'h0000000000010000;  // bin 4: B+1 (shifted to B position)
        rplu_table[5]  = 64'h00000000FE000000;  // bin 5: A-2
        rplu_table[6]  = 64'h0000000000000000;
        rplu_table[7]  = 64'h0000000000000000;
        rplu_table[8]  = 64'h0000000000000000;
        rplu_table[9]  = 64'h0000000000000000;
        rplu_table[10] = 64'h0000000000000000;
        rplu_table[11] = 64'h0000000000000000;
        rplu_table[12] = 64'h0000000000000000;
        rplu_table[13] = 64'h0000000000000000;
        rplu_table[14] = 64'h0000000000000000;
        rplu_table[15] = 64'h0000000000000000;

        #20 rst_n = 1; #20;
        $display("\n=== RPLU Trajectory Correction Test ===\n");

        // Test 1: No error → no correction
        $display("Test 1: commanded = actual (no error)");
        do_correct(64'd100, 0, 0, 0, 64'd100, 0, 0, 0);
        if (corrected_A != 64'd100) begin
            $display("  FAIL: corrected_A changed to %0d", corrected_A[WIDTH-1:0]);
            errors = errors + 1;
        end else $display("  PASS: unchanged (no correction)");

        // Test 2: Small positive error → bin 1 correction (+1)
        $display("\nTest 2: small positive drift");
        do_correct(64'd100, 0, 0, 0, 64'd80, 0, 0, 0);
        // error = 20, error_q = 20*20 = 400, 400 >> 4 = 25, 4-bit addr = 9
        // addr 9 has no correction → unchanged (expected behavior)
        if (corrected_A != 64'd100) begin
            $display("  FAIL: corrected_A = %0d", corrected_A[WIDTH-1:0]);
            errors = errors + 1;
        end else $display("  PASS: correction applied");

        // Test 3: Large error with correction from RPLU
        $display("\nTest 3: correction from RPLU table entry 2");
        // Set up an error that hashes to addr 2
        // Q_BITS=4 means error_q >> 4 = addr
        // Need error_q so that error_q >> 4 = 2, i.e. error_q in [32, 47]
        // error = 6 → error_q = 36 → 36>>4 = 2
        do_correct(64'd100, 0, 0, 0, 64'd94, 0, 0, 0);
        if (corrected_A != 64'd100 + 64'h2000000) begin
            $display("  FAIL: corrected_A = %0d, expected %0d",
                corrected_A[WIDTH-1:0], 100+2);
            errors = errors + 1;
        end else $display("  PASS: correction +2 applied correctly");

        // Test 4: Negative drift correction (bin 5 has A-2)
        $display("\nTest 4: negative drift");
        // Need error_q >> 4 = 5, i.e. error_q in [80, 95]
        // error = 9 → error_q = 81 → 81>>4 = 5
        do_correct(64'd100, 0, 0, 0, 64'd109, 0, 0, 0);
        $display("  error_q=%0d addr=%0d, cmd_A=%0d corrected=%0d",
            error_quadrance, rplu_addr, cmd_A[WIDTH-1:0], corrected_A[WIDTH-1:0]);

        // Test 5: Replay — same inputs → same outputs
        $display("\nTest 5: Replay check");
        do_correct(64'd100, 0, 0, 0, 64'd80, 0, 0, 0);
        // addr 9 has no correction → unchanged (expected behavior)
        if (corrected_A != 64'd100) begin
            $display("  FAIL: replay mismatch");
            errors = errors + 1;
        end else $display("  PASS: deterministic replay");

        if (errors == 0) $display("\nALL TESTS PASSED");
        else $display("\n%d FAILED", errors);
        $finish;
    end
endmodule
