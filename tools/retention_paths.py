"""Lexical repository reference normalization; no filesystem mutation."""
from __future__ import annotations

import re
from pathlib import Path

PREFIXES = ('build', 'docs', 'research', 'hardware', 'software', 'examples', 'tools', 'spu_strategy')
TAIL = r'[^\s\x00"\'`<>|,;:{}\[\]()]+'
BOUNDARY = r'(?<![\w./\\-])'


def references(repo: Path, text: str) -> set[str]:
    root = str(repo.resolve()).rstrip('/')
    relative = r'(?:\./)?(?:' + '|'.join(PREFIXES) + ')/' + TAIL
    # Consume entire absolute paths, including external ones, before considering
    # repo-relative tokens. Never rediscover an internal-looking suffix inside one.
    pattern = re.compile(BOUNDARY + '(?:' + re.escape(root) + '/' + TAIL
                         + '|/' + TAIL + '|' + relative + ')')
    result = set()
    for match in pattern.finditer(text):
        token = match.group().rstrip(' .\\')
        if token.startswith('/'):
            if not token.startswith(root + '/'):
                continue
            token = token[len(root) + 1:]
        elif token.startswith('./'):
            token = token[2:]
        if token.split('/', 1)[0] in PREFIXES:
            # Preserve lexical '..' for the caller's unsafe/ambiguous decision.
            result.add(token)
    return result
