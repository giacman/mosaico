# Phase 2 Backend Setup Guide

This guide covers the setup for the Phase 2 Mosaico platform with database and authentication.

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

## Production Deployment

See deployment guide for Cloud Run + Cloud SQL setup.

