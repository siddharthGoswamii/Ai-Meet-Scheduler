#!/bin/bash

# Script to commit and push CORS fixes to trigger Render redeploy

echo "Adding all changes..."
git add .

echo "Committing changes..."
git commit -m "Fix: Use environment variables for CORS configuration

- Updated app/main.py to use settings.cors_origins_list
- This allows dynamic CORS configuration from Render environment variables
- Fixes authentication issues with deployed frontend"

echo "Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Changes pushed to GitHub!"
echo "🔄 Render will automatically redeploy your backend"
echo "⏱️  Wait 2-3 minutes for the deployment to complete"
echo ""
echo "After deployment completes:"
echo "1. Go to https://ai-meet-scheduler-frontend.onrender.com"
echo "2. Click 'Sign in with Google'"
echo "3. Authentication should now work!"

# Made with Bob
