// spu13_su3_sidecar_tb.v -- SPI-instruction protocol test for SU3 sidecar.
//
// Starts the SU3 stream, loads dense A and B matrices as 32-bit chunks, then
// reads one selected 256-bit result element back through QR commit A/B/C/D.

`timescale 1ns / 1ps

module spu13_su3_sidecar_tb;
    localparam [7:0] OP_SU3_LOAD_A = 8'hE8;
    localparam [7:0] OP_SU3_LOAD_B = 8'hE9;
    localparam [7:0] OP_SU3_START  = 8'hEA;
    localparam [7:0] OP_SU3_READ   = 8'hEB;

    reg clk, rst_n;
    reg inst_valid;
    reg [63:0] inst_word;
    wire inst_claimed;
    wire busy;
    wire error;
    wire qr_commit_valid;
    wire [3:0] qr_commit_lane;
    wire [63:0] qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D;
    wire shared_mult_start;
    wire [31:0] shared_mult_a0, shared_mult_a1, shared_mult_a2, shared_mult_a3;
    wire [31:0] shared_mult_b0, shared_mult_b1, shared_mult_b2, shared_mult_b3;
    wire [31:0] shared_mult_r0, shared_mult_r1, shared_mult_r2, shared_mult_r3;
    wire shared_mult_done, shared_mult_busy;

    spu13_m31_multiplier u_ext_mult (
        .clk(clk),
        .rst_n(rst_n),
        .start(shared_mult_start),
        .a0(shared_mult_a0),
        .a1(shared_mult_a1),
        .a2(shared_mult_a2),
        .a3(shared_mult_a3),
        .b0(shared_mult_b0),
        .b1(shared_mult_b1),
        .b2(shared_mult_b2),
        .b3(shared_mult_b3),
        .r0(shared_mult_r0),
        .r1(shared_mult_r1),
        .r2(shared_mult_r2),
        .r3(shared_mult_r3),
        .done(shared_mult_done),
        .busy(shared_mult_busy),
        .rns_error()
    );

    spu13_su3_sidecar #(
        .EXTERNAL_MULT(1)
    ) uut (
        .clk(clk),
        .rst_n(rst_n),
        .inst_valid(inst_valid),
        .inst_word(inst_word),
        .inst_claimed(inst_claimed),
        .busy(busy),
        .error(error),
        .qr_commit_valid(qr_commit_valid),
        .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A),
        .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C),
        .qr_commit_D(qr_commit_D),
        .debug_status(),
        .debug_state(),
        .shared_mult_start(shared_mult_start),
        .shared_mult_a0(shared_mult_a0),
        .shared_mult_a1(shared_mult_a1),
        .shared_mult_a2(shared_mult_a2),
        .shared_mult_a3(shared_mult_a3),
        .shared_mult_b0(shared_mult_b0),
        .shared_mult_b1(shared_mult_b1),
        .shared_mult_b2(shared_mult_b2),
        .shared_mult_b3(shared_mult_b3),
        .shared_mult_r0(shared_mult_r0),
        .shared_mult_r1(shared_mult_r1),
        .shared_mult_r2(shared_mult_r2),
        .shared_mult_r3(shared_mult_r3),
        .shared_mult_done(shared_mult_done),
        .shared_mult_busy(shared_mult_busy)
    );

    always #5 clk = ~clk;

    integer errors;

    function [255:0] dense_a_elem(input integer idx);
        begin
            case (idx)
                0: dense_a_elem = 256'h000000190000001700000013000000110000000a000000080000000600000004;
                1: dense_a_elem = 256'h0000002f0000002d00000029000000270000001500000013000000110000000f;
                2: dense_a_elem = 256'h00000045000000430000003f0000003d000000200000001e0000001c0000001a;
                3: dense_a_elem = 256'h00000023000000210000001d0000001b0000000f0000000d0000000b00000009;
                4: dense_a_elem = 256'h000000390000003700000033000000310000001a000000180000001600000014;
                5: dense_a_elem = 256'h0000004f0000004d00000049000000470000002500000023000000210000001f;
                6: dense_a_elem = 256'h0000002d0000002b00000027000000250000001400000012000000100000000e;
                7: dense_a_elem = 256'h00000043000000410000003d0000003b0000001f0000001d0000001b00000019;
                default: dense_a_elem = 256'h000000590000005700000053000000510000002a000000280000002600000024;
            endcase
        end
    endfunction

    function [255:0] dense_b_elem(input integer idx);
        begin
            case (idx)
                0: dense_b_elem = 256'h0000004d0000004b00000047000000450000002400000022000000200000001e;
                1: dense_b_elem = 256'h0000006700000065000000610000005f000000310000002f0000002d0000002b;
                2: dense_b_elem = 256'h000000810000007f0000007b000000790000003e0000003c0000003a00000038;
                3: dense_b_elem = 256'h0000005b0000005900000055000000530000002b000000290000002700000025;
                4: dense_b_elem = 256'h00000075000000730000006f0000006d00000038000000360000003400000032;
                5: dense_b_elem = 256'h0000008f0000008d00000089000000870000004500000043000000410000003f;
                6: dense_b_elem = 256'h0000006900000067000000630000006100000032000000300000002e0000002c;
                7: dense_b_elem = 256'h00000083000000810000007d0000007b0000003f0000003d0000003b00000039;
                default: dense_b_elem = 256'h0000009d0000009b00000097000000950000004c0000004a0000004800000046;
            endcase
        end
    endfunction

    function [255:0] dense_expected(input integer idx);
        begin
            case (idx)
                0: dense_expected = 256'h0000a30000014f3000021510000446a07fff6b677ffed36f7ffe271f7ffc43ef;
                1: dense_expected = 256'h0000d3240001b14c0002ae0400057e047fff41f77ffe7ff37ffda5ef7ffb3fbb;
                2: dense_expected = 256'h0001034800021368000346f80006b5687fff18877ffe2c777ffd24bf7ffa3b87;
                3: dense_expected = 256'h0000ca2400019e2c00028dc400053a247fff4bff7ffe94637ffdc7077ffb830b;
                4: dense_expected = 256'h00010678000218a800034b480006baa87fff196b7ffe2e9f7ffd2a6b7ffa47ff;
                5: dense_expected = 256'h000142cc00029324000408cc00083b2c7ffee6d77ffdc8db7ffc8dcf7ff90cf3;
                6: dense_expected = 256'h0000f1480001ed280003067800062da87fff2c977ffe55577ffd66ef7ffac227;
                7: dense_expected = 256'h000139cc000280040003e88c0007f74c7ffef0df7ffddd4b7ffcaee77ff95043;
                default: dense_expected = 256'h00018250000312e00004caa00009c0f07ffeb5277ffd653f7ffbf6df7ff7de5f;
            endcase
        end
    endfunction

    task send_inst(input [63:0] word);
        begin
            @(negedge clk);
            inst_word = word;
            inst_valid = 1'b1;
            @(posedge clk); #1;
            if (!inst_claimed) begin
                $display("FAIL: instruction %h was not claimed", word);
                errors = errors + 1;
            end
            @(negedge clk);
            inst_valid = 1'b0;
            inst_word = 64'd0;
        end
    endtask

    task load_elem(input [7:0] op, input integer elem, input [255:0] value);
        integer word_idx;
        reg [31:0] word_data;
        begin
            for (word_idx = 0; word_idx < 8; word_idx = word_idx + 1) begin
                word_data = value[word_idx * 32 +: 32];
                send_inst({op, elem[3:0], 1'b0, word_idx[2:0], 16'd0, word_data});
            end
        end
    endtask

    task read_and_check(input integer elem, input [3:0] lane);
        reg [255:0] got;
        reg [255:0] exp;
        begin
            send_inst({OP_SU3_READ, lane, elem[3:0], 48'd0});
            if (!qr_commit_valid) begin
                $display("FAIL: read elem %0d did not emit QR commit", elem);
                errors = errors + 1;
            end
            if (qr_commit_lane != lane) begin
                $display("FAIL: read elem %0d lane expected %0d got %0d", elem, lane, qr_commit_lane);
                errors = errors + 1;
            end
            got = {qr_commit_D, qr_commit_C, qr_commit_B, qr_commit_A};
            exp = dense_expected(elem);
            if (got != exp) begin
                $display("FAIL: read elem %0d expected %h got %h", elem, exp, got);
                errors = errors + 1;
            end
        end
    endtask

    task start_and_wait(input integer elem);
        integer wait_guard;
        integer matrix_idx;
        begin
            send_inst({OP_SU3_START, 4'd0, elem[3:0], 48'd0});
            for (matrix_idx = 0; matrix_idx < 9; matrix_idx = matrix_idx + 1)
                load_elem(OP_SU3_LOAD_A, matrix_idx, dense_a_elem(matrix_idx));
            for (matrix_idx = 0; matrix_idx < 9; matrix_idx = matrix_idx + 1)
                load_elem(OP_SU3_LOAD_B, matrix_idx, dense_b_elem(matrix_idx));
            wait_guard = 0;
            while (busy && wait_guard < 4000) begin
                @(posedge clk);
                wait_guard = wait_guard + 1;
            end
            if (busy) begin
                $display("FAIL: SU3 sidecar timed out waiting for multiply elem %0d", elem);
                errors = errors + 1;
            end
            if (error) begin
                $display("FAIL: SU3 sidecar error asserted for elem %0d", elem);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        $display("=== SU3 Sidecar Protocol Testbench ===");
        errors = 0;
        clk = 1'b0;
        rst_n = 1'b0;
        inst_valid = 1'b0;
        inst_word = 64'd0;
        #25 rst_n = 1'b1;

        start_and_wait(0);
        read_and_check(0, 4'd2);
        start_and_wait(4);
        read_and_check(4, 4'd5);
        start_and_wait(8);
        read_and_check(8, 4'd8);

        if (errors == 0)
            $display("PASS: spu13_su3_sidecar_tb -- 0 errors");
        else
            $display("FAIL: spu13_su3_sidecar_tb -- %0d error(s)", errors);
        $finish;
    end
endmodule
