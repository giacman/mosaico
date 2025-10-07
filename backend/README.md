# Mosaico Backend

FastAPI backend for Mosaico AI Content Creation Co-Pilot.

## 🚀 Tech Stack (Modern 2025 - NO LangChain)

- **FastAPI** - Modern Python web framework
- **Vertex AI SDK** - Direct Google AI integration (no LangChain!)
- **Pydantic v2** - Data validation and settings
- **Google Cloud Platform** - Serverless deployment

## 📋 Features

- ✅ **Generate Variations** - Create multiple text alternatives with tone control
- ✅ **Translate** - Contextual translation maintaining tone and style
- ✅ **Refine** - One-click improvements (shorten, fix grammar, improve clarity)
- ✅ **Few-Shot Learning** - RAG pattern for brand voice consistency
- ✅ **Self-Healing** - Automatic JSON fixing with retry logic
- ✅ **Rate Limiting** - Prevent API abuse

## 🛠️ Setup

### Prerequisites

- Python 3.11+
- Google Cloud Project with Vertex AI API enabled
- Google Cloud credentials configured

### Installation

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Copy environment configuration
cp env.example .env

# Edit .env with your GCP settings
nano .env
```

### Configuration

Edit `.env`:

```bash
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-2.5-pro
```

### Run Locally

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Or use Python directly
python -m app.main
```

API will be available at: `http://localhost:8080`

Interactive docs: `http://localhost:8080/docs`

## 📚 API Endpoints

### Generate Variations
```http
POST /api/v1/generate
Content-Type: application/json

{
  "text": "Nuova collezione primavera",
  "count": 3,
  "tone": "professional",
  "content_type": "newsletter"
}
```

### Translate
```http
POST /api/v1/translate
Content-Type: application/json

{
  "text": "Welcome to our store",
  "target_language": "it",
  "maintain_tone": true
}
```

### Refine
```http
POST /api/v1/refine
Content-Type: application/json

{
  "text": "This is a very long text that needs to be shortened",
  "operation": "shorten",
  "content_type": "newsletter"
}
```

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── generate.py   # Variations generation
│   │   ├── translate.py  # Translation
│   │   └── refine.py     # Text refinement
│   ├── core/             # Core functionality
│   │   ├── config.py     # Settings
│   │   └── vertex_ai.py  # Vertex AI client
│   ├── models/           # Pydantic models
│   │   └── schemas.py    # Request/Response schemas
│   └── main.py           # FastAPI app
├── tests/                # Unit tests
├── requirements.txt      # Dependencies
└── env.example           # Environment template
```

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## 🚀 Deployment (Cloud Run)

```bash
# Build and deploy
gcloud run deploy mosaico-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=your-project

# Or use Dockerfile
docker build -t mosaico-backend .
docker run -p 8080:8080 mosaico-backend
```

## 🎯 Design Decisions

### Why NO LangChain?

- ❌ **LangChain** - Over-engineered, considered legacy in 2025
- ✅ **Vertex AI SDK** - Direct, modern, native Google integration
- ✅ **Simpler codebase** - 800 lines vs 5000+ with LangChain
- ✅ **Better control** - Direct access to all Vertex AI features

### Pattern Reuse from InventioHub

✅ **What we took:**
- Prompt engineering structure
- Few-shot learning pattern (RAG)
- Output self-healing logic
- Pydantic models with descriptions

❌ **What we didn't take:**
- LangChain framework
- Django backend
- Task queue complexity
- State machine with 7 states

## 📊 Performance

- **Latency**: ~1-2s per generation (Vertex AI)
- **Rate Limit**: 5 requests/second (configurable)
- **Cost**: ~$0.02 per request (Gemini 2.5 Pro)

## 🔐 Security

- Rate limiting per IP
- CORS configuration
- Environment-based secrets
- No hardcoded credentials

## 📝 License

Private - LuisaViaRoma Internal Project
