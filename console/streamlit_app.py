"""
Streamlit Admin Console for B2B Chat API
"""
import streamlit as st
import httpx
import json
from datetime import datetime
import time
import os

# Configuration - supports local dev and Streamlit Cloud
# Priority: Streamlit secrets > Environment variables > Default
if hasattr(st, 'secrets') and 'API_BASE_URL' in st.secrets:
    API_BASE_URL = st.secrets['API_BASE_URL']
else:
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

# Page config
st.set_page_config(
    page_title="B2B Chat API Console",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
    }
    .bot-card {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# Session state initialization
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None


def api_request(method: str, endpoint: str, data=None, auth=True):
    """Make API request"""
    headers = {"Content-Type": "application/json"}
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"

    url = f"{API_BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = httpx.get(url, headers=headers, timeout=30.0)
        elif method == "POST":
            response = httpx.post(url, headers=headers, json=data, timeout=30.0)
        elif method == "PATCH":
            response = httpx.patch(url, headers=headers, json=data, timeout=30.0)
        elif method == "DELETE":
            response = httpx.delete(url, headers=headers, timeout=30.0)

        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        st.error(f"API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                st.error(f"Details: {error_detail}")
            except:
                st.error(f"Status: {e.response.status_code}")
        return None


def login_page():
    """Login/Register page"""
    st.markdown("<div class='main-header'>🤖 B2B Chat API Console</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login to your account")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                result = api_request("POST", "/auth/login", {
                    "email": email,
                    "password": password
                }, auth=False)

                if result:
                    st.session_state.token = result["access_token"]
                    # Get user info
                    user = api_request("GET", "/auth/me")
                    if user:
                        st.session_state.user = user
                        st.success("Logged in successfully!")
                        st.rerun()

    with tab2:
        st.subheader("Create a new account")
        with st.form("register_form"):
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password (min 8 characters)", type="password", key="reg_pass")
            submit = st.form_submit_button("Register")

            if submit:
                if len(password) < 8:
                    st.error("Password must be at least 8 characters")
                else:
                    result = api_request("POST", "/auth/register", {
                        "email": email,
                        "password": password
                    }, auth=False)

                    if result:
                        st.session_state.token = result["access_token"]
                        user = api_request("GET", "/auth/me")
                        if user:
                            st.session_state.user = user
                            st.success("Account created! You received $0.30 trial credits.")
                            st.rerun()


def dashboard_page():
    """Main dashboard"""
    st.markdown("<div class='main-header'>Dashboard</div>", unsafe_allow_html=True)

    # Get wallet
    wallet = api_request("GET", "/wallet")

    if wallet:
        col1, col2, col3 = st.columns(3)

        with col1:
            balance_usd = wallet["balance_cents"] / 100
            st.metric("💰 Wallet Balance", f"${balance_usd:.2f}")

        with col2:
            spent_usd = wallet["total_spent_cents"] / 100
            st.metric("📊 Total Spent", f"${spent_usd:.2f}")

        with col3:
            deposited_usd = wallet["total_deposited_cents"] / 100
            st.metric("💳 Total Deposited", f"${deposited_usd:.2f}")

        # Low balance warning
        if wallet["balance_cents"] < 100:
            st.warning("⚠️ Low balance! Please top up your wallet to continue using the API.")

    # Recent activity
    st.subheader("📈 Recent Activity")

    payments = api_request("GET", "/wallet/payments")
    if payments:
        for payment in payments[:5]:
            amount_usd = payment["amount_cents"] / 100
            status_emoji = {"confirmed": "✅", "pending": "⏳", "failed": "❌"}.get(payment["status"], "❓")
            created = datetime.fromisoformat(payment["created_at"].replace("Z", "+00:00"))

            st.text(f"{status_emoji} ${amount_usd:.2f} - {payment['status']} - {created.strftime('%Y-%m-%d %H:%M')}")
    else:
        st.info("No payment history yet")


def bots_page():
    """Bots management"""
    st.markdown("<div class='main-header'>🤖 Bots</div>", unsafe_allow_html=True)

    # Create new bot
    with st.expander("➕ Create New Bot", expanded=False):
        with st.form("create_bot"):
            name = st.text_input("Bot Name")
            model = st.selectbox("Model", ["core-13b", "core-34b", "flagship-70b"])
            system_prompt = st.text_area(
                "System Prompt",
                value="You are a helpful, creative AI assistant. You're friendly, engaging, and adapt to the user's style.",
                height=150
            )
            temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
            max_tokens = st.slider("Max Tokens", 128, 8192, 2048, 128)
            safety_level = st.selectbox("Safety Level", ["none", "loose", "medium"])

            if st.form_submit_button("Create Bot"):
                result = api_request("POST", "/bots", {
                    "name": name,
                    "model_id": model,
                    "system_prompt": system_prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "safety_level": safety_level
                })

                if result:
                    st.success(f"✅ Bot '{name}' created!")
                    st.rerun()

    # List existing bots
    st.subheader("Your Bots")
    bots = api_request("GET", "/bots")

    if bots:
        for bot in bots:
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    status = "🟢" if bot["is_active"] else "🔴"
                    st.markdown(f"### {status} {bot['name']}")
                    st.text(f"Model: {bot['model_id']} | Temp: {bot['temperature']} | Safety: {bot['safety_level']}")
                    with st.expander("System Prompt"):
                        st.text(bot['system_prompt'])

                with col2:
                    st.text(f"ID: {bot['id'][:8]}...")
                    if st.button("Test", key=f"test_{bot['id']}"):
                        st.session_state.test_bot_id = bot['id']

                st.divider()
    else:
        st.info("No bots yet. Create your first bot above!")


def api_keys_page():
    """API Keys management"""
    st.markdown("<div class='main-header'>🔑 API Keys</div>", unsafe_allow_html=True)

    # Create new API key
    with st.expander("➕ Create New API Key", expanded=False):
        with st.form("create_key"):
            key_name = st.text_input("Key Name (e.g., 'Production', 'Development')")

            if st.form_submit_button("Generate API Key"):
                result = api_request("POST", "/api-keys", {"name": key_name})

                if result:
                    st.success("✅ API Key Created!")
                    st.code(result["secret_key"], language=None)
                    st.warning("⚠️ Save this key now! It won't be shown again.")
                    st.rerun()

    # List existing keys
    st.subheader("Your API Keys")
    api_keys = api_request("GET", "/api-keys")

    if api_keys:
        for key in api_keys:
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.text(f"🔑 {key['name']}")

            with col2:
                st.code(key['key_prefix'], language=None)

            with col3:
                if key['revoked']:
                    st.text("❌ Revoked")
                elif st.button("Revoke", key=f"revoke_{key['id']}"):
                    api_request("DELETE", f"/api-keys/{key['id']}")
                    st.rerun()

            st.text(f"Created: {datetime.fromisoformat(key['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d')}")
            if key['last_used_at']:
                st.text(f"Last used: {datetime.fromisoformat(key['last_used_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')}")

            st.divider()
    else:
        st.info("No API keys yet. Create your first key above!")


def wallet_page():
    """Wallet and top-up"""
    st.markdown("<div class='main-header'>💰 Wallet</div>", unsafe_allow_html=True)

    wallet = api_request("GET", "/wallet")

    if wallet:
        balance_usd = wallet["balance_cents"] / 100
        st.metric("Current Balance", f"${balance_usd:.2f}", delta=None)

        # Top-up form
        st.subheader("💳 Top Up")
        with st.form("topup_form"):
            amount = st.number_input("Amount (USD)", min_value=1.0, max_value=10000.0, value=10.0, step=1.0)

            if st.form_submit_button("Create Payment"):
                result = api_request("POST", "/wallet/topup", {
                    "amount_usd": amount,
                    "currency": "usd"
                })

                if result and result.get("payment_url"):
                    st.success("Payment created!")
                    st.markdown(f"[Click here to pay]({result['payment_url']})")
                elif result:
                    st.info("Payment created. Payment URL will be available once processed.")

        # Payment history
        st.subheader("📜 Payment History")
        payments = api_request("GET", "/wallet/payments")

        if payments:
            for payment in payments:
                amount_usd = payment["amount_cents"] / 100
                status_color = {"confirmed": "🟢", "pending": "🟡", "failed": "🔴"}.get(payment["status"], "⚪")

                st.text(f"{status_color} ${amount_usd:.2f} - {payment['status'].upper()} - {datetime.fromisoformat(payment['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')}")


def playground_page():
    """Chat playground"""
    st.markdown("<div class='main-header'>🎮 Playground</div>", unsafe_allow_html=True)

    # Select bot
    bots = api_request("GET", "/bots")

    if not bots:
        st.warning("Create a bot first to use the playground!")
        return

    selected_bot = st.selectbox(
        "Select Bot",
        options=bots,
        format_func=lambda x: f"{x['name']} ({x['model_id']})"
    )

    if not selected_bot:
        return

    # Get API key
    api_keys = api_request("GET", "/api-keys")
    active_keys = [k for k in api_keys if not k['revoked']]

    if not active_keys:
        st.warning("Create an API key first!")
        return

    # Chat interface
    if 'playground_messages' not in st.session_state:
        st.session_state.playground_messages = []

    # Display chat history
    for msg in st.session_state.playground_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        st.session_state.playground_messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.write(prompt)

        # Call API (non-streaming for simplicity)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Use first active API key
                    api_key = active_keys[0]['key_prefix']  # This won't work - need full key
                    # For demo, show instructions
                    st.info("💡 To test the API, use the curl command below with your API key:")
                    st.code(f"""
curl {API_BASE_URL}/v1/chat/completions \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "bot_id": "{selected_bot['id']}",
    "messages": [{{"role": "user", "content": "{prompt}"}}],
    "stream": false
  }}'
                    """, language="bash")

                except Exception as e:
                    st.error(f"Error: {e}")


# Main app
def main():
    if not st.session_state.token:
        login_page()
    else:
        # Sidebar
        with st.sidebar:
            st.title("🤖 B2B Chat API")

            if st.session_state.user:
                st.success(f"👤 {st.session_state.user['email']}")

            page = st.radio(
                "Navigation",
                ["Dashboard", "Bots", "API Keys", "Wallet", "Playground"],
                label_visibility="collapsed"
            )

            st.divider()

            if st.button("🚪 Logout"):
                st.session_state.token = None
                st.session_state.user = None
                st.rerun()

            st.divider()
            st.caption("v0.1.0")

        # Main content
        if page == "Dashboard":
            dashboard_page()
        elif page == "Bots":
            bots_page()
        elif page == "API Keys":
            api_keys_page()
        elif page == "Wallet":
            wallet_page()
        elif page == "Playground":
            playground_page()


if __name__ == "__main__":
    main()
