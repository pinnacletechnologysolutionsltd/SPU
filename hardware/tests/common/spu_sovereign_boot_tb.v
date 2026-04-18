`timescale 1ns/1ps

module spu_sovereign_boot_tb;

    reg clk, clk_ghost, rst_n;
    
    // SPI Flash Interface
    wire flash_sclk, flash_cs_n, flash_mosi, flash_miso;
    
    // PMOD Prime Interface
    wire pmod_sclk, pmod_mosi, pmod_cs_n;
    
    // Control & Status
    reg rd_trig;
    reg [23:0] rd_addr;
    wire [7:0] rd_data;
    wire rd_done;
    
    wire prime_done;
    wire [831:0] prime_manifold;
    wire prime_valid;

    // 1. SPI Flash Bridge
    spu_flash_bridge u_flash (
        .clk(clk), .rst_n(rst_n),
        .rd_trig(rd_trig), .rd_addr(rd_addr), .rd_data(rd_data), .rd_done(rd_done),
        .flash_sclk(flash_sclk), .flash_cs_n(flash_cs_n), .flash_mosi(flash_mosi), .flash_miso(flash_miso)
    );

    // 2. PMOD Prime Loader
    spu_pmod_loader u_pmod (
        .clk(clk), .rst_n(rst_n),
        .pmod_sclk(pmod_sclk), .pmod_mosi(pmod_mosi), .pmod_cs_n(pmod_cs_n),
        .load_done(prime_done), .prime_manifold(prime_manifold), .prime_valid(prime_valid)
    );

    // 3. Mocks
    assign flash_miso = 1'b1; // Mock Flash MISO (Always 1 for now)
    
    // PMOD Mock: Simulated 832-bit Prime Bloom
    reg pmod_clk_reg;
    reg pmod_mosi_reg;
    reg pmod_cs_n_reg;
    assign pmod_sclk = pmod_clk_reg;
    assign pmod_mosi = pmod_mosi_reg;
    assign pmod_cs_n = pmod_cs_n_reg;

    always #41.66 clk = ~clk; // 12 MHz iCE40 Clock
    always #3.76 clk_ghost = ~clk_ghost; // 133 MHz Ghost OS

    integer b;
    initial begin
        $dumpfile("boot_trace.vcd");
        $dumpvars(0, spu_sovereign_boot_tb);
        
        clk = 0; clk_ghost = 0; rst_n = 0;
        rd_trig = 0; rd_addr = 0;
        pmod_clk_reg = 0; pmod_mosi_reg = 0; pmod_cs_n_reg = 1;
        
        #1000;
        rst_n = 1;
        #2000;
        
        $display("--- [Sovereign Boot] Initiating Prime Hydration ---");
        
        // Simulate PMOD Bit-stream (832 bits)
        pmod_cs_n_reg = 0;
        for (b = 0; b < 832; b = b + 1) begin
            pmod_mosi_reg = (b % 2); // alternating test pattern
            #400; pmod_clk_reg = 1; #400; pmod_clk_reg = 0;
        end
        pmod_cs_n_reg = 1;
        
        #5000;
        if (prime_valid) begin
            $display("[PASS] Prime Manifold Hydrated: %x", prime_manifold[63:0]);
        end else begin
            $display("[FAIL] Prime Manifold not valid.");
        end

        $display("--- [Sovereign Boot] Initiating Flash OS Pulse ---");
        @(posedge clk);
        rd_trig = 1; rd_addr = 24'h00ABCD;
        @(posedge clk);
        rd_trig = 0;
        
        #50000;
        $finish;
    end

endmodule
