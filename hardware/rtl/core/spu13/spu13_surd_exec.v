// Canonical 0x70..0x77 extension frontend; no scalar/Quadray register overlay.
module spu13_surd_exec (
    input wire clk,rst,start, input wire [63:0] word,
    output reg busy,retire_valid,write_valid,read_valid,
    output reg [3:0] status, output reg [2:0] retire_dst,
    output reg [31:0] read_data
);
    wire [2:0] op=word[58:56];
    wire [7:0] dst=word[55:48],sa=word[47:40],sb=word[31:24];
    reg [2:0] held_dst;
    wire [191:0] qa,qb,staged,arith_result;
    wire va,vb,slice_ok,load_ok,arith_done;
    wire [3:0] arith_status,phase;
    wire rescue_request,normalization_start;
    wire arithmetic=(op>=3 && op<=6);
    wire bad_reserved=word[7:0]!=0 ||
        (op==0 ? sa>=6 : op==1 ? (sa!=0 || word[39:8]!=0) :
         op==2 ? (sa>=6 || word[39:8]!=0) :
         op>=3 && op<=5 ? (sa>=8 || sb>=8 || word[39:32]!=0 || word[23:8]!=0) :
         op==6 ? (sa>=8 || word[39:8]!=0) :
         (dst!=0 || sa!=0 || word[39:8]!=0));
    wire encoding_ok=(dst<8 && !bad_reserved);
    wire operands_ok=va && (op==6 || vb);
    wire accept=start && !busy && !rst;
    wire arith_start=accept && encoding_ok && arithmetic && operands_ok;
    wire load_commit=accept && encoding_ok && op==1;
    wire bank_we=!rst && ((arith_done && busy && arith_status==0) ||
                         (load_commit && load_ok));
    wire [2:0] bank_wa=(arith_done && busy) ? held_dst:dst[2:0];
    wire [191:0] bank_wd=(arith_done && busy) ? arith_result:staged;
    spu13_surd_bank bank (.clk(clk),.rst(rst),
        .ra(op==2 ? dst[2:0]:sa[2:0]),.rb(sb[2:0]),.qa(qa),.qb(qb),
        .valid_a(va),.valid_b(vb),.we(bank_we),.wa(bank_wa),.wd(bank_wd));
    spu13_surd_load loader (.clk(clk),.rst(rst),
        .slice_en(accept && encoding_ok && op==0),.commit_en(load_commit),
        .target(dst[2:0]),.slice(sa[2:0]),.payload(word[39:8]),
        .slice_ok(slice_ok),.commit_ok(load_ok),.tuple(staged));
    spu13_surd_arith arithmetic_unit (.clk(clk),.rst(rst),.start(arith_start),
        .op(op),.lhs(qa),.rhs(qb),.done(arith_done),.status(arith_status),
        .result(arith_result),.phase(phase),.rescue_request(rescue_request),
        .normalization_start(normalization_start));
    always @(posedge clk) begin
        if(rst) begin
            busy<=0;retire_valid<=0;write_valid<=0;read_valid<=0;
            status<=0;retire_dst<=0;held_dst<=0;read_data<=0;
        end else begin
            retire_valid<=0;write_valid<=0;read_valid<=0;
            if(arith_done && busy) begin
                busy<=0;retire_valid<=1;status<=arith_status;
                retire_dst<=held_dst;write_valid<=arith_status==0;
            end else if(accept) begin
                retire_dst<=dst[2:0];
                if(!encoding_ok) begin retire_valid<=1;status<=4;end
                else if(arithmetic) begin
                    if(!operands_ok) begin retire_valid<=1;status<=1;end
                    else begin busy<=1;held_dst<=dst[2:0];end
                end else begin
                    retire_valid<=1;
                    case(op)
                        0: status<=slice_ok ? 0:1;
                        1: begin status<=load_ok ? 0:1;write_valid<=load_ok;end
                        2: begin
                            status<=va ? 0:1;
                            if(va) begin read_valid<=1;read_data<=qa[32*sa[2:0] +:32];end
                        end
                        7: begin read_valid<=1;read_data<={28'd0,status};end
                        default: status<=4;
                    endcase
                end
            end
        end
    end
endmodule
