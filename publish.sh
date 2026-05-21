#!/bin/bash

# Publish script for FocusTrack AI
echo "🚀 Welcome to FocusTrack AI Publisher"
read -p "Enter new version (e.g., v4.0.0): " NEW_VERSION

if [[ -z "$NEW_VERSION" ]]; then
    echo "Version cannot be empty."
    exit 1
fi

if [[ ! "$NEW_VERSION" == v* ]]; then
    NEW_VERSION="v$NEW_VERSION"
fi

echo "Updating .env with APP_VERSION=$NEW_VERSION"
# Remove old APP_VERSION if exists and append new
if grep -q "^APP_VERSION=" .env; then
    sed -i "s/^APP_VERSION=.*/APP_VERSION=$NEW_VERSION/" .env
else
    echo "APP_VERSION=$NEW_VERSION" >> .env
fi

echo "Building Docker container..."
docker-compose build

echo "Starting deployment..."
docker-compose up -d

echo "✅ App updated to $NEW_VERSION and deployed!"