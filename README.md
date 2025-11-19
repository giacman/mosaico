# 🎨 Mosaico
### Multilingual Content Studio

[![Version](https://img.shields.io/badge/version-0.9.0-blue.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Private-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/next.js-15.3-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![Cloud Run](https://img.shields.io/github/actions/workflow/status/giacman/mosaico/cloud-run-backend.yml?label=Cloud%20Run%20Deploy&logo=googlecloud&logoColor=white)](https://github.com/giacman/mosaico/actions/workflows/cloud-run-backend.yml)
[![Vercel](https://img.shields.io/badge/Vercel-Frontend%20Deploy-black?logo=vercel)](https://vercel.com/dashboard)

---

## 📋 Overview

**Mosaico** is an AI-powered platform for creating, translating, and managing multilingual email campaign content. Built for modern marketing teams, it streamlines the workflow from content creation to export, leveraging **Google Vertex AI (Gemini 2.5)** for intelligent content generation.

### Key Features

- ✨ **AI Content Generation**: Create email components (subjects, pre-headers, title, body, CTAs) with customizable tone and structure
- 🌍 **Batch Translation**: Translate content to multiple languages simultaneously with context preservation
- 🎯 **Drag-and-Drop Email Structure**: Visual builder with always-on Subject & Pre-header; add/reorder Title, Body, CTAs
- 🖼️ **Image Context**: Generate content based on uploaded product images
- 🔄 **Regenerate & Refine**: Fine-tune individual components with temperature control (0.0-1.0)
- 🧠 **Intelligent Model Selection**: Auto-choose Gemini Pro vs Flash with JSON-stability fallback
- 📊 **Project Management**: Organize campaigns with team collaboration and activity tracking
- 🏷️ **Labels**: Add pastel color labels to projects (dashboard, editor, sidebar)
- ✅ **Status**: `in_progress` (editable) vs `approved` (read-only) with UI gating
- 🧭 **Sidebar & Filters**: Projects nested under In Progress / Approved; dashboard tabs for filtering
- 🔔 **Notifications**: Real-time in-app and Slack notifications for team handoffs
- 📤 **Handlebar Export**: Export components with multi-language handlebar templates for Airship integration
- 🔠 **CTA Consistency**: CTAs normalized to UPPERCASE across generation and regeneration
- 🔁 **Auto-Retranslation**: Regeneration and manual edits trigger translation updates with clear UX states
  - Single-component regenerate now automatically re-translates only that component
  - Notification bell persists entries across navigation

---

## 🏗️ Architecture

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 15, React, TypeScript, Tailwind CSS, shadcn/ui | Modern web application with real-time updates |
| **Backend** | Python, FastAPI, SQLAlchemy, Alembic | RESTful API with async support |
| **Database** | PostgreSQL | Project data, components, translations, activity logs |
| **AI** | Google Vertex AI (Gemini 2.5 Pro/Flash) | Content generation, translation, prompt optimization |
| **Storage** | Google Cloud Storage | User-uploaded images, prompt templates |
| **Auth** | Clerk | User authentication and authorization |
| **Deployment** | Google Cloud Run | Serverless container deployment |
| **Monitoring** | Cloud Logging, Slack Webhooks | Error tracking and team notifications |

### System Flow

```
User (Next.js Frontend)
    ↓
Clerk Authentication
    ↓
FastAPI Backend (Cloud Run)
    ↓
┌─────────────┬──────────────┬───────────────┐
│  PostgreSQL │  Vertex AI   │  Cloud Storage│
│  (Projects) │  (Gemini)    │  (Images)     │
└─────────────┴──────────────┴───────────────┘
    ↓
Export to Airship (Handlebar Templates)
```

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

### 2. Run the Application

#### Start Backend & Database
From the project root:

```bash
docker compose up -d --build
```
- This starts PostgreSQL (port 5433 host / 5432 container) and Backend (port 8000 host / 8080 container).
- It automatically runs database migrations on startup.

**Verify Backend:** `curl http://localhost:8000/health`

#### Start Frontend
From the `frontend` directory:

```bash
npm install
npm run dev
```
**Access Frontend:** `http://localhost:3000`

---

## 📖 Documentation

### Core Documentation

- **[CHANGELOG.md](CHANGELOG.md)**: Version history and release notes
- **[CURRENT_STATUS.md](CURRENT_STATUS.md)**: Current project status and recent changes
- **[QUICK_START.md](QUICK_START.md)**: Summary setup guide
- **[TEAM_WORKFLOW_NOTIFICATIONS.md](TEAM_WORKFLOW_NOTIFICATIONS.md)**: Team collaboration workflow and notification system

### Backend Documentation

- **[backend/README.md](backend/README.md)**: Backend architecture and API reference
- **[backend/docs/FEW_SHOT_STRATEGY.md](backend/docs/FEW_SHOT_STRATEGY.md)**: Few-shot learning design and rationale

---

## 🎯 Team Workflow

Mosaico supports a collaborative multi-team workflow:

### 1. **Project Setup** (CRM Team)
- Create new campaign project
- Define email structure (subjects, CTAs, body sections)
- Add creative brief and context
- Upload product images
- Add URLs for CTAs and products

### 2. **Content Generation** (AI + Content Team Review)
- AI generates email components based on brief and images
- Intelligent model selection (Pro/Flash) with automatic Flash fallback for JSON stability
- Few-shot examples used during regeneration only, for higher variety without breaking JSON
- Individual component regeneration with temperature control
- Real-time editing and approval

### 3. **Translation** (AI + Translation Team Review)
- Batch translate to multiple languages (IT, DE, FR, ES, PT, RU, ZH, JA, AR, NL)
- Auto-retranslation after Regenerate All / Regenerate Single if translations existed
- "Save & Retranslate" after manual edits to keep translations in sync
- Spinner + greyed-out states + disabled actions during translation

### 4. **Export to Airship** (CRM Team)
- Export components as handlebar templates
- Copy/paste into Airship email editor
- Handlebar format supports dynamic language selection

**Example Handlebar Output:**
```handlebars
{{#eq selected_language "IT"}}Scopri la collezione{{else eq selected_language "FR"}}Découvrez la collection{{else}}Discover the collection{{/eq}}
```

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

After merging a change to the `main` branch that includes a new database migration file (generated by `alembic revision`), you must manually apply this migration to the production database.

**Steps to Apply Migrations:**

1.  **Open Google Cloud Shell** for the `mosaico-474415` project.
2.  **Navigate to the backend directory**:
    ```bash
    cd mosaico/backend
    ```
3.  **Set up the environment**: You will need to `export` the required environment variables (`DATABASE_URL`, `CLERK_SECRET_KEY`, etc.) just as we did during our debugging session.
4.  **Run the migration command**:
    ```bash
    alembic upgrade head
    ```

This will bring your production database schema in sync with your latest code.

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

---

## 📞 Support

For questions or issues:
- Check the [documentation](docs/)
- Review [CURRENT_STATUS.md](CURRENT_STATUS.md) for known issues
- Contact the development team

---

**Built with ❤️ for modern marketing teams**
