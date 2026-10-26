" SPU-13 Synergetic Engine — Vim/Neovim file-type detection
" Detects .sas (Sovereign Assembly) and .lam (Laminar Lang) files.
autocmd BufNewFile,BufRead *.sas setfiletype sovereign
autocmd BufNewFile,BufRead *.lam setfiletype sovereign
