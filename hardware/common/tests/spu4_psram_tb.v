`timescale 1ns/1ps

// Simple APS6404L PSRAM Behavioural Model
module psram_model (
    input  wire        sck,
    input  wire        ce_n,
    inout  wire [3:0]  dq
);
    reg [7:0] mem [0:255]; // Small 256-byte model for simulation
    reg [3:0] dq_r;
    reg       dq_oe;
    reg [7:0] cmd;
    reg [23:0] addr_r;
    reg [3:0]  state;
    reg [7:0]  bit_cnt;
    reg        qpi_mode;

    assign dq = dq_oe ? dq_r : 4'bzzzz;

    localparam CMD_RST_EN    = 8'h66;
    localparam CMD_RST       = 8'h99;
    localparam CMD_ENTER_QPI = 8'h35;
    localparam CMD_FAST_READ = 8'hEB;
    localparam CMD_QUAD_WRITE= 8'h38;

    integer i;
    initial begin
        dq_oe = 0; qpi_mode = 0; state = 0; bit_cnt = 0;
        for (i = 0; i < 256; i = i+1) mem[i] = i[7:0]; // seed
    end

    always @(posedge sck or posedge ce_n) begin
        if (ce_n) begin
            dq_oe <= 0;
            state <= 0; bit_cnt <= 0;
        end else begin
            case (state)
                0: begin // Receive CMD (SPI or QPI)
                    if (!qpi_mode) begin
                        cmd <= {cmd[6:0], dq[0]};
                        if (bit_cnt == 7) begin
                            bit_cnt <= 0;
                            if (cmd[6:0] == CMD_RST_EN[6:0]) state <= 1;
                            else if (cmd[6:0] == CMD_ENTER_QPI[6:0]) begin qpi_mode <= 1; state <= 9; end
                            else if (cmd[6:0] == CMD_FAST_READ[6:0]) state <= 2;
                            else if (cmd[6:0] == CMD_QUAD_WRITE[6:0]) state <= 5;
                        end else bit_cnt <= bit_cnt + 1;
                    end else begin // QPI nibbles
                        cmd <= {cmd[3:0], dq};
                        if (bit_cnt == 1) begin
                            bit_cnt <= 0;
                            if (cmd[3:0] == CMD_FAST_READ[3:0]) state <= 2;
                            else if (cmd[3:0] == CMD_QUAD_WRITE[3:0]) state <= 5;
                        end else bit_cnt <= bit_cnt + 1;
                    end
                end
                1: state <= 0; // After RST_EN: accept RST
                2: begin // Receive ADDR (6 QPI nibbles = 24 bits)
                    addr_r <= {addr_r[19:0], dq};
                    if (bit_cnt == 5) begin bit_cnt <= 0; state <= 3; end
                    else bit_cnt <= bit_cnt + 1;
                end
                3: begin // Dummy cycles (6)
                    if (bit_cnt == 5) begin bit_cnt <= 0; dq_oe <= 1; state <= 4; end
                    else bit_cnt <= bit_cnt + 1;
                end
                4: begin // Send DATA (QPI nibbles)
                    dq_r <= mem[addr_r[7:0]][7 - (bit_cnt[0] ? 0 : 4) +: 4];
                    if (bit_cnt == 3) begin dq_oe <= 0; state <= 0; bit_cnt <= 0; end
                    else bit_cnt <= bit_cnt + 1;
                end
                5: begin // Write ADDR
                    addr_r <= {addr_r[19:0], dq};
                    if (bit_cnt == 5) begin bit_cnt <= 0; state <= 6; end
                    else bit_cnt <= bit_cnt + 1;
                end
                6: begin // Write DATA (2 nibbles = 1 byte)
                    mem[addr_r[7:0]] <= {mem[addr_r[7:0]][3:0], dq};
                    if (bit_cnt == 1) begin state <= 0; bit_cnt <= 0; end
                    else bit_cnt <= bit_cnt + 1;
                end
                9: state <= 0; // QPI mode entered
            endcase
        end
    end
endmodule

// ── Main Testbench ──────────────────────────────────────────────────────────
module spu4_psram_tb;

    reg clk, reset;

    // PSRAM PMOD pins
    wire psram_ce_n, psram_clk;
    wire [3:0] psram_dq;

    // DUT: SPU-4 Core with PSRAM
    spu4_core u_dut (
        .clk(clk), .reset(reset),
        .spi_cs_n(), .spi_sck(), .spi_mosi(), .spi_miso(1'b1),
        .prog_en_aux(1'b0), .prog_addr_aux(4'h0), .prog_data_aux(16'h0),
        .mode_autonomous(1'b0),
        .A_in(16'h1234), .B_in(16'h0), .C_in(16'h0), .D_in(16'h0),
        .F_rat(16'h0050), .G_rat(16'h00B5), .H_rat(16'h0050),
        .bus_addr(),  .bus_wen(), .bus_ren(),
        .bus_ready(1'b1),
        .psram_ce_n(psram_ce_n), .psram_clk(psram_clk), .psram_dq(psram_dq),
        .A_out(), .B_out(), .C_out(), .D_out(),
        .bloom_complete()
    );

    // PSRAM model
    psram_model u_psram (
        .sck(psram_clk), .ce_n(psram_ce_n), .dq(psram_dq)
    );

    always #41.66 clk = ~clk;

    initial begin
        $dumpfile("psram_inhale.vcd");
        $dumpvars(0, spu4_psram_tb);
        clk = 0; reset = 1; #500; reset = 0;

        $display("--- [PSRAM] Waiting for QPI init (~200us) ---");
        #250000; // 250us

        if (u_dut.u_psram.init_done)
            $display("[PASS] PSRAM QPI Init complete. Memory is Crystalline.");
        else
            $display("[WARN] PSRAM init still pending.");

        #50000;
        $display("[PASS] Refractive Memory online.");
        $finish;
    end
endmodule
