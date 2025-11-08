# B2B Chat API - CandyAI-Style Provider

A production-ready **B2B Chat API provider** built with FastAPI, PostgreSQL, Redis, and DeepInfra. Supports **streaming chat completions**, **prepaid wallets**, **multi-channel** (Web, Telegram, WhatsApp), **usage metering** with OpenMeter, and **crypto payments** via NOWPayments.

---

## 🚀 Features

- **OpenAI-Compatible API** - Drop-in replacement for OpenAI's chat completions
- **Streaming SSE** - Real-time token streaming for responsive UX
- **Multi-Model Support** - 13B, 34B, and 70B models via DeepInfra
- **Prepaid Wallet System** - Balance-based billing with auto-debit
- **Crypto Payments** - NOWPayments integration for top-ups
- **Usage Metering** - OpenMeter integration for granular analytics
- **Rate Limiting** - Redis-based sliding window rate limits
- **Multi-Channel** - Web widget, Telegram, and WhatsApp adapters
- **Bot Builder** - Custom system prompts, temperature, safety levels
- **Admin Console** - Beautiful Streamlit dashboard
- **Production-Grade** - Proper auth, audit logs, request tracking

---

## 📦 Tech Stack

- **Backend**: FastAPI + Uvicorn
- **Database**: PostgreSQL + SQLAlchemy
- **Cache/Rate Limit**: Redis
- **LLM Provider**: DeepInfra
- **Payments**: NOWPayments (crypto)
- **Metering**: OpenMeter (optional)
- **Console**: Streamlit

---

## 🏗️ Architecture

```
┌─────────────┐
│  Streamlit  │  Console (Dashboard, Bots, Keys, Wallet)
│   Console   │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────────────────────┐
│          FastAPI Backend                │
│  ┌────────┬─────────┬──────────────┐   │
│  │  Auth  │  Bots   │  Chat API    │   │
│  ├────────┼─────────┼──────────────┤   │
│  │ Wallet │ Webhooks│ Rate Limiter │   │
│  └────────┴─────────┴──────────────┘   │
└───┬────────────┬────────────┬──────────┘
    │            │            │
    ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌──────────┐
│ Postgres│ │ Redis  │  │ DeepInfra│
└────────┘  └────────┘  └──────────┘
```

---

## 🔧 Setup

### 1. Prerequisites

- **Python 3.10+**
- **PostgreSQL 14+**
- **Redis 7+**

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/b2b_chat
REDIS_URL=redis://localhost:6379/0
DEEPINFRA_API_KEY=your_deepinfra_key
JWT_SECRET=your_secure_random_secret
```

### 4. Initialize Database

```bash
python scripts/init_db.py
```

### 5. Create Test User (Optional)

```bash
python scripts/create_test_user.py
```

This creates:
- **Email**: `test@example.com`
- **Password**: `testpassword123`
- **Balance**: $100.00
- **API Key**: (printed to console)

---

## 🚀 Run

### Start API Server

```bash
python app/main.py
```

Or with Uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: `http://localhost:8000`

- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

### Start Admin Console

```bash
streamlit run console/streamlit_app.py
```

Console will be available at: `http://localhost:8501`

---

## 📖 API Usage

### 1. Register & Login

**Register:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "yourpassword"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "yourpassword"
  }'
```

Returns: `{"access_token": "...", "token_type": "bearer"}`

### 2. Create API Key

```bash
curl -X POST http://localhost:8000/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Production Key"}'
```

Returns your API key (save it!).

### 3. Create a Bot

```bash
curl -X POST http://localhost:8000/bots \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My NSFW Bot",
    "model_id": "core-13b",
    "system_prompt": "You are a flirty, creative AI assistant.",
    "temperature": 0.8,
    "max_tokens": 2048,
    "safety_level": "none"
  }'
```

Returns: `{"id": "bot_uuid", ...}`

### 4. Chat with Bot (Streaming)

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "your_bot_uuid",
    "messages": [
      {"role": "user", "content": "Hey! Tell me a story."}
    ],
    "stream": true
  }'
```

Returns SSE stream of tokens.

### 5. Check Wallet

```bash
curl http://localhost:8000/wallet \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Returns: `{"balance_cents": 3000, ...}`

### 6. Top-Up Wallet

```bash
curl -X POST http://localhost:8000/wallet/topup \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount_usd": 50.0,
    "currency": "usd"
  }'
