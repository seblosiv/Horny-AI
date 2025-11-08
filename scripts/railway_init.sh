#!/bin/bash
# Railway initialization script
set -e

echo "🚀 Initializing B2B Chat API on Railway..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
sleep 5

# Initialize database
echo "🔧 Initializing database tables..."
python scripts/init_db.py

# Create test user with API key
echo "👤 Creating test user..."
python scripts/create_test_user.py

echo "✅ Initialization complete!"
