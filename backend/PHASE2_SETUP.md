# Phase 2 Backend Setup Guide

This guide covers the setup for the Phase 2 Mosaico platform with database and authentication.

**⚠️ COLLABORATION MODEL:** This backend supports **team collaboration**. All authenticated users can see and edit all projects. Activity logging tracks who did what. See `../COLLABORATION_MODEL.md` for details.

## Prerequisites

- PostgreSQL database (local or Cloud SQL)
- Google Cloud Storage bucket for images
- Clerk account for authentication
- Google Sheets API credentials (service account)

## Local Development Setup

### 1. Database Setup

**Option A: Local PostgreSQL**

```bash
# Install PostgreSQL (macOS)
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb mosaico

# Or using psql
psql postgres
CREATE DATABASE mosaico;
\q
```

**Option B: Docker PostgreSQL**

```bash
docker run --name mosaico-postgres \
  -e POSTGRES_DB=mosaico \
  -e POSTGRES_USER=mosaico \
  -e POSTGRES_PASSWORD=mosaico123 \
  -p 5432:5432 \
  -d postgres:15
```

### 2. Update Environment Variables

Copy and update your `.env` file:

```bash
cd backend
cp env.example .env
```

Update the following in `.env`:

```bash
# Database
DATABASE_URL=postgresql://mosaico:mosaico123@localhost:5432/mosaico

# Clerk (get from https://dashboard.clerk.com/)
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key

# Google Sheets API
GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/your/service-account.json

# Cloud Storage for images
GCS_BUCKET_IMAGES=mosaico-images
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations

```bash
# Run migrations
alembic upgrade head

# To create a new migration (if you modify models)
alembic revision --autogenerate -m "description"
```

### 5. Create Google Cloud Storage Bucket

```bash
# Create bucket for user-uploaded images
gsutil mb -l europe-west1 gs://mosaico-images

# Make bucket publicly accessible (for image URLs)
gsutil iam ch allUsers:objectViewer gs://mosaico-images
```

### 6. Setup Google Sheets API

1. Go to Google Cloud Console
2. Enable Google Sheets API
3. Create a service account
4. Download the JSON key file
5. Update `GOOGLE_SHEETS_CREDENTIALS_PATH` in `.env`

### 7. Run the Backend

```bash
python -m app.main
```

The API will be available at `http://localhost:8080`.

Visit `http://localhost:8080/docs` for interactive API documentation.

## New API Endpoints (Phase 2)

### Projects

- `POST /api/v1/projects` - Create new project
- `GET /api/v1/projects` - List all user projects
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Image Upload

- `POST /api/v1/upload-image` - Upload image to GCS
- `GET /api/v1/images/{id}` - Get image metadata
- `DELETE /api/v1/images/{id}` - Delete image

### Generation (Project-based)

- `POST /api/v1/projects/{id}/generate` - Generate content for project
- `POST /api/v1/projects/{id}/translate` - Translate all components
- `POST /api/v1/projects/{id}/export` - Export to Google Sheets

## Authentication

All Phase 2 endpoints require authentication via Clerk JWT tokens.

Include the token in the Authorization header:

```
Authorization: Bearer <clerk_jwt_token>
```

For local development without Clerk, the system will use a dev user ID when `ENVIRONMENT=development`.

## Database Schema

```
projects
├── id (PK)
├── user_id
├── name
├── brief_text
├── structure (JSON)
├── tone
├── target_languages (ARRAY)
├── created_at
└── updated_at

images
├── id (PK)
├── project_id (FK -> projects)
├── user_id
├── filename
├── gcs_path
├── gcs_public_url
└── uploaded_at

components
├── id (PK)
├── project_id (FK -> projects)
├── component_type
├── component_index
├── generated_content
├── component_url
├── image_id (FK -> images)
└── created_at

translations
├── id (PK)
├── component_id (FK -> components)
├── language_code
├── translated_content
└── created_at
```

## Troubleshooting

### Database Connection Error

```
# Check PostgreSQL is running
brew services list  # macOS
# or
docker ps  # Docker

# Test connection
psql postgresql://mosaico:mosaico123@localhost:5432/mosaico
```

### Migration Issues

```
# Reset database (WARNING: deletes all data)
alembic downgrade base
alembic upgrade head

# Or recreate database
dropdb mosaico
createdb mosaico
alembic upgrade head
```

### Clerk Authentication Issues

- Ensure `CLERK_SECRET_KEY` is set correctly
- For local dev, set `ENVIRONMENT=development` to bypass auth

## Production Deployment (Cloud Run + Cloud SQL)

### Overview

