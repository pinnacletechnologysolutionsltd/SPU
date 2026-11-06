"""Registered claims and independently listed expected outcomes."""
import copy
from checker import manifest, digest
from producer import LANG, RULES, claim, train

def obs(id, linked, fixed, outcome):
    return {'id':id,'kind':'observation','linked':linked,'fixed':fixed,'outcome':outcome}
A=obs('a',True,True,True); B=obs('b',False,True,False); C=obs('c',True,False,False)
D=obs('d',True,True,False)
FACT={'id':'f','kind':'fact','proposition':['key','inside','box']}
R1={'id':'r1','kind':'relation','left':'A','relation':'subset','right':'B'}
R2={'id':'r2','kind':'relation','left':'B','relation':'subset','right':'C'}

def setup(name, evidence, c, expected, finding=None):
    m=manifest(evidence,LANG,RULES)
    return {'name':name,'records':copy.deepcopy(evidence),'language':copy.deepcopy(LANG),
      'rules':copy.deepcopy(RULES),'trusted_manifest':m,'trusted_anchor':digest(m),
      'claim':c,'expected':expected,'finding':finding}

def fixtures():
    pre=[A,B]; post=[A,B,C]
    cases=[
      setup('direct_valid',[FACT],claim('direct',refs=['f'],proposition=['key','inside','box']),'SUPPORTED'),
      setup('direct_unrelated',[FACT],claim('direct',refs=['f'],proposition=['key','inside','case']),'UNSUPPORTED'),
      setup('derived_valid',[R1,R2],claim('deduction',refs=['r1','r2'],rule='transitive',proposition=['A','subset','C']),'SUPPORTED'),
      setup('derived_bad_chain',[R1,R2],claim('deduction',refs=['r2','r1'],rule='transitive',proposition=['A','subset','C']),'UNSUPPORTED'),
      setup('missing_premise',[R1,R2],claim('deduction',refs=['r1'],rule='transitive',proposition=['A','subset','C']),'UNKNOWN'),
      setup('unsupported_rule',[R1,R2],claim('deduction',refs=['r1','r2'],rule='imaginary',proposition=['A','subset','C']),'UNVERIFIED'),
      setup('provisional_multiple',pre,claim('survivors',survivors=train(pre),unique=False),'SUPPORTED','MULTIPLE_SURVIVORS'),
      setup('forged_unique',pre,claim('survivors',survivors=train(pre),unique=True),'UNSUPPORTED','MULTIPLE_SURVIVORS'),
      setup('incorrect_elimination',pre,claim('survivors',survivors=['linked'],unique=False),'UNSUPPORTED'),
      setup('rejection_valid',post,claim('reject',hypothesis='linked',refs=['c']),'SUPPORTED','CONTRADICTED'),
      setup('false_counterexample',post,claim('reject',hypothesis='linked',refs=['a']),'UNSUPPORTED','CONSISTENT'),
      setup('incorrect_retention',post,claim('survivors',survivors=['linked','linked_and_fixed'],unique=False),'UNSUPPORTED'),
      setup('revised_unique',post,claim('survivors',survivors=train(post),unique=True),'SUPPORTED','UNIQUE_WITHIN_DECLARED_HYPOTHESIS_AND_EVIDENCE_BOUNDARY'),
      setup('zero_survivors',[A,D],claim('survivors',survivors=[],unique=False),'SUPPORTED','NO_SURVIVORS'),
      setup('unique_contradicted',post,claim('survivors',survivors=['linked'],unique=True),'UNSUPPORTED'),
      setup('prediction_derived_incorrect_empirically',pre,claim('prediction',hypothesis='linked',features={'linked':True,'fixed':False},prediction=True),'SUPPORTED'),
      setup('prediction_invalid',pre,claim('prediction',hypothesis='linked',features={'linked':True,'fixed':False},prediction=False),'UNSUPPORTED'),
      setup('forged_reference',post,claim('reject',hypothesis='linked',refs=['missing']),'UNKNOWN'),
    ]
    incomplete=setup('incomplete_false_unique',[A,B,C,D],claim('survivors',survivors=['linked_and_fixed'],unique=True),'UNKNOWN'); incomplete['records']=copy.deepcopy(post);cases.append(incomplete)
    missing=setup('missing_record',post,claim('survivors',survivors=[],unique=False),'UNKNOWN');missing['records'].pop();cases.append(missing)
    bad=setup('altered_membership',post,claim('survivors',survivors=[],unique=False),'INVALID_EVIDENCE');bad['records'][0]['id']='other';cases.append(bad)
    sublang=setup('substituted_language',post,claim('survivors',survivors=[],unique=False),'INVALID_EVIDENCE');sublang['language']['candidates']['linked']='0';cases.append(sublang)
    subrules=setup('substituted_rules',post,claim('survivors',survivors=[],unique=False),'INVALID_EVIDENCE');subrules['rules']['inference']=[];cases.append(subrules)
    noanchor=setup('missing_anchor',post,claim('survivors',survivors=[],unique=False),'UNKNOWN');noanchor['trusted_anchor']=None;cases.append(noanchor)
    badanchor=setup('invalid_anchor',post,claim('survivors',survivors=[],unique=False),'INVALID_EVIDENCE');badanchor['trusted_anchor']='0'*64;cases.append(badanchor)
    return cases
