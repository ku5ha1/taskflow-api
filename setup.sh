#!/bin/bash

# TaskFlow API Setup Script
# This script helps you set up the environment for the first time

set -e

echo "=========================================="
echo "TaskFlow API - Initial Setup"
echo "=========================================="
echo ""

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Using existing .env file."
        exit 0
    fi
fi

# Copy .env.example to .env
echo "📋 Creating .env file from .env.example..."
cp .env.example .env

# Generate a secure SECRET_KEY
echo "🔐 Generating secure SECRET_KEY..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
sed -i "s|your-secret-key-change-in-production|$SECRET_KEY|g" .env

# Prompt for custom admin credentials
echo ""
echo "👤 Configure Super Admin Account"
echo "=================================="
read -p "Admin Username (default: admin): " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}

read -p "Admin Email (default: admin@taskflow.local): " ADMIN_EMAIL
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@taskflow.local}

read -sp "Admin Password (default: admin123): " ADMIN_PASS
echo
ADMIN_PASS=${ADMIN_PASS:-admin123}

# Update admin credentials in .env
sed -i "s|ADMIN_USERNAME=admin|ADMIN_USERNAME=$ADMIN_USER|g" .env
sed -i "s|ADMIN_EMAIL=admin@taskflow.local|ADMIN_EMAIL=$ADMIN_EMAIL|g" .env
sed -i "s|ADMIN_PASSWORD=admin123|ADMIN_PASSWORD=$ADMIN_PASS|g" .env

# Prompt for database credentials
echo ""
echo "🗄️  Configure Database"
echo "======================"
read -p "PostgreSQL Password (default: taskflow_dev): " DB_PASS
DB_PASS=${DB_PASS:-taskflow_dev}
sed -i "s|POSTGRES_PASSWORD=taskflow_dev|POSTGRES_PASSWORD=$DB_PASS|g" .env

# Prompt for MinIO credentials
echo ""
echo "📦 Configure MinIO Storage"
echo "==========================="
read -p "MinIO Root User (default: minioadmin): " MINIO_USER
MINIO_USER=${MINIO_USER:-minioadmin}

read -sp "MinIO Root Password (default: minioadmin): " MINIO_PASS
echo
MINIO_PASS=${MINIO_PASS:-minioadmin}

sed -i "s|MINIO_ROOT_USER=minioadmin|MINIO_ROOT_USER=$MINIO_USER|g" .env
sed -i "s|MINIO_ROOT_PASSWORD=minioadmin|MINIO_ROOT_PASSWORD=$MINIO_PASS|g" .env

echo ""
echo "✅ Configuration complete!"
echo ""
echo "📝 Summary:"
echo "  - .env file created"
echo "  - SECRET_KEY generated"
echo "  - Admin credentials configured"
echo "  - Database credentials configured"
echo "  - MinIO credentials configured"
echo ""
echo "🚀 Next steps:"
echo "  1. Review your .env file: nano .env"
echo "  2. Start the services: docker-compose up -d"
echo "  3. Check health: curl http://localhost:8000/health"
echo "  4. Login with admin credentials"
echo ""
echo "📖 For more information, see CONFIG.md"
echo ""
