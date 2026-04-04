" SPU-13 Sovereign Engine — Vim/Neovim syntax highlighting
" File: syntax/sovereign.vim
" Language: Sovereign Assembly (.sas) / Laminar Lang (.lam)
" Maintainer: SPU-13 Project
" Vim 8+ and Neovim compatible

if exists("b:current_syntax")
  finish
endif

" ── Opcodes ─────────────────────────────────────────────────────────────────

" Control-flow opcodes (highlighted as conditionals)
syn keyword sovereignFlowOp JMP SNAP COND CALL RET NOP

" Quadray / geometry opcodes (highlighted as functions)
syn keyword sovereignQuadrayOp QLOAD QADD QROT QNORM QLOG SPREAD HEX EQUIL IDNT JINV ANNE

" Scalar arithmetic opcodes
syn keyword sovereignOpcode LD ADD SUB MUL ROT LOG

" ── Registers ───────────────────────────────────────────────────────────────

" Quadray registers QR0–QR12 (must come before scalar to avoid partial match)
syn match sovereignQRegister '\<QR\([0-9]\|1[0-2]\)\>'

" Scalar registers R0–R25
syn match sovereignRegister '\<R\([0-9]\|1[0-9]\|2[0-5]\)\>'

" ── Literals ────────────────────────────────────────────────────────────────

" Hexadecimal literals: 0x1A, 0xFF
syn match sovereignHex '\<0x[0-9A-Fa-f]\+\>'

" Decimal integers (including negative): 42, -7
syn match sovereignNumber '\<-\?[0-9]\+\>'

" ── Labels ──────────────────────────────────────────────────────────────────

" Label definitions: LOOP: at the start of a line
syn match sovereignLabel '^\s*\w\+:'

" ── Comments ────────────────────────────────────────────────────────────────

" Semicolon comment to end of line
syn match sovereignComment ';.*$'

" ── Highlight links ─────────────────────────────────────────────────────────

hi def link sovereignOpcode      Keyword
hi def link sovereignFlowOp      Conditional
hi def link sovereignQuadrayOp   Function
hi def link sovereignRegister    Identifier
hi def link sovereignQRegister   Type
hi def link sovereignHex         Number
hi def link sovereignNumber      Number
hi def link sovereignLabel       Label
hi def link sovereignComment     Comment

let b:current_syntax = "sovereign"
