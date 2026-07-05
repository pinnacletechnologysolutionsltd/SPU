`timescale 1ns / 1ps

module spu13_southbridge_token_parser_tb;

    // Inputs
    reg           sys_clk;
    reg           rst_n;
    reg           fifo_valid;
    reg  [7:0]    fifo_data_out;
    reg  [3:0]    byte_counter;
    reg  [7:0]    calculated_crc;
    integer       i;

    // Outputs
    wire          config_reg_write;
    wire          error_flag_out;

    // Instantiate the Unit Under Test (UUT)
    spu13_southbridge_token_parser uut (
        .sys_clk            (sys_clk),
        .rst_n              (rst_n),
        .fifo_valid         (fifo_valid),
        .fifo_data_out      (fifo_data_out),
        .byte_counter       (byte_counter),
        .calculated_crc     (calculated_crc),
        .config_reg_write   (config_reg_write),
        .error_flag_out     (error_flag_out)
    );

    // Clock generation
    initial begin
        sys_clk = 0;
        forever #5 sys_clk = ~sys_clk; // 100 MHz clock (5ns period)
    end

    // Test sequence
    initial begin
        // Initialize inputs
        rst_n          = 0;
        fifo_valid     = 0;
        fifo_data_out  = 0;
        byte_counter   = 0;
        calculated_crc = 0;

        $display("\n--- Starting Testbench ---\n");

        // 1. Reset
        #10 rst_n = 1; // Release reset

        // Test Case 1: Valid token reception
        $display("Test Case 1: Valid token reception");
        @(posedge sys_clk) #1; // Wait for one clock edge after reset release

        // Send A5 header
        fifo_valid    = 1;
        fifo_data_out = 8'hA5;
        byte_counter  = 16; // Dummy value, byte_counter is not used for header recognition in the module
        @(posedge sys_clk) #1;
        fifo_valid    = 0;

        // Send 10 bytes after header: address + 64-bit payload + CRC.
        for (i = 0; i <= 9; i = i + 1) begin
            @(posedge sys_clk) #1;
            fifo_valid    = 1;
            fifo_data_out = i;
            byte_counter  = i;
            if (i == 9) begin
                calculated_crc = 9; // Expected CRC to match the last byte sent
            end
            @(posedge sys_clk) #1;
            fifo_valid    = 0;
        end

        @(posedge sys_clk) #1;
        if (config_reg_write == 1 && error_flag_out == 0) begin
            $display("Test Case 1 PASSED: Valid token received and committed.");
        end else begin
            $display("Test Case 1 FAILED: Invalid config_reg_write or error_flag_out. (write=%d, error=%d)", config_reg_write, error_flag_out);
        end
        // ------------------------------------------------------------
        // Test Case 2: Timeout scenario
        $display("\nTest Case 2: Timeout scenario (partial packet stall)");
        @(posedge sys_clk) #1;

        // Send A5 header
        fifo_valid    = 1;
        fifo_data_out = 8'hA5;
        byte_counter  = 16; // Dummy value
        @(posedge sys_clk) #1;
        fifo_valid    = 0;

        // Send a few data bytes (e.g., 5 bytes)
        for (i = 0; i <= 4; i = i + 1) begin
            @(posedge sys_clk) #1;
            fifo_valid    = 1;
            fifo_data_out = i;
            byte_counter  = i;
            @(posedge sys_clk) #1;
            fifo_valid    = 0;
        end

        // Now, induce a stall for more than 16 cycles
        #180; // 18 clock cycles (18 * 10ns = 180ns)

        if (config_reg_write == 0 && error_flag_out == 0) begin // Should not commit or error, just reset
            $display("Test Case 2 PASSED: State machine reset due to timeout.");
        end else begin
            $display("Test Case 2 FAILED: State machine did not reset on timeout. (write=%d, error=%d)", config_reg_write, error_flag_out);
        end
        // ------------------------------------------------------------
        // Test Case 3: CRC mismatch scenario
        $display("\nTest Case 3: CRC mismatch");
        @(posedge sys_clk) #1;

        // Send A5 header
        fifo_valid    = 1;
        fifo_data_out = 8'hA5;
        byte_counter  = 16;
        @(posedge sys_clk) #1;
        fifo_valid    = 0;

        // Send 10 bytes after header: address + 64-bit payload + CRC.
        for (i = 0; i <= 9; i = i + 1) begin
            @(posedge sys_clk) #1;
            fifo_valid    = 1;
            fifo_data_out = i;
            byte_counter  = i;
            if (i == 9) begin
                calculated_crc = 99; // Intentionally wrong CRC
            end
            @(posedge sys_clk) #1;
            fifo_valid    = 0;
        end

        @(posedge sys_clk) #1;
        if (config_reg_write == 0 && error_flag_out == 1) begin // Should not commit, should error
            $display("Test Case 3 PASSED: CRC mismatch detected and error flagged.");
        end else begin
            $display("Test Case 3 FAILED: CRC mismatch not handled correctly. (write=%d, error=%d)", config_reg_write, error_flag_out);
        end
        $display("\n--- Testbench Finished ---\n");

        $finish;
    end

endmodule
