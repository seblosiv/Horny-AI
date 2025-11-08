"""
Create a test user for development
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import User, Wallet, APIKey
from app.auth import hash_password, generate_api_key


def main():
    """Create test user"""
    db = SessionLocal()

    try:
        # Create user
        email = "test@example.com"
        password = "testpassword123"

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"⚠️  User {email} already exists")
            user = existing
        else:
            user = User(
                email=email,
                password_hash=hash_password(password)
            )
            db.add(user)
            db.flush()

            # Create wallet
            wallet = Wallet(
                user_id=user.id,
                balance_cents=10000,  # $100 for testing
                total_deposited_cents=10000
            )
            db.add(wallet)
            db.commit()
            db.refresh(user)

            print(f"✅ Created user: {email}")
            print(f"💰 Wallet balance: $100.00")

        # Create API key
        full_key, key_prefix, key_hash = generate_api_key()

        api_key = APIKey(
            user_id=user.id,
            name="Test API Key",
            key_prefix=key_prefix,
            key_hash=key_hash
        )
        db.add(api_key)
        db.commit()

        print(f"\n🔑 API Key created:")
        print(f"   {full_key}")
        print(f"\n⚠️  Save this key! It won't be shown again.\n")

        print(f"📧 Email: {email}")
        print(f"🔒 Password: {password}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
