`timescale 1ns/1ps

module spu13_isa_math_tb;

    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk;

    // Sequencer Mock Signals
    reg         instr_valid = 0;
    reg  [7:0]  instr_opcode = 0;
    reg  [7:0]  instr_r1 = 0;
    reg  [7:0]  instr_r2 = 0;
    reg  [15:0] instr_p1_a = 0;
    reg  [15:0] instr_p1_b = 0;
    wire        instr_done;
    wire        instr_stall;

    // Regfile Interface
    wire [3:0]  qrf_rd_addr;
    wire [63:0] qrf_rd_A, qrf_rd_B, qrf_rd_C, qrf_rd_D;
    wire        qrf_wr_en;
    wire [3:0]  qrf_wr_addr;
    wire [63:0] qrf_wr_A, qrf_wr_B, qrf_wr_C, qrf_wr_D;

    spu_instr_decode u_decode (
        .clk(clk), .rst_n(rst_n),
        .instr_valid(instr_valid), .instr_opcode(instr_opcode),
        .instr_r1(instr_r1), .instr_r2(instr_r2),
        .instr_p1_a(instr_p1_a), .instr_p1_b(instr_p1_b),
        .instr_done(instr_done), .instr_stall(instr_stall),
        .qrf_rd_addr(qrf_rd_addr), .qrf_rd_A(qrf_rd_A), .qrf_rd_B(qrf_rd_B), .qrf_rd_C(qrf_rd_C), .qrf_rd_D(qrf_rd_D),
        .qrf_wr_en(qrf_wr_en), .qrf_wr_addr(qrf_wr_addr), .qrf_wr_A(qrf_wr_A), .qrf_wr_B(qrf_wr_B), .qrf_wr_C(qrf_wr_C), .qrf_wr_D(qrf_wr_D),
        .rote_start(), .rote_angle(), .rote_field(), .rote_done(1'b0),
        .reg_wr_addr_0(), .reg_wr_data_0(), .reg_wr_en_0(),
        .reg_wr_addr_1(), .reg_wr_data_1(), .reg_wr_en_1(),
        .uart_strobe(), .uart_data(), .core_halted()
    );

    spu_quadray_regfile u_qrf (
        .clk(clk), .rst_n(rst_n),
        .rd_lane(qrf_rd_addr), .rd_A(qrf_rd_A), .rd_B(qrf_rd_B), .rd_C(qrf_rd_C), .rd_D(qrf_rd_D),
        .wr_en(qrf_wr_en), .wr_lane(qrf_wr_addr), .wr_A(qrf_wr_A), .wr_B(qrf_wr_B), .wr_C(qrf_wr_C), .wr_D(qrf_wr_D),
        .init_en(1'b0), .init_lane(4'd0), .init_A(64'd0), .init_B(64'd0), .init_C(64'd0), .init_D(64'd0),
        .dbg_A(), .dbg_B(), .dbg_C(), .dbg_D()
    );

    task send_instr;
        input [7:0] op;
        input [7:0] r1;
        input [7:0] r2;
        input [15:0] p1a;
        input [15:0] p1b;
        begin
            @(posedge clk);
            instr_opcode <= op;
            instr_r1 <= r1;
            instr_r2 <= r2;
            instr_p1_a <= p1a;
            instr_p1_b <= p1b;
            instr_valid <= 1;
            @(posedge clk);
            while (instr_stall) @(posedge clk);
            instr_valid <= 0;
            // Clear fields to avoid latching X from previous undefined state
            instr_opcode <= 0;
            instr_r1 <= 0;
            instr_r2 <= 0;
            instr_p1_a <= 0;
            instr_p1_b <= 0;
            while (!instr_done) @(posedge clk);
            #1;
        end
    endtask

    initial begin
        $dumpfile("build/spu13_isa_math_tb.vcd");
        $dumpvars(0, spu13_isa_math_tb);

        #20 rst_n = 1;
        #20;

        // TEST 1: QLDI QR1, (10, 20, 30, 40)
        $display("TEST 1: QLDI QR1");
        send_instr(8'h1D, 8'd1, 8'd0, 16'h0A14, 16'h1E28); 
        // Verification: check QR1 components
        if (u_qrf.reg_A[1][31:0] === 32'sd10 && u_qrf.reg_B[1][31:0] === 32'sd20 && 
            u_qrf.reg_C[1][31:0] === 32'sd30 && u_qrf.reg_D[1][31:0] === 32'sd40)
            $display("  PASS: QLDI correctly loaded QR1");
        else
            $display("  FAIL: QLDI failed QR1! A=%d B=%d C=%d D=%d", u_qrf.reg_A[1][31:0], u_qrf.reg_B[1][31:0], u_qrf.reg_C[1][31:0], u_qrf.reg_D[1][31:0]);

        // TEST 2: QLDI QR2, (1, 1, 1, 1)
        $display("TEST 2: QLDI QR2");
        send_instr(8'h1D, 8'd2, 8'd0, 16'h0101, 16'h0101);

        // TEST 3: QSUB QR3, QR1, QR2 (QR3 = QR1 - QR2)
        $display("TEST 3: QSUB QR3, QR1, QR2");
        // QSUB QRd, QRa, QRb -> r1=3, r2=1, p1_b=2
        send_instr(8'h1B, 8'd3, 8'd1, 16'h0000, 16'h0002);
        
        // Expected: (9, 19, 29, 39)
        if (u_qrf.reg_A[3][31:0] === 32'sd9 && u_qrf.reg_B[3][31:0] === 32'sd19 && 
            u_qrf.reg_C[3][31:0] === 32'sd29 && u_qrf.reg_D[3][31:0] === 32'sd39)
            $display("  PASS: QSUB result correct");
        else
            $display("  FAIL: QSUB failed! A=%d", u_qrf.reg_A[3][31:0]);

        // TEST 4: DELTA QR4, Q1=3, Q2=4, steps=10
        $display("TEST 4: DELTA QR4, Q1=3, Q2=4, steps=10");
        send_instr(8'h1E, 8'd4, 8'd10, 16'd3, 16'd4);
        
        // Expected A=7 (q_sum), B=0 (right-triangle endpoint), C=10 (steps)
        if (u_qrf.reg_A[4][31:0] === 32'sd7 && u_qrf.reg_B[4][31:0] === 32'sd0 && u_qrf.reg_C[4][31:0] === 32'sd10)
            $display("  PASS: DELTA result correct");
        else
            $display("  FAIL: DELTA failed! A=%d C=%d", u_qrf.reg_A[4][31:0], u_qrf.reg_C[4][31:0]);

        #100;
        $finish;
    end

endmodule
