# 🎨 Mosaico
### Multilingual Content Studio

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Private-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/next.js-15.3-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![Cloud Run](https://img.shields.io/github/actions/workflow/status/giacman/mosaico/cloud-run-backend.yml?label=Cloud%20Run%20Deploy&logo=googlecloud&logoColor=white)](https://github.com/giacman/mosaico/actions/workflows/cloud-run-backend.yml)
[![Vercel](https://img.shields.io/badge/Vercel-Frontend%20Deploy-black?logo=vercel)](https://vercel.com/dashboard)

---

## 📋 Overview

**Mosaico** is an AI-powered platform for creating, translating, and managing multilingual email campaign content. Built for modern marketing teams, it streamlines the workflow from content creation to export, leveraging **Google Vertex AI (Gemini 2.5)** for intelligent content generation.

---

## ✨ Key Features

- 🤖 **AI Content Generation**: Create email components (subjects, pre-headers, title, body, CTAs) with customizable tone and structure
- 📱 **Push Notifications**: Create mobile push notifications with strict character limits (Title: 20, Body: 100, CTA: 30 chars) - convert newsletter sections to push with one click
- 🎓 **Few-Shot Learning**: Strategic use of examples during regeneration to increase content variety while maintaining JSON stability
- 🌍 **Enhanced Translation System**: AI-powered transcreation with Sequential Validation
  - Gemini 2.5 Pro for cultural nuance and natural phrasing
  - Automatic quality validation with confidence scoring (0-1 scale)
  - Self-healing retry if confidence < 0.7 (auto-corrects poor translations)
  - Language-specific guidance (DE, FR, ES, IT, PT) to avoid literal translations
- 🎯 **Drag-and-Drop Email Structure**: Visual builder with always-on Subject & Pre-header; add/reorder Title, Body, CTAs, and Images
- 🖼️ **Image Context**: Generate content based on uploaded product images
- 🔄 **Regenerate & Refine**: Fine-tune individual components with temperature control (0.0-1.0)
- 🧠 **Intelligent Model Selection**: Auto-choose Gemini Pro vs Flash with JSON-stability fallback
- 📊 **Project Management**: Organize campaigns with team collaboration and activity tracking
- 🏷️ **Labels & Status**: Add pastel color labels; `in_progress` (editable) vs `approved` (read-only) with UI gating
- 🧭 **Sidebar & Filters**: Projects nested under In Progress / Approved; dashboard tabs for filtering
- 🔔 **Notifications**: Real-time in-app and Slack notifications for team handoffs with persistent notification bell
- 📤 **Handlebar Export**: Export components with multi-language handlebar templates for Airship integration
- 🔠 **CTA Consistency**: CTAs normalized to UPPERCASE across generation and regeneration
- 🔁 **Auto-Retranslation**: Regeneration and manual edits trigger translation updates with clear UX feedback states

---

## 🏗️ Architecture

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 15, React, TypeScript, Tailwind CSS, shadcn/ui | Modern web application with real-time updates |
| **Backend** | Python, FastAPI, SQLAlchemy, Alembic | RESTful API with async support |
| **Database** | PostgreSQL (local), Google Cloud SQL (production) | Project data, components, translations, activity logs |
| **AI** | Google Vertex AI (Gemini 2.5 Pro/Flash) | Content generation, translation, prompt optimization |
| **Storage** | Google Cloud Storage | User-uploaded images, prompt templates |
| **Auth** | Clerk | User authentication and authorization |
| **Deployment** | Vercel (Frontend), Google Cloud Run (Backend) | Serverless deployment |
| **Monitoring** | Cloud Logging, Slack Webhooks | Error tracking and team notifications |

### System Flow

```
User (Next.js Frontend on Vercel)
    ↓
Clerk Authentication
    ↓
FastAPI Backend (Cloud Run)
    ↓
┌──────────────────┬──────────────┬───────────────┐
│  PostgreSQL      │  Vertex AI   │  Cloud Storage│
│  (Local Dev) or  │  (Gemini)    │  (Images)     │
│  Cloud SQL (Prod)│              │               │
└──────────────────┴──────────────┴───────────────┘
    ↓
Export to Airship (Handlebar Templates)
```

### Translation Quality System

Mosaico implements a **2-level optimization approach** for high-quality transcreation (creative adaptation vs literal translation):

1. **Enhanced Prompt Engineering**: Focus on cultural adaptation, naturalness, and context-aware word choice (e.g., German "genießen" for content, not "schmecken" for food)
2. **Sequential Validation Chain**: AI-powered quality reviewer validates translations with confidence scoring; auto-retries with feedback if score < 0.7

**Result**: ~90-95% translation quality with self-healing capability. See [docs/TRANSLATION_QUALITY_APPROACHES.md](docs/TRANSLATION_QUALITY_APPROACHES.md) for technical details.

---

## 🚀 Local Setup Guide (Docker)

This is the recommended way to run Mosaico locally. It ensures consistent environments and simplifies dependency management.

### Prerequisites

- **Docker Desktop**: [Install Docker](https://www.docker.com/products/docker-desktop/)
- **Node.js 18+**: [Install Node.js](https://nodejs.org/) (for the frontend)
- **Google Cloud SDK (`gcloud`)**: [Install gcloud](https://cloud.google.com/sdk/docs/install)
- **Clerk Account**: For user authentication.

### 1. Environment Setup

**Note:** There are two main environment files you need to configure.

#### A. Root Configuration (Backend & Docker)
Create a `.env` file in the **project root** (`/mosaico/.env`). This configures Docker Compose, the Database, and the Backend.

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
- **Postgres**: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (e.g., `mosaico`)
- **Database URL**: `DATABASE_URL=postgresql+psycopg2://mosaico:mosaico@db:5432/mosaico` (must match Postgres values)
- **Google Cloud**: `GCP_PROJECT_ID`, `GCP_LOCATION`
- **Vertex AI**: `VERTEX_AI_MODEL=gemini-2.5-pro`
- **Storage**: `GCS_BUCKET_IMAGES` (e.g., `mosaico-images-dev-xxxxx`)
- **Auth**: `CLERK_SECRET_KEY`

**Authenticate locally:**
To let the backend container access GCP services (Vertex AI, GCS):
```bash
gcloud auth application-default login
gcloud config set project <YOUR_GCP_PROJECT_ID>
```

#### B. Frontend Configuration
Create a `.env.local` file in the **frontend directory** (`/mosaico/frontend/.env.local`).

```bash
cd frontend
cp .env.example .env.local
```

Edit `.env.local`:
- `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` (Use 127.0.0.1 to avoid node/docker network issues)
- `NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000`
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`

---

### 2. Initial Build

Build the Docker images for the first time or after code changes:

```bash
docker compose up -d --build
```
- This **rebuilds** the Docker images with your latest code
- Starts PostgreSQL (port 5433 host / 5432 container) and Backend (port 8000 host / 8080 container)
- Automatically runs database migrations on startup

**Verify Backend:** `curl http://localhost:8000/health`

---

## 🏃 Run Locally

Once you've completed the setup above, use these commands for daily development:

### Start Backend & Database (using existing images)

```bash
docker compose up -d
```
*Note: Only use `--build` flag when you've made changes to the backend code.*

### View Logs

To follow the logs after starting in detached mode:

```bash
# View all service logs
docker compose logs -f

# View logs for specific service
docker compose logs -f backend
docker compose logs -f db

# View last 100 lines and then follow
docker compose logs -f --tail=100
```

*Press `Ctrl+C` to stop following logs (containers continue running).*

### Start Frontend

From the `frontend` directory:

```bash
npm run dev
```

**Access the Application:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

---

## 📖 Documentation

- **[CHANGELOG.md](CHANGELOG.md)**: Version history and release notes
- **[QUICK_START.md](QUICK_START.md)**: Quick setup guide
- **[TEAM_WORKFLOW_NOTIFICATIONS.md](TEAM_WORKFLOW_NOTIFICATIONS.md)**: Team collaboration workflow and notification system
- **[backend/docs/FEW_SHOT_STRATEGY.md](backend/docs/FEW_SHOT_STRATEGY.md)**: Few-shot learning design and rationale
- **API Documentation**: `http://localhost:8000/docs` (when running locally)

---

## 🔐 Security

- **Authentication**: Clerk-based user authentication with JWT tokens
- **Authorization**: Role-based access control (future enhancement)
- **API Security**: Rate limiting, input validation, CORS configuration
- **Secrets Management**: Environment variables, Google Secret Manager for production
- **Database**: PostgreSQL with parameterized queries (SQLAlchemy ORM)
- **File Upload**: Validated file types and size limits, GCS with public URLs

---

## 🚢 Deployment

The backend is deployed via GitHub Actions to Google Cloud Run. The frontend is deployed to Vercel.

### Manual Database Migrations in Production

**IMPORTANT**: The automated CI/CD workflow for the backend **does not** run database migrations automatically.

After merging a change to the `main` branch that includes a new database migration file, you must manually apply this migration to the production database.

#### Method 1: Using Alembic (Recommended)

**From Google Cloud Shell** (browser-based):

```bash
# 1. Clone the repo (or pull latest if already cloned)
git clone https://github.com/giacman/mosaico.git
cd mosaico/backend

# 2. Download and start Cloud SQL Auth Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.0/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy
./cloud-sql-proxy --unix-socket=/tmp mosaico-474415:europe-west1:mosaico-db &

# 3. Install dependencies
pip install -r requirements.txt
export PATH=$PATH:~/.local/bin

# 4. Set environment variables
export DATABASE_URL="postgresql+psycopg2://mosaicoapp:PASSWORD@/mosaico?host=/tmp/mosaico-474415:europe-west1:mosaico-db"
export GCP_PROJECT_ID="mosaico-474415"
export GCP_LOCATION="europe-west1"
export VERTEX_AI_MODEL="gemini-2.5-pro"
export GCS_BUCKET_IMAGES="mosaico-images-474415"
export CLERK_SECRET_KEY="sk_xxxxx"

# 5. Run migration
alembic upgrade head
```

**Note**: Get actual PASSWORD and CLERK_SECRET_KEY from Cloud Run:
```bash
gcloud run services describe mosaico-backend --region=europe-west1 --format='value(spec.template.spec.containers[0].env)'
```

#### Method 2: Direct SQL (For Quick Fixes)

If you need to run SQL directly without Alembic:

```bash
# Connect to the database
gcloud sql connect mosaico-db --user=mosaicoapp --database=mosaico
# Enter password when prompted, then run your SQL
```

#### Tips

- **Non-destructive migrations** (adding new tables): Safe to merge first, then migrate
- **Destructive migrations** (dropping/altering): Run migration before merge
- **Verify migration**: Run `alembic current` to check the current revision

### Google Cloud Run (Recommended)

```bash
# Backend deployment
cd backend
gcloud run deploy mosaico-backend \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=xxx,DATABASE_URL=xxx

# Frontend deployment (Vercel recommended)
cd frontend
vercel --prod
```

---

## 🤝 Contributing

This is a private project. For internal development:

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes and commit: `git commit -m "feat: add feature"`
3. Push to the branch: `git push origin feature/my-feature`
4. Create a Pull Request

### Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions/changes

---

## 📝 License

Private & Confidential - All Rights Reserved

---

## 🙏 Acknowledgments

- **Google Vertex AI (Gemini)** for powering the AI capabilities
- **Clerk** for seamless authentication
- **shadcn/ui** for beautiful UI components
- **FastAPI** for the high-performance backend framework
- **Next.js** for the modern React framework