```

Returns NOWPayments payment URL.

---

## 🤖 Models & Pricing

| Model Tier    | Model ID                       | Price (per 1M tokens) |
|---------------|--------------------------------|-----------------------|
| **Core 13B**  | `core-13b`                     | **$1.60**             |
| **Core 34B**  | `core-34b`                     | **$3.20**             |
| **Flagship 70B** | `flagship-70b`              | **$6.00**             |

Your cost (DeepInfra): **$0.08 / 1M tokens** → **20x markup** = great margins!

---

## 🔐 Security Checklist

- ✅ API keys hashed with SHA-256
- ✅ Passwords hashed with Bcrypt
- ✅ JWT tokens for console auth
- ✅ Rate limiting (120 req/min default)
- ✅ CORS protection
- ✅ NOWPayments signature verification
- ✅ Audit logs for sensitive actions
- ✅ Wallet balance checks before chat

**Production TODOs:**
- [ ] Use Argon2id for API key hashing
- [ ] Rotate JWT secret regularly
- [ ] Set up HTTPS (Caddy/Nginx)
- [ ] Enable Redis AUTH
- [ ] Use environment secrets (not .env in prod)
- [ ] Set up monitoring (Sentry, Prometheus)

---

## 📊 OpenMeter Integration

If you configure `OPENMETER_TOKEN`, all usage events are automatically sent to OpenMeter:

```json
{
  "type": "ai.usage",
  "subject": "api_key_id",
  "data": {
    "tenant_id": "user_id",
    "model_id": "core-13b",
    "tokens_in": 150,
    "tokens_out": 300,
    "cost_cents": 72
  }
}
```

Use OpenMeter dashboards for:
- Per-user usage analytics
- Cost tracking
- Rate limit alerts
- Billing reconciliation

---

## 📱 Channels

### Web Widget (SSE)

1. Create a bot
2. Generate a public web token (TODO: implement in console)
3. Embed widget:

```html
<script>
  window.CandyB2B = {
    apiKey: "sk_web_...",
    botId: "your_bot_uuid"
  };
</script>
<script src="https://cdn.yourcdn.com/widget.min.js"></script>
```

### Telegram

1. Create Telegram bot via @BotFather
2. Get bot token
3. Create channel in console:

```bash
curl -X POST http://localhost:8000/channels \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "bot_id": "your_bot_uuid",
    "kind": "telegram",
    "config": {"bot_token": "1234567890:ABCdef..."}
  }'
```

4. Set webhook:

```bash
curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook \
  -d "url=https://yourdomain.com/webhooks/telegram/<channel_id>"
```

### WhatsApp

1. Set up WhatsApp Cloud API (Meta Business)
2. Get access token & phone number ID
3. Create channel with config:

```json
{
  "access_token": "...",
  "phone_number_id": "...",
  "verify_token": "your_random_token"
}
```

4. Set webhook in Meta dashboard

---

## 🛠️ Development

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
black .
ruff check .
```

### Database Migrations (Alembic)

```bash
alembic revision --autogenerate -m "Add new table"
alembic upgrade head
```

---

## 📈 Roadmap

- [ ] **Channels**: Web widget (JS/React)
- [ ] **Billing**: Stripe support (credit cards)
- [ ] **Analytics**: Built-in usage dashboard
- [ ] **Models**: Add image generation endpoints
- [ ] **Limits**: Per-bot rate limits
- [ ] **Teams**: Multi-user organizations
- [ ] **Logs**: Chat history export
- [ ] **Webhook**: Outbound webhooks for events
- [ ] **Docker**: Docker Compose setup
- [ ] **Deploy**: One-click Railway/Fly.io deploy

---

## 📄 License

MIT License - See LICENSE file

---

## 🤝 Support

- **Docs**: See `/docs` endpoint
- **Issues**: GitHub Issues
- **Email**: support@yourdomain.com

---

## 🎉 Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [DeepInfra](https://deepinfra.com/)
- [OpenMeter](https://openmeter.io/)
- [NOWPayments](https://nowpayments.io/)
- [Streamlit](https://streamlit.io/)

---

**Ready to ship! 🚀**

Test the full flow:
1. Start API: `python app/main.py`
2. Start Console: `streamlit run console/streamlit_app.py`
3. Register → Create Bot → Generate API Key → Chat!
