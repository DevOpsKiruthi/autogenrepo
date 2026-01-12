#!/bin/bash
echo "🚀 Pushing Updates to GitHub"
echo "==========================="

# Get commit message or use default
if [ -z "$1" ]; then
    COMMIT_MSG="Update: $(date '+%Y-%m-%d %H:%M:%S')"
else
    COMMIT_MSG="$1"
fi

# Git operations
git add .
git commit -m "$COMMIT_MSG"
git push origin main

echo "✅ Pushed: $COMMIT_MSG"
echo "📁 Repository: https://github.com/DevOpsKiruthi/autogenrepo"
