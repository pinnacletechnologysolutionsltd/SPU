"""One deterministic world; only the evaluator can call truth()."""
def case(id,linked,fixed): return {'id':id,'linked':linked,'fixed':fixed}
def truth(c): return c['linked'] and c['fixed']
def observed(c): return {**c,'outcome':truth(c)}
TRAIN = [case('train_linked_fixed',True,True), case('train_unlinked_fixed',False,True)]
PRE_HELDOUT = [case('pre_new_fixed',True,True),case('pre_new_unlinked',False,True)]
COUNTER = case('feedback_detachable',True,False)
POST_HELDOUT = [case('post_new_detachable',True,False),case('post_new_fixed',True,True),case('post_new_unlinked',False,False)]
