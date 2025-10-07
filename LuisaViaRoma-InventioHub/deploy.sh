#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Pulling latest changes from git..."
git pull origin

echo "Installing frontend dependencies..."
cd frontend
npm install

echo "Building frontend..."
npm run build

cd ..

echo "Stopping existing Docker containers..."
docker-compose down

echo "Rebuilding and starting Docker containers in detached mode..."
docker-compose up --build -d

echo "Deployment complete."
