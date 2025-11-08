# 🚀 Deploy to Streamlit Cloud

This guide will help you deploy the B2B Chat API admin console to Streamlit Cloud.

---

## Prerequisites

1. ✅ **GitHub Account** - Your code must be in a GitHub repository
2. ✅ **Streamlit Cloud Account** - Sign up at https://share.streamlit.io (free)
3. ✅ **Deployed API** - Your FastAPI backend must be deployed and accessible

---

## Step 1: Push Code to GitHub

Your code is already committed. Push to GitHub:

```bash
# If you haven't already
git push -u origin claude/b2b-chat-api-provider-011CUwFQwGECXxKnH67e57Pr

# Or create a new repo
# 1. Go to github.com and create a new repository
# 2. Follow GitHub's instructions to push your code
```

---

## Step 2: Deploy Your API Backend First

Before deploying the console, you need your API running somewhere. Options:

### Option A: Railway (Recommended - Easy)

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your `Horny-AI` repository
5. Railway will auto-detect the Python app
6. Add environment variables:
   ```
   DATABASE_URL=postgresql://...  (Railway provides this)
   REDIS_URL=redis://...          (Railway provides this)
   DEEPINFRA_API_KEY=NDnRfiSssrzknoL9X7Y5tOCzBCZ0bel2
   JWT_SECRET=your-random-secret-here
   PORT=8000
   ```
7. Railway will give you a URL like: `https://horny-ai-production.up.railway.app`
8. **Save this URL** - you'll need it for Streamlit

### Option B: Fly.io

1. Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
2. Login: `flyctl auth login`
3. In your project directory:
   ```bash
   flyctl launch
   flyctl secrets set DEEPINFRA_API_KEY=NDnRfiSssrzknoL9X7Y5tOCzBCZ0bel2
   flyctl secrets set JWT_SECRET=your-random-secret
   flyctl deploy
   ```
4. Your API will be at: `https://your-app.fly.dev`

### Option C: Render

1. Go to https://render.com
2. New → Web Service → Connect your GitHub repo
3. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app/main.py`
4. Add environment variables
5. You'll get: `https://your-app.onrender.com`

---

## Step 3: Deploy Console to Streamlit Cloud

### A. Sign Up for Streamlit Cloud

1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Authorize Streamlit to access your repos

### B. Create New App

1. Click **"New app"**
2. Select your repository: `your-username/Horny-AI`
3. Select branch: `claude/b2b-chat-api-provider-011CUwFQwGECXxKnH67e57Pr` (or `main`)
4. **Main file path**: `console/streamlit_app.py` ⚠️ Important!
5. **App URL**: Choose your subdomain (e.g., `b2b-chat-console`)

### C. Configure Secrets

Before deploying, click **"Advanced settings"** → **"Secrets"**

Add this (replace with your API URL):

```toml
API_BASE_URL = "https://your-api-domain.com"
```

For example:
```toml
API_BASE_URL = "https://horny-ai-production.up.railway.app"
```

### D. Deploy

1. Click **"Deploy!"**
2. Wait 2-3 minutes for deployment
3. Your console will be live at: `https://b2b-chat-console.streamlit.app`

---

## Step 4: Test Your Deployment

1. Open your Streamlit app URL
2. Register a new account (or use test credentials if you imported your database)
3. Create a bot
4. Generate an API key
5. Test the chat API!

---

## Configuration Details

### What Streamlit Cloud Needs

Streamlit Cloud automatically installs dependencies from:
- `console/requirements.txt` (if present in same directory as app)
- OR `requirements.txt` (root level)

We created `console/requirements.txt` with minimal dependencies:
```
streamlit==1.30.0
httpx==0.26.0
python-dotenv==1.0.0
```

### How Secrets Work

The console code checks for API URL in this order:
1. **Streamlit secrets** (`st.secrets['API_BASE_URL']`)
2. **Environment variable** (`os.getenv('API_BASE_URL')`)
3. **Default** (`http://localhost:8000`)

In production, use Streamlit secrets (most secure).