For production, we'll use **Google Cloud SQL** (managed PostgreSQL) connected to Cloud Run via private networking.

**Architecture:**
```
Cloud Run (Backend) ──Private Socket──> Cloud SQL (PostgreSQL)
                                        ↓
                                   Auto Backups
                                   High Availability
```

**Cost:** ~$10-35/month depending on instance size

---

### 1. Create Cloud SQL Instance

```bash
# Set your project ID
export PROJECT_ID=$(gcloud config get-value project)
export REGION=europe-west1

# Create PostgreSQL instance
# Tier options:
#   db-f1-micro   = Shared CPU, 614 MB RAM  (~$10/month)  - For testing/small workloads
#   db-g1-small   = 1 vCPU, 1.7 GB RAM      (~$35/month)  - Production recommended
gcloud sql instances create mosaico-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --root-password=$(openssl rand -base64 32) \
  --backup-start-time=03:00 \
  --storage-auto-increase \
  --storage-size=10GB

# Note: Save the root password if you need it for admin tasks
```

### 2. Create Database and User

```bash
# Create application database
gcloud sql databases create mosaico --instance=mosaico-db

# Generate secure password
export DB_PASSWORD=$(openssl rand -base64 32)
echo "Save this password: $DB_PASSWORD"

# Create application user
gcloud sql users create mosaico-user \
  --instance=mosaico-db \
  --password=$DB_PASSWORD

# Grant privileges (via Cloud SQL proxy)
gcloud sql connect mosaico-db --user=postgres
# Then in psql:
postgres=# GRANT ALL PRIVILEGES ON DATABASE mosaico TO "mosaico-user";
postgres=# \c mosaico
mosaico=# GRANT ALL ON SCHEMA public TO "mosaico-user";
postgres=# \q
```

### 3. Run Migrations to Production Database

**Via Cloud SQL Proxy (Recommended):**

```bash
# Install Cloud SQL Proxy (macOS)
brew install cloud-sql-proxy

# Or download directly:
curl -o cloud-sql-proxy https://dl.google.com/cloudsql/cloud_sql_proxy.darwin.arm64
chmod +x cloud-sql-proxy

# Get connection name
export DB_CONNECTION_NAME=$(gcloud sql instances describe mosaico-db --format="value(connectionName)")

# Start proxy in background
cloud-sql-proxy $DB_CONNECTION_NAME &

# Run migrations through proxy
cd backend
export DATABASE_URL="postgresql://mosaico-user:${DB_PASSWORD}@localhost:5432/mosaico"
alembic upgrade head

# Stop proxy when done
killall cloud-sql-proxy
```

### 4. Deploy Backend to Cloud Run

```bash
cd backend

# Build DATABASE_URL for Cloud Run (uses Unix socket)
export DB_CONNECTION_NAME=$(gcloud sql instances describe mosaico-db --format="value(connectionName)")
export DATABASE_URL="postgresql://mosaico-user:${DB_PASSWORD}@/mosaico?host=/cloudsql/${DB_CONNECTION_NAME}"

# Deploy with Cloud SQL connection
gcloud run deploy mosaico-backend \
  --source . \
  --region=$REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances=$DB_CONNECTION_NAME \
  --set-env-vars="DATABASE_URL=${DATABASE_URL},CLERK_SECRET_KEY=${CLERK_SECRET_KEY},GCP_PROJECT_ID=${PROJECT_ID},ENVIRONMENT=production"

# Note the service URL from the output
```

### 5. Verify Deployment

```bash
# Get Cloud Run service URL
export SERVICE_URL=$(gcloud run services describe mosaico-backend --region=$REGION --format="value(status.url)")

# Test health endpoint
curl $SERVICE_URL/health

# Test projects endpoint (requires auth)
curl $SERVICE_URL/api/v1/projects \
  -H "Authorization: Bearer YOUR_CLERK_TOKEN"
```

---

### Production Database Management

**View Logs:**
```bash
gcloud sql operations list --instance=mosaico-db --limit=10
```

**Create Backup:**
```bash
gcloud sql backups create --instance=mosaico-db
```

**List Backups:**
```bash
gcloud sql backups list --instance=mosaico-db
```

**Scale Instance:**
```bash
# Upgrade to production tier
gcloud sql instances patch mosaico-db --tier=db-g1-small
```

**Estimated Monthly Costs:**
- db-f1-micro: ~$10/month (testing/small workloads)
- db-g1-small: ~$35/month (production recommended)
- Storage (10GB): ~$2/month
- Backups (auto): ~$1/month
- **Total: $13-38/month**



CI: trigger deploy 2025-10-23T18:35:06Z
