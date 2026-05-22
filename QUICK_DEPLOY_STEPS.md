# Quick Deployment Steps for Render

## ✅ What's Already Fixed
- Backend CORS configuration
- OAuth callback URLs (now dynamic)
- Session middleware (production-ready)
- Frontend API URLs (environment-based)
- React hooks dependencies

## 🚀 Deploy Frontend to Render

### Step 1: Create Web Service on Render
1. Go to https://dashboard.render.com/
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `ai-meet-scheduler-frontend` (or your choice)
   - **Root Directory**: `frontend`
   - **Environment**: `Node`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npx serve -s build -p $PORT`

### Step 2: Add Environment Variable
In the Render dashboard for your frontend service:
- **Key**: `REACT_APP_API_URL`
- **Value**: `https://ai-meet-scheduler-eimp.onrender.com`

### Step 3: Deploy
Click "Create Web Service" and wait for deployment to complete.

## 🔧 Update Backend Environment Variables

Once your frontend is deployed (e.g., `https://your-app.onrender.com`):

1. Go to your backend service on Render
2. Go to "Environment" tab
3. Update/Add these variables:
   - `ENVIRONMENT` = `production`
   - `FRONTEND_URL` = `https://your-frontend-app.onrender.com`
   - `CORS_ORIGINS` = `https://ai-meet-scheduler-eimp.onrender.com,https://your-frontend-app.onrender.com`

4. Click "Save Changes" (this will trigger a redeploy)

## 🔐 Update Google OAuth Settings

1. Go to https://console.cloud.google.com/
2. Navigate to "APIs & Services" → "Credentials"
3. Click on your OAuth 2.0 Client ID
4. Under "Authorized JavaScript origins", add:
   - `https://your-frontend-app.onrender.com`
5. Under "Authorized redirect URIs", verify:
   - `https://ai-meet-scheduler-eimp.onrender.com/api/auth/callback`
6. Click "Save"

## ✅ Test Your Deployment

1. Visit your frontend URL: `https://your-frontend-app.onrender.com`
2. Click "Sign in with Google"
3. Complete OAuth flow
4. You should be redirected to the dashboard
5. Test creating a meeting

## 🐛 Troubleshooting

### Build Fails on Render
- Check that `REACT_APP_API_URL` is set correctly
- Verify `package.json` has all dependencies
- Check Render build logs for specific errors

### CORS Errors
- Verify `CORS_ORIGINS` has NO trailing slashes
- Make sure frontend URL is included in `CORS_ORIGINS`
- Check that both URLs use `https://`

### OAuth Fails
- Verify Google OAuth settings include your frontend URL
- Check that `FRONTEND_URL` is set correctly in backend
- Ensure `GOOGLE_REDIRECT_URI` matches Google Console settings

### Session/Cookie Issues
- Verify `ENVIRONMENT=production` is set in backend
- Check browser console for cookie errors
- Ensure both frontend and backend use HTTPS

## 📝 Local Development

To run locally after these changes:

```bash
# Backend
cd c:/Users/AasthaSaha/Ai-Meet-Scheduler
python -m uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm start
```

The app will use:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

Environment variables are automatically configured for local development.