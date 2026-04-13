`timescale 1ns/1ps
module rational_sine_provider_tb;
    parameter DEPTH = 4096;
    reg [$clog2(DEPTH)-1:0] addr;

    wire signed [31:0] p16_out, q16_out;
    wire signed [31:0] p32_out, q32_out;

    // instantiate both provider variants
    rational_sine_provider #(.DEPTH(DEPTH), .HIGH_PRECISION(0)) PROVIDER16(.addr(addr), .pout(p16_out), .qout(q16_out));
    rational_sine_provider #(.DEPTH(DEPTH), .HIGH_PRECISION(1)) PROVIDER32(.addr(addr), .pout(p32_out), .qout(q32_out));

    real SCALE16 = 32767.0;
    real SCALE32 = 2147483647.0;
    real SQRT3 = 1.7320508075688772;

    integer i;
    real orig, recon16, recon32, err16, err32;
    real sum16, sum32, max16, max32;
    integer max_i16, max_i32;

    function real compute_s3;
        input real base_s;
        real s;
        begin
            s = base_s;
            compute_s3 = s * (3.0 - 4.0*s) * (3.0 - 4.0*s);
        end
    endfunction

    // simple absolute value for reals (iverilog-friendly)
    function real abs_r;
        input real x;
        begin
            if (x < 0.0) abs_r = -x; else abs_r = x;
        end
    endfunction

    initial begin
        sum16 = 0.0; sum32 = 0.0; max16 = 0.0; max32 = 0.0; max_i16 = -1; max_i32 = -1;
        $display("idx\torig\trecon16\terr16\trecon32\terr32");
        for (i = 0; i < 256; i = i + 1) begin
            addr = i;
            #1;
            orig = compute_s3($itor(i) / $itor(DEPTH));
            recon16 = $itor($signed(p16_out)) / SCALE16 + $itor($signed(q16_out)) / SCALE16 * SQRT3;
            recon32 = $itor($signed(p32_out)) / SCALE32 + $itor($signed(q32_out)) / SCALE32 * SQRT3;
            err16 = orig - recon16;
            err32 = orig - recon32;
            sum16 = sum16 + abs_r(err16);
            sum32 = sum32 + abs_r(err32);
            if (abs_r(err16) > max16) begin max16 = abs_r(err16); max_i16 = i; end
            if (abs_r(err32) > max32) begin max32 = abs_r(err32); max_i32 = i; end
            $display("%0d\t%0f\t%0f\t%0f\t%0f\t%0f", i, orig, recon16, err16, recon32, err32);
        end
        $display("Summary16: mean_err=%e max_err=%e idx=%0d", sum16/256.0, max16, max_i16);
        $display("Summary32: mean_err=%e max_err=%e idx=%0d", sum32/256.0, max32, max_i32);
        $finish;
    end
endmodule
