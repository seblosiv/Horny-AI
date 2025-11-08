# 🚀 DEPLOY TO RAILWAY - COMPLETE GUIDE

Follow these steps to deploy your entire B2B Chat API to production in **10 minutes**!

---

## 📋 What You'll Get

After deployment:
- ✅ **API Backend** running on Railway
- ✅ **PostgreSQL Database** (managed by Railway)
- ✅ **Redis** (managed by Railway)
- ✅ **Streamlit Console** (already deployed)
- ✅ **Public HTTPS URLs** for everything
- ✅ **Auto-scaling** and monitoring

---

## 🎯 Step-by-Step Deployment

### **Step 1: Sign Up for Railway**

1. Go to: **https://railway.app**
2. Click **"Start a New Project"**
3. Sign in with GitHub
4. Authorize Railway to access your repos

---

### **Step 2: Create New Project**

1. Click **"New Project"** button
2. Select **"Deploy from GitHub repo"**
3. Find and select: `seblosiv/Horny-AI`
4. Select branch: `claude/b2b-chat-api-provider-011CUwFQwGECXxKnH67e57Pr`

Railway will start deploying your app!

---

### **Step 3: Add Database Services**

Your app needs PostgreSQL and Redis. Add them:

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Click **"+ New"** again
4. Select **"Database"** → **"Add Redis"**

Railway will automatically:
- Create the databases
- Set `DATABASE_URL` environment variable
- Set `REDIS_URL` environment variable

---

### **Step 4: Configure Environment Variables**

Click on your **API service** (should be named `horny-ai` or similar) → **"Variables"** tab

Add these variables:

```bash
DEEPINFRA_API_KEY=NDnRfiSssrzknoL9X7Y5tOCzBCZ0bel2
JWT_SECRET=please-change-this-to-a-random-32-character-secret
PORT=8000
HOST=0.0.0.0
```

**IMPORTANT:** Generate a secure JWT secret:
```bash
# On your computer, run:
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Use the output as your JWT_SECRET
```

Optional (but recommended):
```bash
DEBUG=false
INITIAL_TRIAL_CREDITS_CENTS=30
RATE_LIMIT_PER_MIN=120
```

**CORS Configuration:**
Add your Streamlit domain to CORS:
```bash
CORS_ORIGINS=["http://localhost:8501","https://rwxajxvqevkdwvxrsxg3yx.streamlit.app"]
```

---

### **Step 5: Generate Public Domain**

1. Click on your API service
2. Go to **"Settings"** tab
3. Scroll to **"Networking"**
4. Click **"Generate Domain"**

You'll get a URL like:
```
https://horny-ai-production.up.railway.app
```

**🎯 COPY THIS URL - You'll need it for Streamlit!**

---

### **Step 6: Initialize Database**

After the first deployment succeeds, you need to initialize the database.

**Option A: Via Railway CLI (Recommended)**

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run database initialization
railway run python scripts/init_db.py
railway run python scripts/create_test_user.py
```

**Option B: Via Railway Dashboard**

1. Go to your project → API service
2. Click **"Deployments"** tab
3. Click on the latest deployment
4. Click **"View Logs"**
5. In the top right, click **"..."** → **"Run Command"**
6. Run: `python scripts/init_db.py`
7. Then run: `python scripts/create_test_user.py`

---

### **Step 7: Update Streamlit Console**

Now connect your Streamlit console to the deployed API:

1. Go to: **https://share.streamlit.io**
2. Click on your app: `rwxajxvqevkdwvxrsxg3yx`
3. Click **"Settings"** (⚙️) → **"Secrets"**
4. Replace with your Railway URL:

```toml
API_BASE_URL = "https://horny-ai-production.up.railway.app"
```

5. Click **"Save"**
6. App will restart automatically (30 seconds)

---

### **Step 8: Test Everything!**

1. Open your Streamlit console: `https://rwxajxvqevkdwvxrsxg3yx.streamlit.app`
2. Try logging in with test account:
   - **Email:** `test@example.com`
   - **Password:** `testpassword123`

   OR register a new account!

3. Create your first bot:
   - Name: "My First Bot"
   - Model: "core-13b"
   - System Prompt: "You are a helpful AI assistant"

4. Generate an API key

5. Test the API:

