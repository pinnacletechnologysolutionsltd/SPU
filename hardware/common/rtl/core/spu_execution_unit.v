// SPU-13 Pipelined Execution Unit (v1.0)
// Objective: Manage instruction lifecycle through the 3-cycle DSP pipeline.
// Standard: SovereignBus Interface, RationalSurd arithmetic.

module spu_execution_unit (
    input  wire clk,
    input  wire reset,
    
    // Decoder Interface
    input  wire [7:0]  dec_bus_addr,
    input  wire [31:0] dec_bus_data,
    input  wire        dec_bus_wen,
    input  wire        dec_bus_ren,
    input  wire        dec_bus_ready,
    input  wire        dec_trigger_exec,
    
    // Manifold Bus Interface
    output wire [7:0]  bus_addr,
    output wire [31:0] bus_data,
    output wire        bus_wen,
    output wire        bus_ren,
    input  wire        bus_ready,

    // Scoreboard Feedback
    output wire        writeback_valid,
    output wire [7:0]  writeback_reg
);

    // Pipeline Registers
    // Stage 1: Decoded Instruction Latch
    reg [7:0]  pipe_opcode;
    reg [7:0]  pipe_r1_idx;
    reg [7:0]  pipe_r2_idx;
    reg [15:0] pipe_p1_a, pipe_p1_b;
    reg        pipe_exec_valid;

    // Stage 2: Operands Ready
    reg [15:0] op1_a, op1_b;
    reg [15:0] op2_a, op2_b;
    reg [7:0]  op_r1_idx, op_r2_idx;

    // Stage 3: Result Ready
    reg [15:0] res_a, res_b;
    reg        res_ready;

    // State Machine: IDLE -> REQUEST -> EXECUTE -> WRITEBACK -> WAIT
    localparam S_IDLE       = 3'b000;
    localparam S_REQUEST    = 3'b001;
    localparam S_EXECUTE    = 3'b010;
    localparam S_WRITEBACK  = 3'b011;
    localparam S_WAIT       = 3'b100;
    reg [2:0] state;

    // Manifold Bus Instance
    // This instance will handle the actual read/write to the register bank.
    // It will assert 'bus_ready' when the transaction is complete.
    spu_manifold_bus u_manifold_bus (
        .clk(clk),
        .reset(reset),
        .bus_addr(bus_addr),
        .bus_data(bus_data),
        .bus_wen(bus_wen),
        .bus_ren(bus_ren),
        .bus_ready(bus_ready),
        .exec_valid(trigger_exec)
    );

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= S_IDLE;
            // Clear pipeline registers
            pipe_opcode <= 8'hFF;
            pipe_r1_idx <= 0; pipe_r2_idx <= 0;
            pipe_p1_a <= 0; pipe_p1_b <= 0;
            pipe_exec_valid <= 0;
            
            op1_a <= 0; op1_b <= 0;
            op2_a <= 0; op2_b <= 0;
            op_r1_idx <= 0; op_r2_idx <= 0;
            
            res_a <= 0; res_b <= 0;
            res_ready <= 0;
        end else begin
            // State machine for instruction execution
            case (state)
                S_IDLE: begin
                    if (dec_trigger_exec) begin
                        // Latch instruction from decoder
                        pipe_opcode <= dec_bus_addr; // Using bus_addr as opcode temporarily
                        pipe_r1_idx <= dec_bus_addr; // Store R1 index
                        pipe_r2_idx <= dec_bus_addr; // Store R2 index
                        pipe_p1_a   <= dec_bus_data[31:16];
                        pipe_p1_b   <= dec_bus_data[15:0];
                        pipe_exec_valid <= 1;
                        state <= S_REQUEST;
                    end
                end
                S_REQUEST: begin
                    // Issue read requests for operands if needed (R2 for MUL/ADD/etc)
                    // For now, assume operands are available via direct bus access (placeholders)
                    // This part needs to be replaced with actual bus read logic.
                    op1_a <= pipe_p1_a; // Placeholder - needs read from Manifold Bus
                    op1_b <= pipe_p1_b; // Placeholder - needs read from Manifold Bus
                    op2_a <= pipe_p1_a; // Placeholder - needs read from Manifold Bus
                    op2_b <= pipe_p1_b; // Placeholder - needs read from Manifold Bus
                    
                    // Trigger the SMUL unit
                    if (pipe_exec_valid) begin
                        state <= S_EXECUTE;
                    end
                end
                S_EXECUTE: begin
                    // Pass operands to the SMUL unit
                    // Placeholder: Assume SMUL outputs are available here
                    // res_a <= smul_unit.res_a;
                    // res_b <= smul_unit.res_b;
                    // res_ready <= smul_unit.ready;
                    
                    // Dummy values for now
                    res_a <= pipe_p1_a;
                    res_b <= pipe_p1_b;
                    res_ready <= 1;
                    
                    state <= S_WRITEBACK;
                end
                S_WRITEBACK: begin
                    // Write result back to Manifold Bus
                    if (res_ready) begin
                        bus_addr <= pipe_r1_idx; // Write to R1
                        bus_data <= {res_a, res_b}; // Pack result
                        bus_wen <= 1;
                        state <= S_WAIT;
                    end
                end
                S_WAIT: begin
                    if (bus_ready) begin
                        bus_wen <= 0;
                        trigger_exec <= 1;
                        state <= S_IDLE;
                    end
                end
            endcase
        end
    end

endmodule
