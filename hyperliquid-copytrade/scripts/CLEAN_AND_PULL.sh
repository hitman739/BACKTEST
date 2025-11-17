#!/bin/bash

# Clean and Pull Script for Mac
# This script safely cleans your repo and pulls the latest changes

echo "=================================================="
echo "🧹 CLEANING AND PULLING LATEST CHANGES"
echo "=================================================="
echo ""

# Navigate to repo root (script está en scripts/, subimos un nivel)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

echo "📍 Working in: $REPO_ROOT"
echo ""

# Step 1: Show current status
echo "1️⃣  Current Git Status:"
echo "---------------------------------------------------"
git status
echo ""

# Step 2: Stash any uncommitted changes (safety measure)
echo "2️⃣  Stashing any local changes..."
echo "---------------------------------------------------"
if git diff-index --quiet HEAD --; then
    echo "✅ No local changes to stash"
else
    git stash push -m "Auto-stash before pull $(date '+%Y-%m-%d %H:%M:%S')"
    echo "✅ Local changes stashed"
fi
echo ""

# Step 3: Clean untracked files and directories
echo "3️⃣  Cleaning untracked files..."
echo "---------------------------------------------------"
echo "The following files will be removed:"
git clean -n -d
echo ""
read -p "⚠️  Proceed with cleaning? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git clean -f -d
    echo "✅ Untracked files cleaned"
else
    echo "⏭️  Skipped cleaning"
fi
echo ""

# Step 4: Reset to match remote
echo "4️⃣  Resetting to match remote..."
echo "---------------------------------------------------"
git fetch origin claude/fix-copytrading-simulator-016Rwzzxe4AenGmWU5Qw3sqH
git reset --hard origin/claude/fix-copytrading-simulator-016Rwzzxe4AenGmWU5Qw3sqH
echo "✅ Reset to match remote"
echo ""

# Step 5: Pull latest changes
echo "5️⃣  Pulling latest changes..."
echo "---------------------------------------------------"
git pull origin claude/fix-copytrading-simulator-016Rwzzxe4AenGmWU5Qw3sqH
echo "✅ Pull complete"
echo ""

# Step 6: Show final status
echo "6️⃣  Final Git Status:"
echo "---------------------------------------------------"
git status
echo ""

echo "=================================================="
echo "✅ REPOSITORY IS CLEAN AND UP TO DATE"
echo "=================================================="
echo ""
echo "Latest commits:"
git log --oneline -3
echo ""
echo "To view stashed changes (if any):"
echo "  git stash list"
echo "  git stash show stash@{0}"
echo "  git stash pop  # to restore"
echo ""
