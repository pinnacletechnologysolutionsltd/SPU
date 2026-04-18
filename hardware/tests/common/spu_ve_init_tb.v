// spu_ve_init_tb.v — Vector Equilibrium ground state tests
`timescale 1ns/1ps

module spu_ve_init_tb;

    reg  boot_done;
    wire [831:0] ve_state;
    wire         ve_valid;

    spu_ve_init dut (
        .boot_done(boot_done),
        .ve_state(ve_state),
        .ve_valid(ve_valid)
    );

    localparam [31:0] POS = 32'h0000_1000;
    localparam [31:0] NEG = 32'hFFFF_F000;
    localparam [31:0] ZRO = 32'h0000_0000;

    integer i, fail = 0;
    reg [63:0] axis;
    reg [31:0] A, B;

    initial begin
        boot_done = 0; #10;

        // T1: before boot_done, ve_valid = 0
        if (ve_valid === 1'b0)
            $display("T1 PASS: ve_valid=0 before boot");
        else begin
            $display("T1 FAIL: ve_valid should be 0");
            fail = fail + 1;
        end

        boot_done = 1; #1;

        // T2: ve_valid mirrors boot_done
        if (ve_valid === 1'b1)
            $display("T2 PASS: ve_valid=1 after boot_done");
        else begin
            $display("T2 FAIL: ve_valid should be 1");
            fail = fail + 1;
        end

        // T3: axes 0-5 are positive unity {A=+1 Q12, B=0}
        for (i = 0; i < 6; i = i + 1) begin
            axis = ve_state[i*64 +: 64];
            A = axis[63:32]; B = axis[31:0];
            if (A === POS && B === ZRO)
                $display("T3 PASS: axis %0d = +unity", i);
            else begin
                $display("T3 FAIL: axis %0d A=%08h B=%08h (exp A=%08h B=0)", i, A, B, POS);
                fail = fail + 1;
            end
        end

        // T4: axes 6-11 are negative unity {A=-1 Q12, B=0}
        for (i = 6; i < 12; i = i + 1) begin
            axis = ve_state[i*64 +: 64];
            A = axis[63:32]; B = axis[31:0];
            if (A === NEG && B === ZRO)
                $display("T4 PASS: axis %0d = -unity", i);
            else begin
                $display("T4 FAIL: axis %0d A=%08h B=%08h (exp A=%08h B=0)", i, A, B, NEG);
                fail = fail + 1;
            end
        end

        // T5: axis 12 (centre) is positive unity
        axis = ve_state[12*64 +: 64];
        A = axis[63:32]; B = axis[31:0];
        if (A === POS && B === ZRO)
            $display("T5 PASS: axis 12 centre = +unity");
        else begin
            $display("T5 FAIL: axis 12 A=%08h B=%08h", A, B);
            fail = fail + 1;
        end

        // T6: sum of outer 12 rational parts == 0 (true VE equilibrium)
        begin : sum_check
            integer sum_A;
            sum_A = 0;
            for (i = 0; i < 12; i = i + 1) begin
                axis = ve_state[i*64 +: 64];
                sum_A = sum_A + $signed(axis[63:32]);
            end
            if (sum_A === 0)
                $display("T6 PASS: SIGMA outer-12 rational = 0 (VE equilibrium)");
            else begin
                $display("T6 FAIL: SIGMA outer-12 = %0d (expected 0)", sum_A);
                fail = fail + 1;
            end
        end

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail);
        $finish;
    end

endmodule
