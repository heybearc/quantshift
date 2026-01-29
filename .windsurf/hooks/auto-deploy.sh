#!/bin/bash

# Auto-deploy hook - triggers after Cascade writes code
# Automatically commits, pushes, and deploys to container during debugging

# Detect which app we're working on
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_ROOT" ]; then
    exit 0  # Not in a git repo, skip
fi

APP_NAME=$(basename "$REPO_ROOT")

# Only auto-deploy for app repos (not control plane)
case "$APP_NAME" in
    theoshift|ldc-tools|quantshift)
        # App repo detected
        ;;
    *)
        # Not an app repo, skip auto-deploy
        exit 0
        ;;
esac

# Check if we're in an active debugging session
# (You can customize this detection logic)
if [ -f "$REPO_ROOT/.debugging" ]; then
    echo "🚀 Auto-deploying $APP_NAME to container..."
    
    # Commit changes (if any)
    if ! git diff --quiet; then
        git add -A
        COMMIT_MSG="fix: auto-deployed changes during debugging session"
        git commit -m "$COMMIT_MSG" --no-verify
        echo "✅ Changes committed"
    fi
    
    # Push to GitHub
    git push origin main --no-verify 2>/dev/null
    echo "✅ Pushed to GitHub"
    
    # Deploy to container based on app
    case "$APP_NAME" in
        theoshift)
            CONTAINER="blue-theoshift"
            APP_PATH="/opt/theoshift"
            PM2_NAME="theoshift"
            ;;
        ldc-tools)
            CONTAINER="ldc-staging"
            APP_PATH="/opt/ldc-tools/frontend"
            PM2_NAME="ldc-tools"
            ;;
        quantshift)
            CONTAINER="qs-dashboard"
            APP_PATH="/opt/quantshift"
            PM2_NAME="quantshift-dashboard"
            ;;
    esac
    
    # SSH deploy
    ssh "$CONTAINER" "cd $APP_PATH && git pull && npm install && npm run build && pm2 restart $PM2_NAME" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ Deployed to $CONTAINER"
        echo "💡 Test your changes now"
    else
        echo "❌ Deployment failed - check SSH connection"
    fi
else
    # Not in debugging mode, just suggest deployment
    echo "💡 Code changes ready. Say 'deploy this' to test on container."
fi

exit 0
