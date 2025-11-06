# 🎨 Mosaico
### Multilingual Content Studio

[![Version](https://img.shields.io/badge/version-0.7.1-blue.svg)](CHANGELOG.md)
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
| **Deployment** | Google Cloud Run (planned) | Serverless container deployment |
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

## 🚀 Local Setup Guide

Follow these steps to set up and run Mosaico on your local machine.

### Prerequisites

- **Python 3.11+**: [Install Python](https://www.python.org/downloads/)
- **Node.js 18+**: [Install Node.js](https://nodejs.org/)
- **PostgreSQL 14+**: We recommend using [Postgres.app](https://postgresapp.com/) on macOS.
- **Google Cloud Project**: With Vertex AI enabled.
- **Clerk Account**: For user authentication.

### 1. Backend Setup

First, set up the Python backend server.

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create a virtual environment using Python 3.11
#    Replace 'python3.11' with the command for your Python 3.11 installation
python3.11 -m venv venv

# 3. Activate the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Install dependencies
#    This will fail if you are not using Python 3.11+
pip install -r requirements.txt

# 5. Set up environment variables
cp env.example .env

# 6. Edit the .env file with your credentials:
#    - GCP_PROJECT_ID
#    - DATABASE_URL (e.g., postgresql://user:password@localhost:5432/mosaico)
#    - CLERK_SECRET_KEY
#    - GCS_BUCKET_IMAGES
#    - GOOGLE_APPLICATION_CREDENTIALS (path to your service account JSON)
#    - SLACK_WEBHOOK_URL (optional)

# 7. Create the PostgreSQL Database
#    Ensure your PostgreSQL server is running before this step.
createdb mosaico

# 8. Run database migrations
#    We use the full path to the executable to avoid shell PATH issues.
`pwd`/venv/bin/alembic upgrade head

# 9. Start the backend server
`pwd`/venv/bin/uvicorn app.main:app --reload --port 8080
or 
python -m app.main
```

The backend will be available at `http://localhost:8080`.

#### Google Cloud credentials

Mosaico calls Vertex AI from your backend. You must provide Google Cloud credentials locally in ONE of the following ways.

- Option A — gcloud Application Default Credentials (recommended for local)
  ```bash
  # Install gcloud first: https://cloud.google.com/sdk/docs/install
  gcloud auth application-default login
  gcloud config set project <YOUR_PROJECT_ID>   # e.g. mosaico-474415

  # Verify ADC are available
  gcloud auth application-default print-access-token >/dev/null && echo OK
  ```
  Notes:
  - No code/config changes are needed. The backend will automatically pick up ADC.
  - Ensure `.env` contains `GCP_PROJECT_ID=<YOUR_PROJECT_ID>`.

- Option B — Service Account JSON (works without gcloud)
  1) In Google Cloud, create/download a service account key JSON.
  2) Grant roles (minimum):
     - Vertex AI User (`roles/aiplatform.user`)
     - Storage Object Viewer (`roles/storage.objectViewer`) — for image reads
  3) Save the key locally, e.g. `~/secrets/mosaico-sa.json`.
  4) Point the backend to it:
     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS=$HOME/secrets/mosaico-sa.json
     # or set it in backend/.env (GOOGLE_APPLICATION_CREDENTIALS=/abs/path.json)
     ```
  5) Restart the backend.

### 2. Frontend Setup

Next, set up the Next.js frontend application.

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Set up environment variables
cp .env.example .env.local

# 4. Edit .env.local with your credentials:
#    - NEXT_PUBLIC_API_URL=http://localhost:8080
#    - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
#    - CLERK_SECRET_KEY

# 5. Start the frontend development server
npm run dev
```

The frontend will be available at `http://localhost:3000`.

---

## 📖 Documentation

### Core Documentation

- **[CHANGELOG.md](CHANGELOG.md)**: Version history and release notes
- **[CURRENT_STATUS.md](CURRENT_STATUS.md)**: Current project status and recent changes
- **[QUICK_START.md](QUICK_START.md)**: Step-by-step setup guide
- **[TEAM_WORKFLOW_NOTIFICATIONS.md](TEAM_WORKFLOW_NOTIFICATIONS.md)**: Team collaboration workflow and notification system

### Backend Documentation

- **[backend/README.md](backend/README.md)**: Backend architecture and API reference
- **[backend/PHASE2_SETUP.md](backend/PHASE2_SETUP.md)**: Production deployment guide
- **[backend/docs/FEW_SHOT_STRATEGY.md](backend/docs/FEW_SHOT_STRATEGY.md)**: Few-shot learning design and rationale

### Frontend Documentation

- **[frontend/MOSAICO_SETUP.md](frontend/MOSAICO_SETUP.md)**: Frontend architecture and component guide

### Archive

- **[docs/](docs/)**: Historical documentation and design decisions

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

## 🔧 Configuration

### Environment Variables

#### Backend (`.env`)
```bash
# Google Cloud
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=europe-west1
GCS_BUCKET_IMAGES=mosaico-images

# Vertex AI
VERTEX_AI_MODEL=gemini-2.5-pro
VERTEX_AI_MODEL_FLASH=gemini-2.5-flash

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/mosaico

# Authentication
CLERK_SECRET_KEY=sk_test_xxxxx
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# API
RATE_LIMIT_PER_SECOND=30
ALLOWED_ORIGINS=http://localhost:3000

# Notifications (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

#### Frontend (`.env.local`)
```bash
# API
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_BACKEND_URL=http://localhost:8080

# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
CLERK_SECRET_KEY=sk_test_xxxxx
```

---

## 🛠️ Development

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run with auto-reload
uvicorn app.main:app --reload --port 8080

# Run tests
pytest tests/

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Frontend Development

```bash
cd frontend

# Run dev server
npm run dev

# Build for production
npm run build

# Run production build
npm start

# Lint
npm run lint
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View history
alembic history
```

---

## 📊 API Endpoints

### Content Generation
- `POST /api/v1/generate` - Generate email content with dynamic structure
- `POST /api/v1/optimize-prompt` - Optimize user briefs with AI assistance
- `POST /api/v1/refine` - Refine/improve existing content
  - Options: `use_flash`, `use_few_shot`, `temperature`, `count`

### Translation
- `POST /api/v1/translate` - Translate single text
- `POST /api/v1/translate/batch` - Batch translate multiple texts to multiple languages

### Projects
- `GET /api/v1/projects` - List all projects
- `POST /api/v1/projects` - Create new project
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Media & Export
- `POST /api/v1/upload-image` - Upload image to Google Cloud Storage
- `POST /api/v1/handlebars/generate` - Generate handlebar template for component
- `POST /api/v1/projects/{id}/export` - Export project to Google Sheets (future)

Full API documentation: `http://localhost:8080/docs` (when backend is running)

---

## 🎨 Features Deep Dive

### AI Content Generation
- **Drag-and-Drop Structure Builder (V2)**: Subject + Pre-header always present; add/reorder Title/Body/CTA
- **Tone Control**: Professional, casual, enthusiastic, elegant, direct
- **Temperature Control**: 0.0 (consistent) to 1.0 (creative)
- **Image Context**: Upload product images for AI to reference during generation
- **Prompt Assistant**: AI-powered brief optimization for better results
- **Regenerate**: Regenerate all components or individual ones with preserved context
- **Few-Shot Strategy**: Only on regeneration to boost variety; kept off for initial generation to avoid JSON errors
- **Intelligent Model Selection**: Pro for long/narrative, Flash for short or image+complex, with auto-fallback
- **CTA Uppercase Normalization**: Enforced at prompt and post-processing

### Translation System
- **Batch Processing**: Translate multiple components to multiple languages in parallel
- **Context Preservation**: Maintains tone, formality, and brand voice across languages
- **Auto-Retranslation**: Regenerate All/Single re-triggers translations for changed content
- **Save & Retranslate**: Manual edits can persist and refresh all translations for that component
- **Visual Feedback**: Spinner, muted cards, disabled copy buttons during translation
- **Retry Logic & Limits**: Robustness under rate limits, with Flash model for speed

### Project Management & Navigation
- **Labels**: Colored badges on cards, editor, and sidebar; quick toggle + autosave in editor
- **Status**: `in_progress` (editable) vs `approved` (read-only UI with output-only view)
- **Sidebar**: Projects nested under In Progress / Approved; collapsible groups; persisted state
- **Dashboard Tabs**: Quick filter by In Progress, Approved, All

### Notification System

**Dual Notification Approach:**
1. **Toasts** (temporary, 3-5 seconds): Immediate feedback
2. **Notification Center** (persistent): Activity history with bell icon and badge

**Key Notifications:**
- Project created (CRM team kickoff)
- Content generated (content team review)
- Translation completed (translation team review + Airship export)

**Backend Integration:**
- Slack webhooks for team-wide visibility
- Manager oversight without being in the app

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

See `backend/PHASE2_SETUP.md` for detailed production deployment instructions.

**Triggering a new build for Vercel.**

### Manual Cloud Run deploy via GitHub Actions
- Go to GitHub → Actions → “Deploy Backend to Cloud Run” → Run workflow.
- Or push any change under `backend/` to `main`.

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

*Webhook test.*
