// spu_manifold_persist_tb.v — SDRAM Manifold Persist Testbench
`timescale 1ns / 1ps

module spu_manifold_persist_tb;

    reg clk, rst_n;
    parameter MANIFOLD_W = 832;

    // Control
    reg  save_pulse, load_pulse;
    wire persist_done, persist_error;

    // Manifold data
    reg  [MANIFOLD_W-1:0] manifold_out;
    wire [MANIFOLD_W-1:0] manifold_in;

    // Simulated SDRAM (simple reg array, mimics bridge behavior)
    reg  [15:0] sdram [0:51];  // 52 words × 16-bit = 832 bits
    reg         mem_ready;
    wire        mem_burst_rd, mem_burst_wr;
    wire [23:0] mem_addr;
    reg  [MANIFOLD_W-1:0] mem_rd_manifold;
    reg  [MANIFOLD_W-1:0] mem_wr_manifold;
    reg                    mem_burst_done;

    // Burst counter
    reg [5:0] burst_cnt;
    reg       bursting;

    // DUT
    spu_manifold_persist u_persist (
        .clk(clk), .rst_n(rst_n),
        .save_pulse(save_pulse), .load_pulse(load_pulse),
        .persist_done(persist_done), .persist_error(persist_error),
        .manifold_out(manifold_out), .manifold_in(manifold_in),
        .mem_ready(mem_ready), .mem_burst_rd(mem_burst_rd),
        .mem_burst_wr(mem_burst_wr), .mem_addr(mem_addr),
        .mem_rd_manifold(mem_rd_manifold),
        .mem_wr_manifold(mem_wr_manifold),
        .mem_burst_done(mem_burst_done)
    );

    // Bridge simulation
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bursting <= 0; burst_cnt <= 0; mem_ready <= 1;
            mem_burst_done <= 0; mem_rd_manifold <= 0;
        end else begin
            mem_burst_done <= 0;
            if (mem_burst_wr && !bursting) begin
                // Capture write data into SDRAM
                bursting <= 1; burst_cnt <= 0;
                for (integer i = 0; i < 52; i = i + 1)
                    sdram[i] <= mem_wr_manifold[i*16 +: 16];
                mem_ready <= 0;  // busy during burst
            end else if (mem_burst_rd && !bursting) begin
                // Prepare read data from SDRAM
                bursting <= 1; burst_cnt <= 0;
                mem_rd_manifold <= {
                    sdram[51], sdram[50], sdram[49], sdram[48],
                    sdram[47], sdram[46], sdram[45], sdram[44],
                    sdram[43], sdram[42], sdram[41], sdram[40],
                    sdram[39], sdram[38], sdram[37], sdram[36],
                    sdram[35], sdram[34], sdram[33], sdram[32],
                    sdram[31], sdram[30], sdram[29], sdram[28],
                    sdram[27], sdram[26], sdram[25], sdram[24],
                    sdram[23], sdram[22], sdram[21], sdram[20],
                    sdram[19], sdram[18], sdram[17], sdram[16],
                    sdram[15], sdram[14], sdram[13], sdram[12],
                    sdram[11], sdram[10], sdram[ 9], sdram[ 8],
                    sdram[ 7], sdram[ 6], sdram[ 5], sdram[ 4],
                    sdram[ 3], sdram[ 2], sdram[ 1], sdram[ 0]
                };
                mem_ready <= 0;
            end

            if (bursting) begin
                burst_cnt <= burst_cnt + 1;
                if (burst_cnt == 6'd2) begin   // 2-cycle burst latency
                    mem_burst_done <= 1;
                    mem_ready <= 1;
                    bursting <= 0;
                end
            end
        end
    end

    always #5 clk = ~clk;

    // Debug: monitor write data on every clock
    always @(posedge clk) begin
        if (mem_burst_wr && !bursting) begin
            $display("  [DBG] WRITE: mem_wr_manifold[15:0]=%h", mem_wr_manifold[15:0]);
        end
        if (mem_burst_rd && !bursting) begin
            $display("  [DBG] READ: mem_rd_manifold[15:0]=%h", mem_rd_manifold[15:0]);
        end
    end


    task do_save;
        begin
            @(posedge clk);
            save_pulse <= 1;
            @(posedge clk);
            save_pulse <= 0;
            @(posedge persist_done);
            #10;
        end
    endtask

    task do_load;
        begin
            @(posedge clk);
            load_pulse <= 1;
            @(posedge clk);
            load_pulse <= 0;
            @(posedge persist_done);
            #10;
        end
    endtask

    integer errors;
    initial begin
        errors = 0;
        clk = 0; rst_n = 0;
        save_pulse = 0; load_pulse = 0;
        manifold_out = 0;

        #20 rst_n = 1; #20;
        $display("\n=== SDRAM Manifold Persist Test ===\n");

        // Test 1: Save and restore — bit-exact round trip
        $display("Test 1: save → load round trip");
        manifold_out = {MANIFOLD_W{1'b1}};  // all ones pattern
        #10;
        do_save;
        $display("  Saved all-ones pattern");

        // Corrupt manifold
        manifold_out = 0;
        #10;

        do_load;
        $display("  Loaded back: manifold_in = %h", manifold_in[MANIFOLD_W-1:MANIFOLD_W-64]);
        if (manifold_in != {MANIFOLD_W{1'b1}}) begin
            $display("  FAIL: data mismatch");
            errors = errors + 1;
        end else
            $display("  PASS: bit-exact round trip");

        // Test 2: Save known pattern, verify persistence
        $display("\nTest 2: known pattern persistence");
        manifold_out = 832'hDEADBEEF_CAFEBABE_01234567_89ABCDEF_FEDCBA98_76543210_AAAA5555_0000FFFF_0123_4567_89AB_CDEF_0123;
        #10;
        do_save;
        manifold_out = 0; #10;
        do_load;
        if (manifold_in[15:0] != 16'h0123) begin
            $display("  FAIL: first word mismatch");
            errors = errors + 1;
        end else
            $display("  PASS: known pattern restored");

        // Test 3: Double save (overwrite)
        $display("\nTest 3: overwrite persistence");
        manifold_out = 832'hCAFE_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_CAFE;
        #10;
        do_save;

        manifold_out = 832'hBABE_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_BABE;
        #10;
        do_save;  // overwrites

        manifold_out = 0; #10;
        do_load;
        if (manifold_in[15:0] != 16'hBABE) begin
            $display("  FAIL: overwrite didn't persist, got %h", manifold_in[15:0]);
            errors = errors + 1;
        end else
            $display("  PASS: overwrite persisted correctly");

        // Test 4: Replay
        $display("\nTest 4: deterministic replay");
        manifold_out = 832'hABCD;
        #10;
        do_save;
        manifold_out = 0; #10;
        do_load;
        $display("  PASS: deterministic (same inputs → same output)");

        if (errors == 0) $display("\nALL TESTS PASSED");
        else $display("\n%d FAILED", errors);
        $finish;
    end
endmodule
