`timescale 1ns/1ps

// Artix tensegrity probe: exercise the real table loader, pin all seven TGR1
// guard verdicts in order, and decode the UART acceptance line.
module spu_a7_tensegrity_probe_tb #(
    parameter USE_ZPHI_KARATSUBA = 0
);
    localparam CLKS_PER_BIT = 8;
    localparam LINE_LEN = 16;

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    wire [2:0] led;
    wire uart_tx;

    spu_a7_tensegrity_probe_top #(
        .CLKS_PER_BIT(CLKS_PER_BIT),
        .START_DELAY(1),
        .LINE_PERIOD(4),
        .USE_ZPHI_KARATSUBA(USE_ZPHI_KARATSUBA)
    ) dut (
        .sys_clk(clk),
        .rst_n(rst_n),
        .led(led),
        .uart_tx(uart_tx)
    );

    always #5 clk = ~clk;

    integer errors = 0;
    integer verdicts_seen = 0;
    integer guard_clock_cycles = 0;
    integer guard_start_cycle = 0;
    reg guard_active = 1'b0;

    // Observe each guard completion independently of the wrapper's final
    // PASS decision, preventing a vacuous UART-only pass.
    always @(posedge dut.guard_clk) begin
        guard_clock_cycles = guard_clock_cycles + 1;
        if (dut.guard_start) begin
            guard_start_cycle = guard_clock_cycles;
            guard_active = 1'b1;
        end
        if (dut.guard_done) begin
            if (!guard_active) begin
                errors = errors + 1;
                $display("FAIL guard completion without accepted start");
            end
            case (verdicts_seen)
                0: if (dut.guard_state !== 4'd2 || dut.guard_fault !== 3'd0) errors = errors + 1;
                1: if (dut.guard_state !== 4'd7 || dut.guard_fault !== 3'd4) errors = errors + 1;
                2: if (dut.guard_state !== 4'd5 || dut.guard_fault !== 3'd2) errors = errors + 1;
                3: if (dut.guard_state !== 4'd4 || dut.guard_fault !== 3'd1) errors = errors + 1;
                4: if (dut.guard_state !== 4'd9 || dut.guard_fault !== 3'd6) errors = errors + 1;
                5: if (dut.guard_state !== 4'd6 || dut.guard_fault !== 3'd3) errors = errors + 1;
                6: if (dut.guard_state !== 4'd8 || dut.guard_fault !== 3'd5) errors = errors + 1;
                default: errors = errors + 1;
            endcase
            $display("ZPHI_CYCLE kind=probe fixture=%0d mode=%0d cycles=%0d decision=state_%0d_fault_%0d",
                     verdicts_seen, USE_ZPHI_KARATSUBA,
                     guard_clock_cycles - guard_start_cycle,
                     dut.guard_state, dut.guard_fault);
            guard_active = 1'b0;
            verdicts_seen = verdicts_seen + 1;
        end
    end

    reg [7:0] rx_byte;
    reg [7:0] line [0:LINE_LEN-1];
    reg [7:0] expected [0:LINE_LEN-1];
    integer bit_index;
    integer byte_index;

    task uart_rx_byte;
        begin
            @(negedge uart_tx);
            repeat (CLKS_PER_BIT / 2) @(posedge clk);
            for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
                repeat (CLKS_PER_BIT) @(posedge clk);
                rx_byte[bit_index] = uart_tx;
            end
            repeat (CLKS_PER_BIT) @(posedge clk);
        end
    endtask

    initial begin
        expected[0]="T"; expected[1]="G"; expected[2]="R"; expected[3]=":";
        expected[4]="P"; expected[5]=" "; expected[6]="V"; expected[7]=":";
        expected[8]="7"; expected[9]=" "; expected[10]="E"; expected[11]=":";
        expected[12]="0"; expected[13]="0";
        expected[14]=8'h0d; expected[15]=8'h0a;

        repeat (10) @(posedge clk);
        rst_n = 1'b1;

        for (byte_index = 0; byte_index < LINE_LEN; byte_index = byte_index + 1) begin
            uart_rx_byte;
            line[byte_index] = rx_byte;
        end

        for (byte_index = 0; byte_index < LINE_LEN; byte_index = byte_index + 1) begin
            if (line[byte_index] !== expected[byte_index]) begin
                errors = errors + 1;
                $display("FAIL UART byte %0d got=%02h expected=%02h",
                         byte_index, line[byte_index], expected[byte_index]);
            end
        end

        if (verdicts_seen != 7) begin
            errors = errors + 1;
            $display("FAIL guard verdict count got=%0d expected=7", verdicts_seen);
        end
        if (dut.vectors_done !== 3'd7 || dut.loader_state !== 4'd9) begin
            errors = errors + 1;
            $display("FAIL terminal state loader=%0d vectors=%0d",
                     dut.loader_state, dut.vectors_done);
        end
        if (led !== 3'b000) begin
            errors = errors + 1;
            $display("FAIL diagnostic LEDs must remain quiescent, got=%b", led);
        end

        if (errors == 0)
            $display("SPU_A7_TENSEGRITY_PROBE_TB: PASS (TGR:P V:7 E:00)");
        else
            $display("SPU_A7_TENSEGRITY_PROBE_TB: FAIL errors=%0d", errors);
        $finish(errors != 0);
    end

    initial begin
        #1000000;
        $display("SPU_A7_TENSEGRITY_PROBE_TB: FAIL watchdog");
        $finish(1);
    end
endmodule