---

## Troubleshooting

### Error: "Module not found"

**Solution:** Make sure `console/requirements.txt` exists with necessary packages.

### Error: "Connection refused" or API errors

**Solution:** Check that:
1. Your API is actually deployed and running
2. The API URL in Streamlit secrets is correct
3. The API URL includes `https://` (not `http://`)
4. CORS is configured to allow your Streamlit domain

Update API CORS in `app/config.py`:
```python
CORS_ORIGINS = [
    "http://localhost:8501",
    "https://your-streamlit-app.streamlit.app"
]
```

### Error: "File not found: console/streamlit_app.py"

**Solution:** Make sure you specified the correct path when creating the app.
- Path should be: `console/streamlit_app.py`
- NOT: `streamlit_app.py`

### Console loads but login fails

**Solution:**
1. Check API is deployed correctly
2. Test API health: `https://your-api.com/health`
3. Check Streamlit logs for error details

---

## Update Your Deployed App

### Update Console Code

1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add console/streamlit_app.py
   git commit -m "Update console"
   git push
   ```
3. Streamlit Cloud auto-redeploys! (30 seconds)

### Update Secrets

1. Go to Streamlit Cloud dashboard
2. Click on your app
3. Settings → Secrets
4. Edit and save
5. App will automatically restart

---

## Pro Tips

### Custom Domain

Streamlit Cloud allows custom domains on paid plans:
1. Upgrade to Streamlit for Teams
2. Settings → Custom domain
3. Add CNAME record: `console.yourdomain.com` → `your-app.streamlit.app`

### Password Protection

Streamlit Cloud apps are public by default. To restrict access:

**Option 1: Add password to console** (Simple)

Edit `console/streamlit_app.py` to add a password check before login page.

**Option 2: Use Streamlit Teams** (Recommended)

Upgrade to Streamlit Teams for:
- User authentication
- Private apps
- More resources
- Custom domains

### Monitor Usage

Streamlit Cloud dashboard shows:
- Number of visitors
- Resource usage
- Logs

---

## Architecture Diagram

```
┌─────────────────────┐
│   User's Browser    │
└──────────┬──────────┘
           │ HTTPS
           ▼
┌─────────────────────┐
│  Streamlit Cloud    │  (Console)
│  *.streamlit.app    │
└──────────┬──────────┘
           │ API calls (HTTPS)
           ▼
┌─────────────────────┐
│  Railway/Fly.io     │  (Your API)
│  FastAPI Backend    │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌────────┐   ┌────────┐
│Postgres│   │ Redis  │
└────────┘   └────────┘
```

---

## Cost Breakdown

### Streamlit Cloud
- **Free tier**: 1 private app + unlimited public apps
- **Teams**: $20/month (private apps, auth, custom domains)

### API Hosting (Railway example)
- **Free tier**: $5 credit/month (limited resources)
- **Pro**: ~$20-50/month (depends on usage)
- **Postgres**: Included with Railway
- **Redis**: Included with Railway

### Total to start: **$0-$20/month**

---

## Example Deployed URLs

After deployment, you'll have:

```
API:      https://b2b-chat-api.up.railway.app
Console:  https://b2b-chat-console.streamlit.app
Docs:     https://b2b-chat-api.up.railway.app/docs
```

---

## Next Steps After Deployment

1. ✅ Share console URL with your team
2. ✅ Set up monitoring (Sentry, LogRocket)
3. ✅ Configure custom domain
4. ✅ Set up NOWPayments for real crypto payments
5. ✅ Add analytics (Google Analytics, Posthog)
6. ✅ Create marketing landing page
7. ✅ Launch! 🚀

---

## Need Help?

- **Streamlit Docs**: https://docs.streamlit.io/streamlit-community-cloud
- **Railway Docs**: https://docs.railway.app
- **Our README**: Check the main README.md for API setup
- **Issues**: Open a GitHub issue

---

**You're ready to deploy! 🎉**

Time to deployment: **~10 minutes** (after API is deployed)

Start here: https://share.streamlit.io
