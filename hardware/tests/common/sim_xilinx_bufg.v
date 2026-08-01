// Behavioral BUFG model for board-top simulation.  The synthesis primitive is
// intentionally a blackbox; tests need only its clock-buffer behavior.
module BUFG (
    input  wire I,
    output wire O
);
    assign O = I;
endmodule
