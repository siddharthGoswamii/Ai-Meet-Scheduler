# Render Deployment Guide

## Backend Deployment (Already Done)

Your backend is deployed at: `https://ai-meet-scheduler-eimp.onrender.com`

### Required Environment Variables on Render

Make sure these environment variables are set in your Render dashboard for the backend service:

```
# Application Settings
APP_NAME=AI Meeting Scheduler
APP_VERSION=1.0.0
DEBUG=False
ENVIRONMENT=production

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Database Configuration
DATABASE_URL=postgresql+asyncpg://gmeet_scheduler_5y9m_user:U7qQ9aZtVn5bMEvx6cfys8pAGJBfXR1k@dpg-d87fmnjeo5us73e3998g-a.singapore-postgres.render.com/gmeet_scheduler_5y9m

# Google OAuth Configuration
GOOGLE_CLIENT_ID=718679746794-3vesthia66uee450osuvheg9lgdjvcu2.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=https://ai-meet-scheduler-eimp.onrender.com/api/auth/callback

# JWT Configuration
SECRET_KEY=30ba5c3f0adc4544673bc11922a7d9075ed5d9c371fa924fd12074b4511ad1d1
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Configuration (IMPORTANT: No trailing slash!)
CORS_ORIGINS=https://ai-meet-scheduler-eimp.onrender.com,https://your-frontend-url.onrender.com
CORS_ALLOW_CREDENTIALS=True

# Frontend URL (for OAuth callback redirects)
FRONTEND_URL=https://your-frontend-url.onrender.com

# Encryption Key
ENCRYPTION_KEY=w-WZ8iS8Fkv1CNolzgnPQ5L_ALunDUTXEWlejvVBAWg=

# Logging
LOG_LEVEL=INFO

# Timezone
DEFAULT_TIMEZONE=UTC
```

## Frontend Deployment

### Option 1: Deploy to Render (Recommended)

1. **Create a new Web Service on Render**
   - Connect your GitHub repository
   - Select the `frontend` directory as the root directory
   - Build Command: `npm install && npm run build`
   - Start Command: `npx serve -s build -l 3000`

2. **Set Environment Variable**
   - Add this environment variable in Render dashboard:
   ```
   REACT_APP_API_URL=https://ai-meet-scheduler-eimp.onrender.com
   ```

3. **Update Backend Environment Variables**
   - Once you get your frontend URL (e.g., `https://your-app.onrender.com`), update these in backend:
   ```
   FRONTEND_URL=https://your-app.onrender.com
   CORS_ORIGINS=https://ai-meet-scheduler-eimp.onrender.com,https://your-app.onrender.com
   ```

### Option 2: Deploy to Vercel

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Deploy from frontend directory**
   ```bash
   cd frontend
   vercel --prod
   ```

3. **Set Environment Variable in Vercel**
   - Go to your project settings on Vercel
   - Add environment variable:
   ```
   REACT_APP_API_URL=https://ai-meet-scheduler-eimp.onrender.com
   ```

4. **Update Backend Environment Variables**
   - Update `FRONTEND_URL` and `CORS_ORIGINS` with your Vercel URL

### Option 3: Deploy to Netlify

1. **Install Netlify CLI**
   ```bash
   npm install -g netlify-cli
   ```

2. **Deploy from frontend directory**
   ```bash
   cd frontend
   npm run build
   netlify deploy --prod --dir=build
   ```

3. **Set Environment Variable in Netlify**
   - Go to Site settings > Build & deploy > Environment
   - Add:
   ```
   REACT_APP_API_URL=https://ai-meet-scheduler-eimp.onrender.com
   ```

4. **Update Backend Environment Variables**
   - Update `FRONTEND_URL` and `CORS_ORIGINS` with your Netlify URL

## Google OAuth Configuration

**IMPORTANT**: After deploying your frontend, you need to update Google OAuth settings:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to "APIs & Services" > "Credentials"
4. Edit your OAuth 2.0 Client ID
5. Add your frontend URL to "Authorized JavaScript origins":
   - `https://your-frontend-url.onrender.com` (or Vercel/Netlify URL)
6. Add your backend callback URL to "Authorized redirect URIs":
   - `https://ai-meet-scheduler-eimp.onrender.com/api/auth/callback`

## Testing the Deployment

1. Visit your frontend URL
2. Click "Sign in with Google"
3. You should be redirected to Google OAuth
4. After authentication, you should be redirected back to your dashboard

## Troubleshooting

### Issue: CORS errors
- **Solution**: Make sure `CORS_ORIGINS` in backend has NO trailing slashes
- Verify the frontend URL is correctly added to `CORS_ORIGINS`

### Issue: Session/Cookie errors
- **Solution**: The backend now automatically uses `https_only=True` and `same_site="none"` in production
- Make sure `ENVIRONMENT=production` is set in Render

### Issue: OAuth callback fails
- **Solution**: Verify `GOOGLE_REDIRECT_URI` matches exactly what's in Google Cloud Console
- Check that `FRONTEND_URL` is set correctly in backend environment variables

### Issue: 500 Internal Server Error on login
- **Solution**: Check Render logs for the backend service
- Verify all environment variables are set correctly
- Make sure database connection is working

## Local Development

For local development, the app will automatically use:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

The `.env` files are already configured for this.