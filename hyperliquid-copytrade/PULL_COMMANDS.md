# 🧹 CLEAN REPO AND PULL LATEST CHANGES

## ⚡ OPTION 1: Automated Script (Recommended)

Run this single command in your terminal:

```bash
cd ~/path/to/BACKTEST/hyperliquid-copytrade
./CLEAN_AND_PULL.sh
```

This script will:
- ✅ Show current status
- ✅ Stash any uncommitted changes
- ✅ Clean untracked files (with confirmation)
- ✅ Reset to match remote
- ✅ Pull latest changes

---

## 🔧 OPTION 2: Manual Commands

If you prefer to run commands manually:

```bash
# Navigate to repo
cd ~/path/to/BACKTEST/hyperliquid-copytrade

# Check current status
git status

# Stash any uncommitted changes (safety)
git stash

# Clean untracked files
git clean -f -d

# Fetch and reset to remote
git fetch origin claude/fix-copytrading-simulator-016Rwzzxe4AenGmWU5Qw3sqH
git reset --hard origin/claude/fix-copytrading-simulator-016Rwzzxe4AenGmWU5Qw3sqH

# Pull latest
git pull origin claude/fix-copytrading-simulator-016Rwzzxe4AenGmWU5Qw3sqH

# Verify
git status
git log --oneline -3
```

---

## 🔍 Troubleshooting

### If you get "fatal: not a git repository"

```bash
# Make sure you're in the right directory
cd ~/path/to/BACKTEST/hyperliquid-copytrade
pwd
ls -la .git
```

### If you have merge conflicts

```bash
# Abort any ongoing merge
git merge --abort

# Reset hard to remote (CAUTION: loses local changes)
git fetch origin claude/fix-copytrading-simulator-016Rwzzxe4AenGmWU5Qw3sqH
git reset --hard origin/claude/fix-copytrading-simulator-016Rwzzxe4AenGmWU5Qw3sqH
```

### If you want to keep local changes

```bash
# Create a backup branch first
git branch backup-$(date +%Y%m%d-%H%M%S)

# Then reset and pull
git fetch origin claude/fix-copytrading-simulator-016Rwzzxe4AenGmWU5Qw3sqH
git reset --hard origin/claude/fix-copytrading-simulator-016Rwzzxe4AenGmWU5Qw3sqH
git pull origin claude/fix-copytrading-simulator-016Rwzzxe4AenGmWU5Qw3sqH
```

---

## ✅ What You Should See

After successful pull:

```
Already up to date.
```

OR

```
Updating abc1234..def5678
Fast-forward
 hyperliquid-copytrade/backend/simulator_engine.py | 152 +++++++++++++++++----
 hyperliquid-copytrade/backend/api_simulator.py    |  35 +++--
 2 files changed, 152 insertions(+), 35 deletions(-)
```

Latest commits should include:
- `a2cbb9f Fix simulator: use same leverage as trader + detailed logging + debug endpoint`
- `414f4b4 Add startup scripts and documentation for simulator`
- `bf4f687 Add legacy endpoints for Simulator.jsx compatibility`

---

## 📋 After Pulling

Once your repo is clean and up to date:

1. **Stop any running services:**
   ```bash
   pkill -f "python3 api"
   pkill -f "vite"
   ```

2. **Start the fixed simulator:**
   ```bash
   cd hyperliquid-copytrade/backend
   python3 api_simulator.py
   ```

3. **Watch the detailed logs** - you'll see every trade with full details!

---

## 🆘 Need Help?

If you encounter any errors, share:
1. The exact error message
2. Output of `git status`
3. Output of `git log --oneline -3`
