// spu_sensor_bank_tb.v — Testbench for spu_sensor_bank
`timescale 1ns/1ps

module spu_sensor_bank_tb;
    reg        clk, reset;
    reg  [7:0] bus_addr;
    reg  [31:0] bus_wdata;
    reg        bus_wen, bus_ren;
    wire [31:0] bus_rdata;
    wire       bus_ready;

    spu_sensor_bank #(.BASE_ADDR(8'h80)) dut (
        .clk(clk), .reset(reset),
        .bus_addr(bus_addr), .bus_wdata(bus_wdata),
        .bus_wen(bus_wen), .bus_ren(bus_ren),
        .bus_rdata(bus_rdata), .bus_ready(bus_ready)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    integer fail = 0;

    task write_reg;
        input [7:0] addr;
        input [31:0] data;
        begin
            @(negedge clk);
            bus_addr  = addr;
            bus_wdata = data;
            bus_wen   = 1;
            bus_ren   = 0;
            @(posedge clk); #1;
            bus_wen = 0;
            if (!bus_ready) begin
                $display("FAIL: bus_ready not asserted after write addr=%h", addr);
                fail = fail + 1;
            end
        end
    endtask

    task read_reg;
        input [7:0] addr;
        input [31:0] expected;
        begin
            @(negedge clk);
            bus_addr = addr;
            bus_ren  = 1;
            bus_wen  = 0;
            @(posedge clk); #1;
            bus_ren = 0;
            if (!bus_ready) begin
                $display("FAIL: bus_ready not asserted after read addr=%h", addr);
                fail = fail + 1;
            end
            if (bus_rdata !== expected) begin
                $display("FAIL: addr=%h got=%h expected=%h", addr, bus_rdata, expected);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        reset = 1; bus_wen = 0; bus_ren = 0;
        bus_addr = 0; bus_wdata = 0;
        @(posedge clk); @(posedge clk);
        reset = 0;

        // Write all 8 registers
        write_reg(8'h80, 32'hDEAD0001);
        write_reg(8'h81, 32'hDEAD0002);
        write_reg(8'h82, 32'hDEAD0003);
        write_reg(8'h83, 32'hDEAD0004);
        write_reg(8'h84, 32'hDEAD0005);
        write_reg(8'h85, 32'hDEAD0006);
        write_reg(8'h86, 32'hDEAD0007);
        write_reg(8'h87, 32'hDEAD0008);

        // Read back and verify
        read_reg(8'h80, 32'hDEAD0001);
        read_reg(8'h84, 32'hDEAD0005);
        read_reg(8'h87, 32'hDEAD0008);

        // Out-of-range write should be silently ignored (no bus_ready)
        @(negedge clk);
        bus_addr  = 8'h88;
        bus_wdata = 32'hBAADF00D;
        bus_wen   = 1;
        bus_ren   = 0;
        @(posedge clk); #1;
        bus_wen = 0;
        // bus_ready is NOT expected for an out-of-range address
        read_reg(8'h80, 32'hDEAD0001);  // unchanged

        // Overwrite
        write_reg(8'h82, 32'hABCD1234);
        read_reg(8'h82, 32'hABCD1234);

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d errors)", fail);
        $finish;
    end
endmodule
