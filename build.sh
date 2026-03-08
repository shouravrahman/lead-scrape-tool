#!/bin/bash

# Stop the script if any command fails
set -e

echo "🚀 Starting pre-push build check..."

echo "🏗️  1. Checking syntax..."
# Compiles to bytecode to catch syntax errors. -q is quiet.
python3 -m compileall -q .

echo "🧹 2. Linting (Ruff)..."
# Checks for errors (E), pyflakes (F), warnings (W).
ruff check . --select E,F,W --ignore E501

echo "🔍 3. Type Checking (Mypy)..."
mypy . --ignore-missing-imports --exclude venv

echo "✅ Build passed! Ready to push."
