// psurd_runctl.v — v0.3 RTL-0B run control (frozen contract §9; RTL-0B plan §2 correction C, D5).
// Owns busy and the run state, drives psurd_core start/budget, and answers START, STATUS and RESULT.
//   IDLE (0)        no run in flight, no record.
//   RUNNING (1)     accepted START until the core's done.
//   FINALIZING (2)  done until the record builder publishes (rec_done).
//   READY (3)       no run in flight, a completed record exists (record-valid = 1).
// START (budget u32 LE): BUSY while RUNNING or FINALIZING; REFUSED reason 8 if image-valid = 0, reason 9 if
// B = 0; otherwise accepted: record-valid is cleared, the run id increments and the core is started. A
// refused or BUSY START changes nothing, so the previous record stays readable.
// RESULT: BUSY while RUNNING or FINALIZING; REFUSED reason 10 if no record; OK with the 213-byte record.
// STATUS (7 bytes): flags (bit 0 image-valid, 1 load-open, 2 record-valid), run state, cause of the
// retained record (FF if none), run id (u32 LE).
module psurd_runctl (
    input  wire clk, rst,
    input  wire cmd_valid,
    input  wire [2:0] cmd,
    input  wire [31:0] budget_in,
    input  wire image_valid, load_open,
    input  wire core_done,
    input  wire [2:0] core_cause,
    input  wire rec_done,                       // one cycle: record complete, CRC included
    output wire busy,
    output wire record_valid,
    output reg  core_start,
    output reg  [31:0] budget,
    output reg  rec_go,                         // one cycle: the core has finished, build the record
    output reg  [55:0] status_bytes,            // snapshot taken when STATUS is answered
    output reg  rsp_valid,
    output reg  [7:0] rsp_status, rsp_reason, rsp_len
);
    localparam OK = 8'h00, REFUSED = 8'h20, BUSY = 8'h22;
    localparam IDLE = 2'd0, RUNNING = 2'd1, FINALIZING = 2'd2, READY = 2'd3;
    reg [1:0] state;
    reg armed;                                  // the core's done has been seen low since START (done is a level)
    reg [31:0] run_id;
    assign busy = state == RUNNING || state == FINALIZING;
    assign record_valid = state == READY;
    task answer(input [7:0] s, input [7:0] r, input [7:0] l); begin
        rsp_valid <= 1'b1; rsp_status <= s; rsp_reason <= r; rsp_len <= l;
    end endtask
    always @(posedge clk) begin
        rsp_valid <= 1'b0; core_start <= 1'b0; rec_go <= 1'b0;
        if (rst) begin
            state <= IDLE; armed <= 1'b0; run_id <= 32'd0; budget <= 32'd0;
            rsp_status <= OK; rsp_reason <= 8'd0; rsp_len <= 8'd0;
        end else begin
            if (state == RUNNING) begin
                if (!core_done) armed <= 1'b1;
                else if (armed) begin state <= FINALIZING; rec_go <= 1'b1; end
            end
            if (state == FINALIZING && rec_done) state <= READY;
            if (cmd_valid) case (cmd)
                3'd4: if (busy) answer(BUSY, 8'd0, 8'd0);
                      else if (!image_valid) answer(REFUSED, 8'd8, 8'd1);
                      else if (budget_in == 32'd0) answer(REFUSED, 8'd9, 8'd1);
                      else begin
                          state <= RUNNING; armed <= 1'b0; core_start <= 1'b1; budget <= budget_in;
                          run_id <= run_id + 32'd1; answer(OK, 8'd0, 8'd0);
                      end
                3'd5: begin
                    status_bytes <= {run_id, record_valid ? {5'd0, core_cause} : 8'hFF, 6'd0, state,
                                     5'd0, record_valid, load_open, image_valid};
                    answer(OK, 8'd0, 8'd7);
                end
                3'd6: if (busy) answer(BUSY, 8'd0, 8'd0);
                      else if (!record_valid) answer(REFUSED, 8'd10, 8'd1);
                      else answer(OK, 8'd0, 8'd213);
                default: ;
            endcase
        end
    end
endmodule
