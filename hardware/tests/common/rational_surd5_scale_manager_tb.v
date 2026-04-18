`timescale 1ns/1ps

module rational_surd5_scale_manager_tb();
    reg clk = 0;
    reg rst_n = 0;
    reg write_en = 0;
    reg [3:0] write_idx = 0;
    reg [3:0] write_shift = 0;
    reg write_overflow = 0;

    wire [13*4-1:0] scale_table;
    wire [13-1:0] overflow_table;

    rational_surd5_scale_manager #(.NODES(13)) uut (
        .clk(clk),
        .rst_n(rst_n),
        .write_en(write_en),
        .write_idx(write_idx),
        .write_shift(write_shift),
        .write_overflow(write_overflow),
        .scale_table(scale_table),
        .overflow_table(overflow_table)
    );

    always #5 clk = ~clk;

    integer i;
    integer errors;

    initial begin
        // reset
        #2 rst_n = 1;
        #4;

        // write entries
        for (i = 0; i < 13; i = i + 1) begin
            write_idx = i[3:0];
            write_shift = i & 4'hF;
            write_overflow = i & 1;
            write_en = 1;
            #10;
            write_en = 0;
            #10;
        end

        // wait settle
        #20;

        // verify
        errors = 0;
        for (i = 0; i < 13; i = i + 1) begin
            if (scale_table[i*4 +: 4] !== (i & 4'hF)) begin
                $display("ERR shift idx %0d: got %0d expected %0d", i, scale_table[i*4 +:4], (i & 4'hF));
                errors = errors + 1;
            end
            if (overflow_table[i] !== (i & 1)) begin
                $display("ERR overflow idx %0d: got %0d expected %0d", i, overflow_table[i], (i & 1));
                errors = errors + 1;
            end
        end

        if (errors == 0) $display("PASS"); else $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
