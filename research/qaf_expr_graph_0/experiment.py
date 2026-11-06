"""Describe one mathematical workload under eager, DAG and polynomial views."""
from research.qaf_expr_graph_0.model import (X, U, V, CANCEL, CONJ_PRODUCT,
    NORM_X, FACTOR_ORIGINAL, FACTOR, eval_graph, normal, nodes, exact_box)


def coefficient_bits(n):
    n = int(n)
    return (n if n >= 0 else ~n).bit_length() + 1


def show(name, node):
    form = normal(node)
    vals = {'x': (1, 2), 'y': (2, -1)}
    print(name, 'eager=', eval_graph(node, vals),
          'dag_nodes=', len(nodes(node)),
          'canonical_terms=', (len(form[0]),len(form[1])),
          'coefficients=', form)


def main():
    for name, node in [('cancel', CANCEL), ('x', X), ('conjugate_product', CONJ_PRODUCT),
                       ('norm_x', NORM_X), ('original', FACTOR_ORIGINAL), ('factored', FACTOR)]:
        show(name, node)
    print('cancel_input_box_bounds=', exact_box(CANCEL, ((-2,2),)*4))
    print('factored_input_box_bounds=', exact_box(FACTOR_ORIGINAL, ((-2,2),)*4))
    state={'x': ((1<<63)-1,0), 'y': (0,0)}
    first=eval_graph(CANCEL.args[0],state)
    final=eval_graph(CANCEL,state)
    print('overflow_witness first=',first,'first_bits=',tuple(map(coefficient_bits,first)), 'final=',final)
    print('expression DAG and normal form are mathematical, not executable instructions')

if __name__=='__main__': main()
