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

if [[ "$changed_files" == *"app/web_ui/"* ]]; then
    echo "${headerStart}Checking Web UI: format, lint, check${headerEnd}"
    cd app/web_ui
    npm run format_check
    npm run lint
    npm run check
    cd ../..
else
    echo "${headerStart}Skipping Web UI: format, lint, check${headerEnd}"
fi

echo "${headerStart}Running Python Tests${headerEnd}"
python3 -m pytest .

echo "${headerStart}Checking Types${headerEnd}"
pyright .
