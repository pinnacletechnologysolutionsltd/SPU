from pathlib import Path
import re
import subprocess
import sys

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text()

def esc(s):
    return (s.replace('\\', r'\textbackslash{}').replace('&', r'\&')
             .replace('%', r'\%').replace('#', r'\#').replace('_', r'\_')
             .replace('{', r'\{').replace('}', r'\}').replace('~', r'\textasciitilde{}')
             .replace('^', r'\textasciicircum{}'))

def inline(s):
    parts = []
    pos = 0
    pat = re.compile(r'\[([^]]+)\]\(([^)]+)\)|`([^`]+)`|\*\*([^*]+)\*\*')
    for m in pat.finditer(s):
        parts.append(esc(s[pos:m.start()]))
        if m.group(1):
            parts.append(r'\href{' + m.group(2) + '}{' + esc(m.group(1)) + '}')
        elif m.group(3):
            parts.append(r'\path{' + m.group(3).replace('\\', '/') + '}')
        else:
            parts.append(r'\textbf{' + esc(m.group(4)) + '}')
        pos = m.end()
    parts.append(esc(s[pos:]))
    return ''.join(parts)

lines = text.splitlines()
body = []
date_text = ''
i = 0
while i < len(lines):
    line = lines[i]
    if i == 0:
        i += 1
        continue
    meta = re.match(r'^\*\*(Author|Affiliation|Location|Date|AI disclosure):\*\*\s*(.*)$', line)
    if meta:
        block = [meta.group(2)]
        i += 1
        while (i < len(lines) and lines[i].strip()
               and not lines[i].startswith('#')
               and not re.match(r'^\*\*(Author|Affiliation|Location|Date|AI disclosure):', lines[i])):
            block.append(lines[i].strip())
            i += 1
        if meta.group(1) == 'Date':
            date_text = ' '.join(block).strip()
        if meta.group(1) == 'AI disclosure':
            body.append(r'\noindent\textbf{AI disclosure.} ' + inline(' '.join(block).strip()))
        continue
    if not line.strip():
        i += 1
        continue
    if line.startswith('\\['):
        math = []
        i += 1
        while i < len(lines) and not lines[i].startswith('\\]'):
            math.append(lines[i].strip())
            i += 1
        if i < len(lines):
            i += 1
        body.append(r'\(' + ' '.join(math) + r'\)')
        continue
    if line.startswith('\\]') or line.startswith('  '):
        body.append(line)
        i += 1
        continue
    m = re.match(r'^(#{1,6})\s+(.+)$', line)
    if m:
        level = len(m.group(1))
        cmd = 'section' if level == 2 else 'subsection' if level == 3 else 'subsubsection'
        body.append('\\' + cmd + '{' + inline(m.group(2)) + '}')
        i += 1
        continue
    if line.startswith('|'):
        rows = []
        while i < len(lines) and lines[i].startswith('|'):
            cells = [x.strip() for x in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?', x) for x in cells):
                rows.append(cells)
            i += 1
        n = max(map(len, rows))
        body += [r'\begin{center}', r'\scriptsize', r'\sloppy', r'\begin{tabularx}{\linewidth}{@{}' + 'Y' * n + r'@{}}', r'\toprule']
        for j, row in enumerate(rows):
            row += [''] * (n - len(row))
            body.append(' & '.join(inline(x) for x in row) + r' \\')
            if j == 0:
                body.append(r'\midrule')
        body += [r'\bottomrule', r'\end{tabularx}', r'\end{center}']
        continue
    if re.match(r'^[-*] ', line):
        body.append(r'\begin{itemize}')
        while i < len(lines) and re.match(r'^[-*] ', lines[i]):
            body.append(r'\item ' + inline(lines[i][2:]))
            i += 1
        body.append(r'\end{itemize}')
        continue
    if re.match(r'^\d+\. ', line):
        body.append(r'\begin{enumerate}')
        while i < len(lines) and re.match(r'^\d+\. ', lines[i]):
            body.append(r'\item ' + inline(re.sub(r'^\d+\. ', '', lines[i])))
            i += 1
        body.append(r'\end{enumerate}')
        continue
    para = [line.strip()]
    i += 1
    while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,6})\s|^\||^[-*] |^\d+\. |^\\\[|^\\\]', lines[i]):
        para.append(lines[i].strip())
        i += 1
    body.append(inline(' '.join(para)))

tex = r'''\documentclass[11pt]{article}
\usepackage{fontspec}
\setmainfont{DejaVu Serif}
\setmonofont{DejaVu Sans Mono}[Scale=MatchLowercase]
\usepackage[a4paper,margin=25mm]{geometry}
\usepackage{amsmath,amssymb,booktabs,tabularx,hyperref,microtype}
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
\setcounter{secnumdepth}{0}
\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue}
\title{A theorem-licensed typestate machine for exact rotation algebra}
\author{John Curley\\Independent Researcher, SPU-13 Project\\Wellington, New Zealand}
\date{''' + esc(date_text) + r'''}
\begin{document}
\maketitle
''' + '\n\n'.join(body) + r'''
\end{document}
'''
out.write_text(tex)
subprocess.run(['xelatex', '-interaction=nonstopmode', '-halt-on-error', '-output-directory', str(out.parent), str(out)], check=True)