```bash
export API_KEY="your-api-key-here"
export BOT_ID="your-bot-id-here"
export API_URL="https://horny-ai-production.up.railway.app"

curl -X POST $API_URL/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "'$BOT_ID'",
    "messages": [{"role": "user", "content": "Hello! Tell me a joke."}],
    "stream": false
  }'
```

---

## ✅ Deployment Checklist

- [ ] Sign up for Railway
- [ ] Deploy from GitHub repo
- [ ] Add PostgreSQL database
- [ ] Add Redis database
- [ ] Set environment variables (DEEPINFRA_API_KEY, JWT_SECRET, etc.)
- [ ] Generate public domain
- [ ] Initialize database (run scripts)
- [ ] Update Streamlit secrets with Railway URL
- [ ] Test login in console
- [ ] Create a bot
- [ ] Generate API key
- [ ] Test API endpoint
- [ ] 🎉 YOU'RE LIVE!

---

## 📊 Your Architecture (After Deployment)

```
┌─────────────────────┐
│   Users/Customers   │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐  ┌──────────────┐
│Streamlit│  │   API Calls  │
│ Console │  │ (from apps)  │
└────┬────┘  └──────┬───────┘
     │              │
     │ HTTPS        │ HTTPS
     │              │
     └──────┬───────┘
            ▼
    ┌──────────────────┐
    │  Railway API     │  https://your-app.up.railway.app
    │  FastAPI Backend │
    └────────┬─────────┘
             │
      ┌──────┴──────┐
      ▼             ▼
┌──────────┐  ┌─────────┐
│PostgreSQL│  │  Redis  │
│(Railway) │  │(Railway)│
└──────────┘  └─────────┘
```

---

## 💰 Cost Estimate

### Railway Pricing
- **Hobby Plan:** $5/month (includes $5 credit)
  - Good for: Development & testing
  - Limits: 500 hours/month, sleeps after inactivity

- **Pro Plan:** $20/month + usage
  - Good for: Production
  - No sleep, better performance
  - PostgreSQL & Redis included

**Estimated Monthly Cost for Production:**
- Railway Pro: ~$20-40/month (depends on usage)
- Streamlit Cloud: Free (public apps)
- **Total: $20-40/month**

---

## 🔧 Troubleshooting

### Error: "Application failed to start"

**Check logs:**
1. Railway dashboard → Your service → "Deployments"
2. Click latest deployment → "View Logs"

**Common issues:**
- Missing environment variables
- Database not connected
- Port configuration (should be PORT=8000, HOST=0.0.0.0)

### Error: Database connection failed

**Solution:**
- Make sure PostgreSQL is added to project
- Check `DATABASE_URL` is automatically set
- Wait 1-2 minutes for database to be ready

### Error: Redis connection failed

**Solution:**
- Make sure Redis is added to project
- Check `REDIS_URL` is automatically set

### Streamlit can't connect to API

**Solution:**
- Make sure you generated a public domain for API
- Update Streamlit secrets with correct URL (must include `https://`)
- Check API health: `https://your-api.up.railway.app/health`

---

## 🎯 What's Next?

After successful deployment:

1. **Set up monitoring:**
   - Railway provides basic metrics
   - Add Sentry for error tracking: https://sentry.io

2. **Configure NOWPayments:**
   - Sign up: https://nowpayments.io
   - Get API key
   - Add to Railway variables:
     ```
     NOWPAYMENTS_API_KEY=your_key
     NOWPAYMENTS_IPN_SECRET=your_secret
     NOWPAYMENTS_SANDBOX=false
     ```

3. **Set up OpenMeter** (optional):
   - Sign up: https://openmeter.io
   - Get token
   - Add to Railway:
     ```
     OPENMETER_TOKEN=your_token
     ```

4. **Custom domain:**
   - Railway Pro allows custom domains
   - Settings → Domains → Add custom domain
   - Point your DNS to Railway

5. **Launch!** 🚀
   - Share API docs: `https://your-api.up.railway.app/docs`
   - Share console: `https://rwxajxvqevkdwvxrsxg3yx.streamlit.app`
   - Start onboarding customers!

---

## 📞 Support

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **API Docs:** https://your-api.up.railway.app/docs
- **GitHub Issues:** Create issue in your repo

---

## 🎊 YOU'RE READY TO LAUNCH!

Total deployment time: **~10 minutes**
Total cost: **$20-40/month**

**Start deploying:** https://railway.app

🚀🚀🚀
