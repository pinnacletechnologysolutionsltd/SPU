# Derives the handler-only negative control (IDNT handler present, Stage-B chain mirror removed)
# from the committed spu13_core.v. Usage: python3 make_handler_only_control.py <in.v> <out.v>
import sys
t = open(sys.argv[1]).read()
t = t.replace("        core_idnt_opcode ||                 // IDNT (load of identity)\n", "", 1)
for c in "abcd":
    t = t.replace(f"core_idnt_opcode ? {'32' + chr(39) + 'd1' if c == 'a' else '32' + chr(39) + 'd0'} : ", "", 1)
open(sys.argv[2], 'w').write(t)
