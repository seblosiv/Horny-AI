"""
Initialize database and create tables
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, Base, init_db
from app.models import (
    User, APIKey, Wallet, Payment, Bot, Channel,
    Chat, Message, UsageLedger, AuditLog
)

def main():
    """Initialize database"""
    print("🔧 Initializing database...")

    try:
        # Create all tables
        init_db()
        print("✅ Database tables created successfully!")

        # Print created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

        print("\n✨ Database is ready!")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
