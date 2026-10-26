// spu_laminar_boot_tb.v
// Smoke testbench for SPI boot controller (spu_laminar_boot)
//
// Purpose: Verify flash read sequence, BRAM write handoff, boot_done assertion
//
// Expected output: PASS or FAIL

`default_nettype none

module spu_laminar_boot_tb;
    reg         clk;
    reg         rst_n;

    // Flash SPI interface (from ECP5)
    wire        flash_cs;
    wire        flash_sck;
    wire        flash_mosi;
    wire        flash_miso;

    // BRAM interface (to register file)
    wire [23:0] bram_data;
    wire [3:0]  bram_addr;
    wire        bram_we;

    // Pell register interface
    wire [31:0] pell_data;
    wire [2:0]  pell_addr;
    wire        pell_we;

    // Status
    wire        boot_done;
    wire [23:0] jedec_id;
    reg         seen_bram_we;
    reg         seen_pell_we;
    integer     timeout_cycles;

    // Instantiate DUT
    spu_laminar_boot #(
        .ENABLE_RPLU_BOOT(0),
        .SPI_SCK_HALF_CYCLES(1)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .flash_cs(flash_cs),
        .flash_sck(flash_sck),
        .flash_miso(flash_miso),
        .flash_mosi(flash_mosi),
        .bram_data(bram_data),
        .bram_addr(bram_addr),
        .bram_we(bram_we),
        .pell_data(pell_data),
        .pell_addr(pell_addr),
        .pell_we(pell_we),
        .boot_done(boot_done),
        .jedec_id(jedec_id),
        .mem_burst_wr(),
        .mem_addr(),
        .mem_wr_manifold(),
        .mem_burst_done(1'b1),
        .rplu_cfg_wr_en(),
        .rplu_cfg_sel(),
        .rplu_cfg_material(),
        .rplu_cfg_addr(),
        .rplu_cfg_data(),
        .rplu_cfg_loaded(),
        .rplu_cfg_checksum(),
        .boot_state()
    );

    // Clock generation (12 MHz)
    always #41 clk = ~clk;

    // Simplified W25Q flash model (MISO shifter)
    reg [15:0] spi_shift_in;
    reg [7:0]  byte_counter;

    always @(negedge flash_sck or negedge rst_n) begin
        if (!rst_n) begin
            spi_shift_in <= 16'h0;
            byte_counter <= 8'h0;
        end else begin
            // Simplified: just echo back incrementing pattern
            if (!flash_cs) begin
                spi_shift_in <= {spi_shift_in[14:0], 1'b1};  // Shift pattern
                byte_counter <= byte_counter + 1;
            end else begin
                byte_counter <= 8'h0;
            end
        end
    end

    assign flash_miso = spi_shift_in[15];  // MSB out

    // Main test sequence
    initial begin
        clk <= 1'b0;
        rst_n <= 1'b1;
        seen_bram_we <= 1'b0;
        seen_pell_we <= 1'b0;
        timeout_cycles = 0;

        // Hold reset for 100 cycles
        #(100 * 83)  // 83 ns per 12 MHz cycle
        rst_n <= 1'b0;

        #(100 * 83)
        rst_n <= 1'b1;

        // Wait for boot sequence
        // Expected: boot_done should assert after flash read + BRAM writes
        // Typical: 2000–5000 cycles depending on flash latency model

        while (!boot_done && timeout_cycles < 20000) begin
            @(posedge clk);
            timeout_cycles = timeout_cycles + 1;
        end

        if (boot_done) begin
            $display("✓ Boot sequence completed (boot_done asserted)");
        end else begin
            $display("✗ Boot sequence timed out (boot_done not asserted)");
        end

        // Spot-check BRAM writes occurred
        if (seen_bram_we) begin
            $display("✓ BRAM write strobe detected (bram_we pulsed)");
        end

        // Spot-check Pell writes occurred
        if (seen_pell_we) begin
            $display("✓ Pell register write detected (pell_we pulsed)");
        end

        // Summary
        if (boot_done && seen_bram_we && seen_pell_we) begin
            $display("\nPASS: Boot sequence functional");
            $finish;
        end else begin
            $display("\nFAIL: Boot sequence incomplete");
            $finish;
        end
    end

    // Monitoring (optional verbose output)
    always @(posedge clk) begin
        if (bram_we) begin
            seen_bram_we <= 1'b1;
            $display("[%d] BRAM write: addr=%h data=%h", $time, bram_addr, bram_data);
        end
        if (pell_we) begin
            seen_pell_we <= 1'b1;
            $display("[%d] Pell write: addr=%h data=%h", $time, pell_addr, pell_data);
        end
    end

endmodule
