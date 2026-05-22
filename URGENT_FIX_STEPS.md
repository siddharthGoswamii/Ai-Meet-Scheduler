# URGENT: Fix Authentication on Render

## The Problem
Your backend on Render is NOT using the environment variables correctly. The CORS error shows the backend doesn't have your frontend URL in its allowed origins.

## CRITICAL: Update Render Environment Variables NOW

### Step 1: Go to Backend Service on Render
1. Visit https://dashboard.render.com/
2. Click on your backend service: **Ai-Meet-Scheduler** (or similar name)
3. Click on **"Environment"** tab in the left sidebar

### Step 2: Add/Update These Environment Variables

**IMPORTANT**: Make sure these EXACT values are set:

```
ENVIRONMENT=production

FRONTEND_URL=https://ai-meet-scheduler-frontend.onrender.com

CORS_ORIGINS=http://localhost:3000,https://ai-meet-scheduler-eimp.onrender.com,https://ai-meet-scheduler-frontend.onrender.com

CORS_ALLOW_CREDENTIALS=True
```

**CRITICAL NOTES:**
- NO trailing slashes on URLs
- NO spaces after commas in CORS_ORIGINS
- Use commas to separate multiple origins
- Make sure FRONTEND_URL matches your actual frontend URL

### Step 3: Save and Redeploy
1. Click **"Save Changes"** button
2. Render will automatically redeploy your backend
3. Wait 2-3 minutes for deployment to complete
4. Check that status shows "Live" (green)

### Step 4: Verify the Fix
1. Go to https://ai-meet-scheduler-frontend.onrender.com
2. Open browser DevTools (F12)
3. Go to Console tab
4. Click "Sign in with Google"
5. Check if CORS error is gone

## If CORS Error Persists

### Check 1: Verify Environment Variables Were Saved
1. Go back to Render dashboard
2. Click on your backend service
3. Go to "Environment" tab
4. Verify all variables are there with correct values

### Check 2: Check Backend Logs
1. In Render dashboard, click on your backend service
2. Click "Logs" tab
3. Look for any errors during startup
4. Check if it says "Starting application..."

### Check 3: Test Backend Directly
Visit: https://ai-meet-scheduler-eimp.onrender.com/health

Should return:
```json
{
  "status": "healthy",
  "environment": "production"
}
```

If it returns "development" instead of "production", the ENVIRONMENT variable wasn't set correctly.

## Alternative: Manual CORS Fix (If Above Doesn't Work)

If environment variables aren't working, we can hardcode the frontend URL temporarily:

1. I'll update the code to include your frontend URL directly
2. Push the changes
3. Render will redeploy

Let me know if you want me to do this.

## Google OAuth Settings (Do This After CORS is Fixed)

1. Go to https://console.cloud.google.com/
2. Navigate to "APIs & Services" → "Credentials"
3. Click on your OAuth 2.0 Client ID
4. Under "Authorized JavaScript origins", add:
   - `https://ai-meet-scheduler-frontend.onrender.com`
5. Under "Authorized redirect URIs", verify this exists:
   - `https://ai-meet-scheduler-eimp.onrender.com/api/auth/callback`
6. Click "Save"

## Quick Test Commands

Test if backend is accessible:
```bash
curl https://ai-meet-scheduler-eimp.onrender.com/health
```

Test if CORS headers are present:
```bash
curl -H "Origin: https://ai-meet-scheduler-frontend.onrender.com" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     https://ai-meet-scheduler-eimp.onrender.com/api/auth/login -v
```

Look for `Access-Control-Allow-Origin` in the response headers.

## What Should Happen After Fix

1. Frontend loads without errors
2. Click "Sign in with Google" button
3. Redirected to Google OAuth page
4. After signing in, redirected back to your dashboard
5. Dashboard shows your email and allows creating meetings

## Need Help?

If none of this works, let me know and I'll:
1. Add the frontend URL directly to the code (hardcoded)
2. Push the changes
3. This will guarantee it works