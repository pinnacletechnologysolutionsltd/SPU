`timescale 1ns/1ps

module spu_gpu_t1r_palette_pair_tb;
    reg clk=0, rst_n=0, rx_valid=0, activate=0;
    reg [7:0] rx_byte=0;
    reg [1:0] winner_id=0;
    wire [1487:0] active_scene, candidate_scene;
    wire commit_pending;
    wire [31:0] active_palettes;
    wire [7:0] selected_palette;
    wire [3:0] unused_r, unused_g, unused_b;
    integer i, lane, failures=0;
    reg active_bank_before;

    spu_scene_loader #(
        .SCENE_BITS(1488), .PAYLOAD_BYTES(186),
        .VALIDATE_WINDOW_START(174), .VALIDATE_WINDOW_BYTES(4),
        .FINAL_BYTE_MAX(8'h0F),
        .VALIDATE_WINDOW2_START(182), .VALIDATE_WINDOW2_BYTES(4),
        .WINDOW2_BYTE_MAX(8'h3F)
    ) loader (
        .clk(clk), .rst_n(rst_n), .rx_byte(rx_byte), .rx_valid(rx_valid),
        .activate_raw_bank(activate), .active_scene(active_scene),
        .candidate_scene(candidate_scene), .commit_pending(commit_pending)
    );

    spu_material_palette_select4 palette (
        .clk(clk), .rst_n(rst_n), .activate_scene(activate),
        .candidate_palettes(32'h07312A1C), .winner_id(winner_id),
        .active_palettes(active_palettes), .selected_palette(selected_palette)
    );

    spu_gpu_top #(
        .DEVICE("A7"), .ENABLE_HDMI(0), .PREPARED_SCENE(1),
        .FOUR_PRIMITIVE_SCENE(1), .T1I_UV_SCENE(1),
        .T1L_PIPELINE_PARTITION(1), .GPU_POST_WINNER_REG(1),
        .T1Q_TRUTH_TABLE_MATERIAL(0), .T1R_PALETTE_PAIR_MATERIAL(1)
    ) gpu (
        .clk_pixel(clk), .clk_tmds(clk), .rst_n(rst_n),
        .scene_rx_byte(8'd0), .scene_rx_valid(1'b0),
        .vga_r(unused_r), .vga_g(unused_g), .vga_b(unused_b)
    );

    always #5 clk=~clk;

    task send_byte(input [7:0] value);
        begin
            @(negedge clk); rx_byte=value; rx_valid=1;
            @(negedge clk); rx_byte=0; rx_valid=0;
        end
    endtask

    task send_packet(input integer bad_index, input [7:0] bad_value);
        reg [7:0] value;
        begin
            send_byte(8'hA5);
            for (i=0;i<186;i=i+1) begin
                value=0;
                if (i>=174 && i<178) value=8'h06;
                if (i>=182 && i<186) begin
                    case (i)
                        182: value=8'h1C;
                        183: value=8'h2A;
                        184: value=8'h31;
                        default: value=8'h07;
                    endcase
                end
                if (i==bad_index) value=bad_value;
                send_byte(value);
            end
        end
    endtask

    task check_rejected(input [8*32-1:0] label_text);
        begin
            if (commit_pending || loader.receiving || loader.payload_count!==0 ||
                loader.active_bank!==active_bank_before) begin
                failures=failures+1;
                $display("FAIL: %0s pending=%b receiving=%b count=%0d bank=%b",
                    label_text,commit_pending,loader.receiving,loader.payload_count,loader.active_bank);
            end
        end
    endtask

    task check_material_colors;
        integer table_index, pair_index, palette_index;
        reg result_bit, expected_r, expected_g, expected_b;
        reg [7:0] palette_byte;
        reg [31:0] palette_words;
        begin
            palette_words=32'h07312A1C;
            force gpu.t1j_registered_uv_shader.selected_uv_valid_q=1'b1;
            force gpu.t1j_registered_uv_shader.selected_u_q=56'd0;
            force gpu.t1j_registered_uv_shader.selected_v_q=56'd0;
            force gpu.t1p_selected_selector_q=8'd0;
            for (palette_index=0;palette_index<4;palette_index=palette_index+1) begin
                palette_byte=palette_words[palette_index*8+:8];
                force gpu.t1r_selected_palette_q=palette_byte;
                for (table_index=0;table_index<16;table_index=table_index+1) begin
                    force gpu.t1o_selected_material_op_q=table_index[7:0];
                    for (pair_index=0;pair_index<4;pair_index=pair_index+1) begin
                        force gpu.t1j_registered_uv_shader.selected_u_q=pair_index[1] ? 56'd1 : 56'd0;
                        force gpu.t1j_registered_uv_shader.selected_v_q=pair_index[0] ? 56'd1 : 56'd0;
                        result_bit=(table_index>>pair_index)&1;
                        expected_r=result_bit ? palette_byte[3] : palette_byte[0];
                        expected_g=result_bit ? palette_byte[4] : palette_byte[1];
                        expected_b=result_bit ? palette_byte[5] : palette_byte[2];
                        #0.1;
                        if (gpu.display_r!=={4{expected_r}} ||
                            gpu.display_g!=={4{expected_g}} ||
                            gpu.display_b!=={4{expected_b}}) begin
                            failures=failures+1;
                            if (failures<8) $display("FAIL: T1r table=%0d pair=%0d palette=%02x RGB=%h%h%h",
                                table_index,pair_index,palette_byte,gpu.display_r,gpu.display_g,gpu.display_b);
                        end
                    end
                end
            end
            force gpu.t1j_registered_uv_shader.selected_uv_valid_q=1'b0;
            #0.1;
            if (gpu.display_r!==0 || gpu.display_g!==0 || gpu.display_b!==0)
                failures=failures+1;
            release gpu.t1j_registered_uv_shader.selected_uv_valid_q;
            release gpu.t1j_registered_uv_shader.selected_u_q;
            release gpu.t1j_registered_uv_shader.selected_v_q;
            release gpu.t1p_selected_selector_q;
            release gpu.t1o_selected_material_op_q;
            release gpu.t1r_selected_palette_q;
        end
    endtask

    initial begin
        check_material_colors();
        repeat(2) @(negedge clk); rst_n=1;
        repeat(2) @(negedge clk);

        active_bank_before=loader.active_bank;
        send_packet(174,8'h10);
        check_rejected("truth-table high nibble accepted");

        active_bank_before=loader.active_bank;
        send_packet(185,8'h40);
        check_rejected("final palette reserved bits accepted");

        send_packet(-1,8'h00);
        if (!commit_pending || candidate_scene[1456+:32]!==32'h07312A1C) begin
            failures=failures+1;
            $display("FAIL: valid 186-byte scene did not commit with palette tuple");
        end
        for (lane=0;lane<4;lane=lane+1) begin
            @(negedge clk); winner_id=lane[1:0]; activate=1;
            @(posedge clk); #0.1;
            case (lane)
                0: if(selected_palette!==8'h1C) failures=failures+1;
                1: if(selected_palette!==8'h2A) failures=failures+1;
                2: if(selected_palette!==8'h31) failures=failures+1;
                3: if(selected_palette!==8'h07) failures=failures+1;
            endcase
            if (active_palettes!==32'h07312A1C) failures=failures+1;
            @(negedge clk); activate=0;
        end
        if (active_scene[1456+:32]!==32'h07312A1C || loader.active_bank!==1'b1)
            failures=failures+1;

        if (failures) $display("FAIL: T1r loader/palette checks failures=%0d",failures);
        else $display("PASS: T1r 186-byte loader windows, final-byte rejection/recovery, four-lane palette commit/select");
        $finish;
    end
endmodule
