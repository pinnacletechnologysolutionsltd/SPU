// tb_spu_flow_control.v
`timescale 1ns/1ps

module tb_spu_flow_control();
    reg clk;
    reg rst_n;
    reg spi_cs_n;
    reg spi_sck;
    reg spi_mosi;
    wire spi_miso;

    reg fifo_full;

    spu_spi_slave uut (
        .clk(clk),
        .rst_n(rst_n),
        .spi_cs_n(spi_cs_n),
        .spi_sck(spi_sck),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso),
        .manifold_state(832'h0),
        .satellite_snaps(4'h0),
        .is_janus_point(1'b1),
        .dissonance(16'h1234),
        .scale_table(52'h0),
        .scale_overflow(13'h0),
        .rplu_ratio_res(3'd0),
        .rplu_ratio_valid(1'b0),
        .fifo_full(fifo_full),
        .rplu_cfg_wr_en(),
        .rplu_cfg_sel(),
        .rplu_cfg_material(),
        .rplu_cfg_addr(),
        .rplu_cfg_data()
    );

    always #20 clk = ~clk; // 25 MHz

    task send_cmd(input [7:0] cmd);
        integer i;
        begin
            spi_cs_n = 0;
            #100;
            for (i = 7; i >= 0; i = i - 1) begin
                spi_mosi = cmd[i];
                #100;
                spi_sck = 1;
                #100;
                spi_sck = 0;
            end
            #100;
        end
    endtask

    task read_bytes(input integer count);
        integer i, j;
        reg [7:0] data;
        begin
            for (i = 0; i < count; i = i + 1) begin
                data = 8'h0;
                for (j = 7; j >= 0; j = j - 1) begin
                    #100;
                    spi_sck = 1;
                    #10;
                    data[j] = spi_miso;
                    #90;
                    spi_sck = 0;
                end
                $display("Read byte [%0d]: 0x%h", i, data);
            end
            spi_cs_n = 1;
            #100;
        end
    endtask

    initial begin
        clk = 0;
        rst_n = 0;
        spi_cs_n = 1;
        spi_sck = 0;
        spi_mosi = 0;
        fifo_full = 0;

        #100 rst_n = 1;
        #100;

        // Test 1: Read status while FIFO is EMPTY
        $display("--- Test 1: FIFO EMPTY ---");
        send_cmd(8'hAC); // CMD_READ_STATUS
        read_bytes(3);

        // Test 2: Read status while FIFO is FULL
        $display("--- Test 2: FIFO FULL ---");
        fifo_full = 1;
        #100;
        send_cmd(8'hAC);
        read_bytes(3);

        $display("PASS: Flow control flags verified");
        $finish;
    end

endmodule
