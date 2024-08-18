#!/bin/sh

# Check our project: formatting, linting, testing, building, etc.
# Good to call this from .git/hooks/pre-commit

set -e

# work from the root of the repo
cd "$(dirname "$0")"

echo "Checking Python"
ruff check
ruff format --check

echo "checking Web UI"
cd src/web_ui
npm run format_check
npm run lint
npm run check
cd ../..

echo "checking Core: build, test"
cd core
hatch build
hatch test
cd ..

echo "checking Studio: build, test"
cd studio
hatch build
hatch test
cd ..
