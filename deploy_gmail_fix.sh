#!/bin/bash

# Deploy Gmail validation fix - removes strict existence check
# This fixes the issue where valid Gmail addresses were being rejected

echo "🚀 Deploying Gmail validation fix..."

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

echo "📝 Changes being deployed:"
echo "  - Removed strict Gmail account existence verification"
echo "  - Kept format validation (Gmail-only)"
echo "  - Valid Gmail addresses will now be accepted"
echo ""

# Commit changes
echo "📦 Committing changes..."
git add app/services/gmail_verifier.py app/api/meetings.py
git commit -m "fix: Remove strict Gmail verification that caused false negatives

- Gmail People API cannot verify arbitrary Gmail addresses
- Only validates format now (Gmail-only still enforced)
- Fixes issue where valid Gmail addresses were rejected
- Users can now add any valid Gmail address as attendee"

# Push to repository
echo "⬆️  Pushing to repository..."
git push origin main

echo ""
echo "✅ Changes pushed to repository!"
echo ""
echo "🔄 Render will automatically deploy the changes in a few minutes"
echo ""
echo "📋 What was fixed:"
echo "  ✓ Valid Gmail addresses are now accepted"
echo "  ✓ Format validation still enforced (must be @gmail.com)"
echo "  ✓ No more false 'account not found' errors"
echo ""
echo "⏳ Wait 2-3 minutes for Render to deploy, then test with:"
echo "   - aasthasaha7@gmail.com"
echo "   - Any other valid Gmail address"
echo ""
echo "🎉 Done! Your app will be updated shortly."

# Made with Bob
