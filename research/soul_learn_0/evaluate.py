import copy
import json
import os
import sys
from learner import initial, observe, infer, recall, serialize, load, predict
from scenarios import TRAIN, PRE_HELDOUT, COUNTER, POST_HELDOUT, observed, truth

def score(state, cases):
    return [{'case':c,'prediction':infer(state,c),'truth':truth(c), 'correct':infer(state,c)['answer']==truth(c)} for c in cases]

def run():
    state=initial(); unknown=copy.deepcopy(state)
    for x in TRAIN: state=observe(state,observed(x))
    trained=copy.deepcopy(state)
    pre=score(state,PRE_HELDOUT)
    counter_prediction=infer(state,COUNTER)
    state=observe(state,observed(COUNTER))
    revised=copy.deepcopy(state)
    post=score(state,POST_HELDOUT)
    restored=load(serialize(state))
    # Memorization baseline only looks up exact entity IDs, receiving same observations.
    seen={x['id']:x['outcome'] for x in state['observations']}
    baseline=[{'id':x['id'],'answer':seen.get(x['id']),'truth':truth(x)} for x in POST_HELDOUT]
    # Conflicting evidence for identical features forces all candidates out.
    inconsistent=observe(revised,{**TRAIN[0],'id':'contradiction_control','outcome':False})
    return {'initial_state':unknown,'trained_state':trained,'pre_heldout':pre,
      'counter_before_feedback':{'prediction':counter_prediction,'truth':truth(COUNTER),'case':COUNTER},
      'revised_state':revised,'post_heldout':post,'restored_state':restored,
      'memorization_only_post':baseline,
      'metrics':{'training_recall':sum(recall(trained,x['id'])==truth(x) for x in TRAIN),
        'training_total':len(TRAIN),'pre_heldout_correct':sum(x['correct'] for x in pre),
        'pre_heldout_total':len(pre),'counter_prediction_correct':counter_prediction['answer']==truth(COUNTER),
        'revision_changed_hypothesis':trained['active']!=revised['active'],
        'prior_hypothesis_rejected_by_counter':revised['rejected'].get(trained['active'])==COUNTER['id'],
        'post_heldout_correct':sum(x['correct'] for x in post),'post_heldout_total':len(post),
        'restored_exactly':restored==revised,'restored_post_equal':score(restored,POST_HELDOUT)==post},
      'controls':{'initial_unknown':unknown['status']=='unknown',
        'initial_ambiguity_unresolved':trained['status']=='unresolved',
        'rejected_retains_counterexample':revised['rejected'].get('linked')==COUNTER['id'],
        'no_counter_no_revision':trained['active']=='linked',
        'contradiction_unresolved_not_false':inconsistent['status']=='unresolved' and infer(inconsistent,POST_HELDOUT[0])['answer'] is None,
        'memorizer_abstains_unseen':all(x['answer'] is None for x in baseline)}}

def main(path):
    os.makedirs(path,exist_ok=True); result=run()
    with open(os.path.join(path,'results.json'),'w') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps({'metrics':result['metrics'],'controls':result['controls']},indent=2,sort_keys=True))
if __name__=='__main__': main(sys.argv[1])
