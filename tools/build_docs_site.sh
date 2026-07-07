#!/usr/bin/env bash
# build_docs_site.sh — stage knowledge/ into the MkDocs tree and build the site.
# Local preview:  bash tools/build_docs_site.sh serve
# CI build:       bash tools/build_docs_site.sh
set -e
cd "$(dirname "$0")/.."

# knowledge/ lives at repo root but publishes under docs/knowledge/ (gitignored).
# Repo-root-relative links (../docs/foo.md) become site-relative (../foo.md).
rm -rf docs/knowledge
cp -r knowledge docs/knowledge
find docs/knowledge -name "*.md" -exec sed -i 's#\.\./docs/#../#g' {} +

if [ "$1" = "serve" ]; then
    mkdocs serve
else
    mkdocs build --strict
fi
