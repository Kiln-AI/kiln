#!/bin/sh

# Check our project: formatting, linting, testing, building, etc.
# Good to call this from .git/hooks/pre-commit

set -e

# work from the root of the repo
cd "$(dirname "$0")"

headerStart="\n\033[4;34m=== "
headerEnd=" ===\033[0m\n"

echo "${headerStart}Checking Python: Ruff, format, check${headerEnd}"
ruff check
ruff format --check

changed_files=$(git diff --name-only)

if [[ "$changed_files" == *"src/web_ui/"* ]]; then
    echo "${headerStart}Checking Web UI: format, lint, check${headerEnd}"
    cd src/web_ui
    npm run format_check
    npm run lint
    npm run check
    cd ../..
else
    echo "${headerStart}Skipping Web UI: format, lint, check${headerEnd}"
fi

echo "${headerStart}Checking Core: build, test${headerEnd}"
cd libs/core
poetry install
python3 -m pytest tests/
cd ../..

echo "${headerStart}Checking Studio: build, test${headerEnd}"
cd libs/studio
# note: don't install, or it will fetch pypi version of core instead of local
python3 -m pytest tests/
cd ../..

echo "${headerStart}Checking Types${headerEnd}"
cd libs/core
pyright .
cd ../studio
pyright .
cd ../..
