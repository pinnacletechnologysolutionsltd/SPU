`timescale 1ns/1ps

module boot_spi_flash_model (
    input  wire sck,
    input  wire cs_n,
    input  wire mosi,
    output reg  miso
);
    localparam integer MEM_BYTES = 24'h110040;
    localparam [2:0] ST_CMD   = 3'd0;
    localparam [2:0] ST_ADDR  = 3'd1;
    localparam [2:0] ST_READ  = 3'd2;
    localparam [2:0] ST_JEDEC = 3'd3;
    localparam [2:0] ST_DROP  = 3'd4;

    reg [7:0] mem [0:MEM_BYTES-1];
    reg [2:0] state;
    reg [7:0] cmd;
    reg [7:0] out_byte;
    reg [23:0] addr;
    reg [7:0] bit_cnt;
    reg [2:0] out_bit;
    reg [1:0] jedec_idx;
    reg [7:0] cmd_next;
    reg [23:0] addr_next;

    integer i;

    function [7:0] mem_at;
        input [23:0] a;
        begin
            if (a < MEM_BYTES)
                mem_at = mem[a];
            else
                mem_at = 8'hFF;
        end
    endfunction

    function [7:0] jedec_at;
        input [1:0] idx;
        begin
            case (idx)
                2'd0: jedec_at = 8'hEF;
                2'd1: jedec_at = 8'h40;
                2'd2: jedec_at = 8'h18;
                default: jedec_at = 8'hFF;
            endcase
        end
    endfunction

    task store32;
        input [23:0] base;
        input [31:0] value;
        begin
            mem[base + 0] = value[31:24];
            mem[base + 1] = value[23:16];
            mem[base + 2] = value[15:8];
            mem[base + 3] = value[7:0];
        end
    endtask

    task store64;
        input [23:0] base;
        input [63:0] value;
        begin
            mem[base + 0] = value[63:56];
            mem[base + 1] = value[55:48];
            mem[base + 2] = value[47:40];
            mem[base + 3] = value[39:32];
            mem[base + 4] = value[31:24];
            mem[base + 5] = value[23:16];
            mem[base + 6] = value[15:8];
            mem[base + 7] = value[7:0];
        end
    endtask

    function [63:0] rplu_header;
        input [2:0] sel;
        input material;
        input [9:0] table_addr;
        begin
            rplu_header = 64'd0;
            rplu_header[63:56] = 8'hA5;
            rplu_header[50:48] = sel;
            rplu_header[47] = material;
            rplu_header[46:37] = table_addr;
        end
    endfunction

    initial begin
        for (i = 0; i < MEM_BYTES; i = i + 1)
            mem[i] = 8'hFF;

        // Pell table at 0x100000: 8 entries, each big-endian P then Q.
        for (i = 0; i < 8; i = i + 1) begin
            store32(24'h100000 + (i * 8), 32'h00010000 + i[31:0]);
            store32(24'h100004 + (i * 8), 32'h00000010 + i[31:0]);
        end

        // Golden-prime table at 0x100100: 13 big-endian 32-bit words.
        for (i = 0; i < 13; i = i + 1)
            store32(24'h100100 + (i * 4), 32'h0000C000 + i[31:0]);

        // RPLU chord stream at 0x110000: header/data pairs.
        store64(24'h110000, rplu_header(3'd0, 1'b0, 10'd0));
        store64(24'h110008, 64'h0000_0000_0001_1111);
        store64(24'h110010, rplu_header(3'd5, 1'b0, 10'h012));
        store64(24'h110018, 64'h0000_0000_0002_2222);
        store64(24'h110020, rplu_header(3'd6, 1'b1, 10'h3FF));
        store64(24'h110028, 64'h0000_0000_0000_0001);

        miso = 1'b0;
        state = ST_CMD;
        cmd = 8'd0;
        out_byte = 8'd0;
        addr = 24'd0;
        bit_cnt = 8'd0;
        out_bit = 3'd7;
        jedec_idx = 2'd0;
    end

    always @(posedge cs_n or negedge cs_n) begin
        miso <= 1'b0;
        state <= ST_CMD;
        cmd <= 8'd0;
        addr <= 24'd0;
        bit_cnt <= 8'd0;
        out_bit <= 3'd7;
        jedec_idx <= 2'd0;
        out_byte <= 8'd0;
    end

    always @(posedge sck) begin
        if (!cs_n) begin
            case (state)
                ST_CMD: begin
                    cmd_next = {cmd[6:0], mosi};
                    cmd <= cmd_next;
                    if (bit_cnt == 8'd7) begin
                        bit_cnt <= 8'd0;
                        if (cmd_next == 8'h9F) begin
                            state <= ST_JEDEC;
                            out_byte <= jedec_at(2'd0);
                            out_bit <= 3'd7;
                            jedec_idx <= 2'd0;
                        end else if (cmd_next == 8'h03) begin
                            state <= ST_ADDR;
                            addr <= 24'd0;
                        end else begin
                            state <= ST_DROP;
                            out_byte <= 8'hFF;
                            out_bit <= 3'd7;
                        end
                    end else begin
                        bit_cnt <= bit_cnt + 1'b1;
                    end
                end

                ST_ADDR: begin
                    addr_next = {addr[22:0], mosi};
                    addr <= addr_next;
                    if (bit_cnt == 8'd23) begin
                        bit_cnt <= 8'd0;
                        state <= ST_READ;
                        out_byte <= mem_at(addr_next);
                        out_bit <= 3'd7;
                    end else begin
                        bit_cnt <= bit_cnt + 1'b1;
                    end
                end

                default: ;
            endcase
        end
    end

    always @(negedge sck) begin
        if (!cs_n) begin
            case (state)
                ST_JEDEC: begin
                    miso <= out_byte[out_bit];
                    if (out_bit == 3'd0) begin
                        out_bit <= 3'd7;
                        if (jedec_idx == 2'd2) begin
                            out_byte <= 8'hFF;
                        end else begin
                            jedec_idx <= jedec_idx + 1'b1;
                            out_byte <= jedec_at(jedec_idx + 1'b1);
                        end
                    end else begin
                        out_bit <= out_bit - 1'b1;
                    end
                end

                ST_READ: begin
                    miso <= out_byte[out_bit];
                    if (out_bit == 3'd0) begin
                        out_bit <= 3'd7;
                        addr <= addr + 1'b1;
                        out_byte <= mem_at(addr + 1'b1);
                    end else begin
                        out_bit <= out_bit - 1'b1;
                    end
                end

                ST_DROP: begin
                    miso <= 1'b1;
                end

                default: begin
                    miso <= 1'b0;
                end
            endcase
        end
    end
endmodule

module spu_laminar_boot_rplu_tb;
    reg clk = 1'b0;
    always #1 clk = ~clk;

    reg rst_n = 1'b0;
    wire flash_cs;
    wire flash_sck;
    wire flash_miso;
    wire flash_mosi;
    wire [23:0] jedec_id;
    wire [23:0] bram_data;
    wire [3:0] bram_addr;
    wire bram_we;
    wire [31:0] pell_data;
    wire [2:0] pell_addr;
    wire pell_we;
    wire mem_burst_wr;
    wire [24:0] mem_addr;
    wire [831:0] mem_wr_manifold;
    wire rplu_cfg_wr_en;
    wire [2:0] rplu_cfg_sel;
    wire [7:0] rplu_cfg_material;
    wire [9:0] rplu_cfg_addr;
    wire [63:0] rplu_cfg_data;
    wire [15:0] rplu_cfg_loaded;
    wire [31:0] rplu_cfg_checksum;
    wire boot_done;

    boot_spi_flash_model u_flash (
        .sck(flash_sck),
        .cs_n(flash_cs),
        .mosi(flash_mosi),
        .miso(flash_miso)
    );

    spu_laminar_boot #(
        .ENABLE_RPLU_BOOT(1),
        .RPLU_CFG_RECORDS(16'd3),
        .SPI_SCK_HALF_CYCLES(1)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .flash_cs(flash_cs),
        .flash_sck(flash_sck),
        .flash_miso(flash_miso),
        .flash_mosi(flash_mosi),
        .jedec_id(jedec_id),
        .bram_data(bram_data),
        .bram_addr(bram_addr),
        .bram_we(bram_we),
        .pell_data(pell_data),
        .pell_addr(pell_addr),
        .pell_we(pell_we),
        .mem_burst_wr(mem_burst_wr),
        .mem_addr(mem_addr),
        .mem_wr_manifold(mem_wr_manifold),
        .mem_burst_done(1'b1),
        .rplu_cfg_wr_en(rplu_cfg_wr_en),
        .rplu_cfg_sel(rplu_cfg_sel),
        .rplu_cfg_material(rplu_cfg_material),
        .rplu_cfg_addr(rplu_cfg_addr),
        .rplu_cfg_data(rplu_cfg_data),
        .rplu_cfg_loaded(rplu_cfg_loaded),
        .rplu_cfg_checksum(rplu_cfg_checksum),
        .boot_done(boot_done)
    );

    reg [2:0] seen_sel [0:2];
    reg [7:0] seen_material [0:2];
    reg [9:0] seen_addr [0:2];
    reg [63:0] seen_data [0:2];
    integer rplu_writes = 0;
    integer pell_writes = 0;
    integer prime_writes = 0;
    integer errors = 0;
    integer timeout_cycles;

    function [31:0] record_checksum;
        input [63:0] header;
        input [63:0] data;
        begin
            record_checksum = header[63:32] + header[31:0] + data[63:32] + data[31:0];
        end
    endfunction

    function [63:0] expected_rplu_header;
        input [2:0] sel;
        input material;
        input [9:0] table_addr;
        begin
            expected_rplu_header = 64'd0;
            expected_rplu_header[63:56] = 8'hA5;
            expected_rplu_header[50:48] = sel;
            expected_rplu_header[47] = material;
            expected_rplu_header[46:37] = table_addr;
        end
    endfunction

    always @(posedge clk) begin
        if (pell_we)
            pell_writes = pell_writes + 1;
        if (bram_we)
            prime_writes = prime_writes + 1;
        if (rplu_cfg_wr_en) begin
            if (rplu_writes < 3) begin
                seen_sel[rplu_writes] = rplu_cfg_sel;
                seen_material[rplu_writes] = rplu_cfg_material;
                seen_addr[rplu_writes] = rplu_cfg_addr;
                seen_data[rplu_writes] = rplu_cfg_data;
            end
            rplu_writes = rplu_writes + 1;
        end
    end

    task check;
        input cond;
        input [255:0] msg;
        begin
            if (!cond) begin
                $display("ERROR: %0s", msg);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        repeat (4) @(negedge clk);
        rst_n = 1'b1;

        timeout_cycles = 0;
        while (!boot_done && timeout_cycles < 250000) begin
            @(posedge clk);
            timeout_cycles = timeout_cycles + 1;
        end

        check(boot_done, "boot_done timed out");
        check(jedec_id == 24'hEF4018, "JEDEC ID mismatch");
        check(pell_writes == 8, "Pell write count mismatch");
        check(prime_writes == 13, "golden-prime write count mismatch");
        check(rplu_writes == 3, "RPLU config write count mismatch");
        check(rplu_cfg_loaded == 16'd3, "RPLU loaded count mismatch");
        check(rplu_cfg_checksum == (record_checksum(expected_rplu_header(3'd0, 1'b0, 10'd0), 64'h0000_0000_0001_1111)
                                  + record_checksum(expected_rplu_header(3'd5, 1'b0, 10'h012), 64'h0000_0000_0002_2222)
                                  + record_checksum(expected_rplu_header(3'd6, 1'b1, 10'h3FF), 64'h0000_0000_0000_0001)),
              "RPLU checksum mismatch");

        if (rplu_writes >= 3) begin
            check(seen_sel[0] == 3'd0, "RPLU record 0 sel mismatch");
            check(seen_material[0] == 8'd0, "RPLU record 0 material mismatch");
            check(seen_addr[0] == 10'd0, "RPLU record 0 addr mismatch");
            check(seen_data[0] == 64'h0000_0000_0001_1111, "RPLU record 0 data mismatch");

            check(seen_sel[1] == 3'd5, "RPLU record 1 sel mismatch");
            check(seen_material[1] == 8'd0, "RPLU record 1 material mismatch");
            check(seen_addr[1] == 10'h012, "RPLU record 1 addr mismatch");
            check(seen_data[1] == 64'h0000_0000_0002_2222, "RPLU record 1 data mismatch");

            check(seen_sel[2] == 3'd6, "RPLU record 2 sel mismatch");
            check(seen_material[2] == 8'd1, "RPLU record 2 material mismatch");
            check(seen_addr[2] == 10'h3FF, "RPLU record 2 addr mismatch");
            check(seen_data[2] == 64'h0000_0000_0000_0001, "RPLU record 2 data mismatch");
        end

        if (errors == 0) begin
            $display("PASS");
        end else begin
            $display("FAIL: %0d errors", errors);
        end
        $finish;
    end
endmodule
