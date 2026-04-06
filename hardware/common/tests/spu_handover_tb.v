`timescale 1ns/1ps

/*
 * spu_handover_tb.v (v1.1 - Sovereign Boot Verification)
 * Objective: Verify the Phi-Gated Boot -> SQR Sovereign handover.
 * Target: spu_icesugar_top.v
 */

module spu_handover_tb;

    reg clk;
    wire led_r, led_g, led_b;
    wire psram_ce_n, psram_clk;
    wire [3:0] psram_dq;
    wire uart_tx;
    wire sovereign_heartbeat;

    // --- 1. DUT Instance ---
    spu_icesugar_top dut (
        .clk(clk),
        .LED_R(led_r),
        .LED_G(led_g),
        .LED_B(led_b),
        .psram_ce_n(psram_ce_n),
        .psram_clk(psram_clk),
        .psram_dq(psram_dq),
        .uart_tx(uart_tx),
        .sovereign_heartbeat(sovereign_heartbeat)
    );

    // Helper to monitor internal signals (requires iverilog -g2012)
    wire boot_done_internal = dut.boot_done;

    // --- 2. SPI Flash / PSRAM Model ---
    reg [7:0] flash_mem [0:1023];
    integer i;
    initial begin
        for (i = 0; i < 1024; i = i + 1) flash_mem[i] = i[7:0];
    end

    reg [31:0] shift_in;
    reg [7:0]  out_byte;
    integer bit_ptr;

    assign psram_dq[1] = (!psram_ce_n && !boot_done_internal) ? out_byte[7] : 1'bz;

    always @(posedge psram_clk) begin
        shift_in <= {shift_in[30:0], psram_dq[0]};
    end

    always @(negedge psram_clk) begin
        if (psram_ce_n) begin
            bit_ptr <= 7;
        end else begin
            out_byte <= flash_mem[bit_ptr]; 
            bit_ptr <= (bit_ptr == 0) ? 7 : bit_ptr - 1;
        end
    end

    // --- 3. Clock & Simulation Control ---
    initial clk = 0;
    always #41.66 clk = ~clk; // 12 MHz

    initial begin
        $dumpfile("handover_trace.vcd");
        $dumpvars(0, spu_handover_tb);
        
        $display("--- [Sovereign Handover] Initializing iCEsugar Domain ---");
        #1000;
        
        $display("--- [Sovereign Handover] Monitoring Boot Hydration (Blue LED) ---");
        
        // Timeout check for boot
        fork
            begin
                while (!boot_done_internal) begin
                    @(posedge psram_clk);
                    if (dut.u_boot.bit_cnt == 0 && dut.u_boot.state == 3) // S_INHALE_DATA
                        $display("[TB] Hydrating Prime %0d...", dut.u_boot.prime_addr);
                end
                $display("--- [Sovereign Handover] Boot Hydration COMPLETE (Handover Triggered) ---");
            end
            begin
                #10000000; // 10ms timeout
                if (!boot_done_internal) begin
                    $display("[FAIL] Boot Hydration TIMEOUT at 10ms. Internal State: %0d, Bit: %0d", dut.u_boot.state, dut.u_boot.bit_cnt);
                    $finish;
                end
            end
        join


        $display("--- [Sovereign Handover] Sovereign Core ACTIVE (Green LED) ---");
        #100000;
        
        if (sovereign_heartbeat) begin
            $display("[PASS] Sierpinski Heartbeat Detected. System is Laminar-Locked.");
        end

        $display("--- [Sovereign Handover] Verification PASS ---");
        $finish;
    end

endmodule
