#!/bin/bash
echo "🔒 Secure Team Repository Setup"
echo "=============================="

# Clean up existing git
cd /workspaces/codespaces-blank
rm -rf .git
git init
git config user.name "DevOpsKiruthi"
git config user.email "rkiruthi@gmail.com"

# Add all files
git add .

# Commit
git commit -m "Azure IoT AutoGen Evaluation System - Team Ready"

echo ""
echo "✅ Local repository ready"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Go to: https://github.com/new"
echo "2. Create: iot-autogen-team-workspace (PUBLIC)"
echo "3. DO NOT initialize with anything"
echo "4. After creation, COPY the HTTPS URL"
echo "5. Return here and press Enter"
read -p "Press Enter after creating repository..."

echo ""
read -p "Paste the repository URL: " REPO_URL

# Add remote
git remote add origin "$REPO_URL"

# Push
echo "📤 Pushing code..."
if git push -u origin main; then
    echo ""
    echo "🎉 SUCCESS!"
    echo "Repository: $REPO_URL"
    echo ""
    echo "👥 Share with team:"
    echo "• Clone: git clone $REPO_URL"
    echo "• Codespace: Open from GitHub UI"
else
    echo ""
    echo "⚠️  Push failed. Trying SSH method..."
    # Convert HTTPS to SSH URL
    SSH_URL=$(echo "$REPO_URL" | sed 's|https://github.com/|git@github.com:|')
    git remote set-url origin "$SSH_URL"
    git push -u origin main
fi
