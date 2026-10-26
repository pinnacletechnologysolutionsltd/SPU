"""Directed canonical Python/C++ control compatibility; no RTL parity claim."""
import ast
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from software import spu_vm as vm
from software.tools import spu13_asm as asm
for module in (vm,asm):
    assert module.OPCODES['CALL']==0x20 and module.OPCODES['RET']==0x21
    assert module.OPCODES['QREAD']==0x22 and 'COND' not in module.OPCODES
    tree=ast.parse(Path(module.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='OPCODES' for t in node.targets):
            keys=[k.value for k in node.value.keys if isinstance(k,ast.Constant)]
            assert all(keys.count(k)==1 for k in ('CALL','RET','QREAD')), 'Duplicate canonical control mnemonic'
for assemble in (vm.assemble_source,lambda s:asm.assemble(s,fold=False)[0]):
    try:assemble('COND R0, 0')
    except (ValueError,asm.AssemblyError):pass
    else:raise AssertionError('Ambiguous COND accepted')
# Nested CALL/RET, return-PC, empty stack, QREAD distinct from RET.
words=[0x2000000003000000,0x0600000008000000,0xff00000000000000,
       0x2000000006000000,0x0001000009000000,0x2100000000000000,
       0x0002000007000000,0x2100000000000000]
core=vm.SPUCore(verbose=False);core.load(words);core.run()
assert core.regs[1].a==9 and core.regs[2].a==7 and not core.call_stack
core=vm.SPUCore(verbose=False);core.load([0x2100000000000000]);core.run();assert core.halted
core=vm.SPUCore(verbose=False);core.qregs[1]=vm.QuadrayVector(vm.RationalSurd(3),vm.RationalSurd(),vm.RationalSurd(),vm.RationalSurd())
core.load([0x2202010000000000]);core.run();assert core.qregs[2].a.a==3
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    cpp=tmp/'check.cpp';binary=tmp/'check'
    cpp.write_text('#define main vm_cli_main\n#include "'+str(ROOT/'software/vm/spu_vm.cpp')+'"\n#undef main\n#include <cassert>\nint main(){\n'
        'assert(OPCODES.at("CALL")==0x20 && OPCODES.at("RET")==0x21);\n'
        'assert(assemble_line({"QREAD","QR2","QR1"},1,{})==0x2202010000000000ULL);\n'
        'SPUCore c(256,false); c.load({'+','.join(hex(w)+'ULL' for w in words)+'}); c.run();\n'
        'assert(c.regs[1].a==9 && c.regs[2].a==7 && c.call_stack.empty());\n'
        'SPUCore q(256,false); q.qregs[1].a=RationalSurd(3); q.load({0x2202010000000000ULL}); q.run(); assert(q.qregs[2].a.a==3);\n'
        'SPUCore e(256,false); e.load({0x2100000000000000ULL}); e.run(); assert(e.halted);\n'
        'try {assemble_line({"COND","R0","0"},1,{});} catch(const std::runtime_error&) {return 0;} return 1; }\n')
    subprocess.run(['g++','-std=c++17',str(cpp),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
    # CLI rejects legacy source without aborting or executing a partial program.
    legacy=tmp/'legacy.sas';legacy.write_text('LD R0, 1, 0\nCOND R0, 0\n')
    subprocess.run(['g++','-std=c++17',str(ROOT/'software/vm/spu_vm.cpp'),'-o',str(binary)],check=True)
    rejected=subprocess.run([str(binary),str(legacy)],capture_output=True)
    assert rejected.returncode==1 and b'COND has no canonical encoding' in rejected.stderr
    header=ROOT/'software/common/include/spu_lithic_l.h'
    cpp.write_text('#include "'+str(header)+'"\nstatic_assert((L_CALL(1)>>56)==0x20);\nstatic_assert((L_RET()>>56)==0x21);\nint main(){}\n')
    subprocess.run(['g++','-std=c++17',str(cpp),'-o',str(binary)],check=True)
    cpp.write_text('#include "'+str(header)+'"\nint main(){L_COND(0,1);}\n')
    bad=subprocess.run(['g++','-std=c++17',str(cpp),'-o',str(binary)],capture_output=True)
    assert bad.returncode!=0 and b'deleted' in bad.stderr
print('PASS canonical control: Python/C++, nested returns, QREAD, COND rejection and constructor diagnostics')
