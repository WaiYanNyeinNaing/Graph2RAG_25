#!/bin/bash

# Bosch Graph2RAG Server with Authentication
# This script starts the server with user authentication enabled

echo "🔐 Starting Bosch Graph2RAG with Authentication"
echo "=============================================="

# Set working directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./install_local.sh first"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Load authentication configuration
if [ -f ".env.auth" ]; then
    echo "📋 Loading authentication configuration..."
    source .env.auth
else
    echo "⚠️  No .env.auth file found. Creating from template..."
    cp .env.auth.sample .env.auth
    echo "📝 Please edit .env.auth with your configuration"
    exit 1
fi

# Create default admin user if no users exist
if [ ! -f "users.json" ]; then
    echo "👤 Creating default admin user..."
    python manage_users.py add <<EOF
admin
admin@bosch.com
admin123
admin123
EOF
fi

# Display user information
echo ""
echo "📊 Configuration:"
echo "   - Port: ${PORT:-9621}"
echo "   - Authentication: ENABLED"
echo "   - Users file: ./users.json"
echo ""

# Show registered users
python manage_users.py list

echo ""
echo "🌐 Starting server..."
echo "   - Web UI: http://localhost:${PORT:-9621}"
echo "   - API Docs: http://localhost:${PORT:-9621}/docs"
echo "   - Login: http://localhost:${PORT:-9621}/auth/login"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the authenticated server
python lightrag_server_auth.py