# 🚀 Quick Start Guide

Get your B2B Chat API running in **5 minutes**!

---

## Option 1: Automated Setup (Recommended)

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run quick start
./scripts/quickstart.sh
```

This will:
1. Create virtual environment
2. Install dependencies
3. Start Postgres & Redis (via Docker)
4. Initialize database
5. Create test user

Then start the services:

```bash
# Start API
python app/main.py

# In another terminal, start console
streamlit run console/streamlit_app.py
```

---

## Option 2: Manual Setup

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start Postgres & Redis

**With Docker:**
```bash
docker-compose up -d postgres redis
```

**Or install locally:**
- PostgreSQL: https://www.postgresql.org/download/
- Redis: https://redis.io/download/

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 4. Initialize Database

```bash
python scripts/init_db.py
```

### 5. Create Test User

```bash
python scripts/create_test_user.py
```

This creates:
- **Email**: `test@example.com`
- **Password**: `testpassword123`
- **Balance**: $100.00

### 6. Start Services

**Terminal 1 - API:**
```bash
python app/main.py
```

**Terminal 2 - Console:**
```bash
streamlit run console/streamlit_app.py
```

---

## 🎯 Access Points

- **API Docs**: http://localhost:8000/docs
- **Admin Console**: http://localhost:8501
- **Health Check**: http://localhost:8000/health

---

## ✅ Test the API

### 1. Login via Console

1. Open http://localhost:8501
2. Login with `test@example.com` / `testpassword123`
3. Go to "API Keys" → Create new key
4. Copy the API key (shown once!)

### 2. Create a Bot

In the console:
1. Go to "Bots"
2. Click "Create New Bot"
3. Fill in:
   - **Name**: My Test Bot
   - **Model**: core-13b
   - **System Prompt**: You are a helpful AI assistant
4. Click "Create Bot"
5. Copy the Bot ID

### 3. Test Chat API

```bash
export BOT_ID="your_bot_id_here"
export API_KEY="your_api_key_here"

curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"bot_id\": \"$BOT_ID\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"Hello! Tell me a joke.\"}
    ],
    \"stream\": false
  }"
```

You should see a JSON response with the AI's reply!

---

## 🔧 Troubleshooting

### Database connection error

Check if Postgres is running:
```bash
docker-compose ps postgres
# Or if installed locally:
pg_isready
```

Update `DATABASE_URL` in `.env` if needed.

### Redis connection error

Check if Redis is running:
```bash
docker-compose ps redis
# Or if installed locally:
redis-cli ping
```

Update `REDIS_URL` in `.env` if needed.

### Port already in use

Change ports in `.env`:
```env
PORT=8001  # Instead of 8000
```

Or for Streamlit:
```bash
streamlit run console/streamlit_app.py --server.port 8502
```

### Module not found

Make sure you're in the virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📚 Next Steps

1. **Read the full [README.md](README.md)** for detailed documentation
2. **Configure NOWPayments** for crypto top-ups (optional)
3. **Set up OpenMeter** for usage analytics (optional)
4. **Deploy to production** (Railway, Fly.io, VPS)
5. **Set up channels** (Telegram, WhatsApp)

---

## 🆘 Need Help?

- Check the API docs: http://localhost:8000/docs
- Review logs: API prints to stdout
- Open an issue on GitHub

---

**Ready to build! 🎉**
