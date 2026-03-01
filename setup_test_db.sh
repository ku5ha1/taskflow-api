#!/bin/bash
# Setup test database with full schema

echo "Creating test database..."
docker exec taskflow-postgres psql -U taskflow -c "DROP DATABASE IF EXISTS taskflow_test;"
docker exec taskflow-postgres psql -U taskflow -c "CREATE DATABASE taskflow_test;"

echo "Copying schema from main database..."
docker exec taskflow-postgres pg_dump -U taskflow -d taskflow --schema-only | \
  docker exec -i taskflow-postgres psql -U taskflow -d taskflow_test

echo "Test database ready!"
