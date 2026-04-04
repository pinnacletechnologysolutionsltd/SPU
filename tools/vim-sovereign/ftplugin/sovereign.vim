" SPU-13 Sovereign Engine — Vim/Neovim file-type settings
" File: ftplugin/sovereign.vim

setlocal commentstring=;\ %s
setlocal tabstop=4
setlocal shiftwidth=4
setlocal expandtab
setlocal textwidth=80

" Run current file with spu_vm if the binary is present relative to cwd
if executable('./software/vm/spu_vm')
  nnoremap <buffer> <F5> :!./software/vm/spu_vm %<CR>
  nnoremap <buffer> <leader>p :!./software/vm/spu_vm % --proof<CR>
endif
