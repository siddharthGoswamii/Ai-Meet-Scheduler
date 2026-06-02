#!/bin/bash

echo "=========================================="
echo "Deploying Gmail-Only Validation Fix"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

echo "Step 1: Backend is already updated (no restart needed for Python changes)"
echo "  - app/utils/email_validator.py has been updated"
echo "  - Changes will take effect on next API call"
echo ""

echo "Step 2: Rebuilding Frontend..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "  Installing dependencies..."
    npm install
fi

echo "  Building React app..."
npm run build

if [ $? -eq 0 ]; then
    echo "  ✓ Frontend build successful!"
else
    echo "  ✗ Frontend build failed!"
    exit 1
fi

cd ..

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. If running locally: Restart your React dev server (npm start)"
echo "2. If deployed: Deploy the 'frontend/build' folder to your hosting"
echo "3. Clear browser cache or do a hard refresh (Ctrl+Shift+R)"
echo ""
echo "Testing:"
echo "1. Try adding 'abcdef' - should be rejected"
echo "2. Try adding 'test@yahoo.com' - should be rejected"
echo "3. Try adding 'user@gmail.com' - should be accepted"
echo ""

# Made with Bob
