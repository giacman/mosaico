# Getting Started with Mosaico

Welcome to Mosaico - Your AI Content Creation Co-Pilot! 🚀

This guide will help you set up and run Mosaico from scratch.

## 📋 What You'll Build

- ✅ **Backend API** - FastAPI + Vertex AI (modern, NO LangChain)
- ✅ **Google Sheets Add-on** - AI assistant directly in Sheets
- ✅ **Few-Shot Learning** - Brand voice consistency through RAG
- ✅ **Self-Healing AI** - Automatic JSON fixing with retry logic

## 🎯 Prerequisites

### Required
- Python 3.11+
- Google Cloud Project
- Google Account (for Sheets Add-on)
- Basic knowledge of Python and Google Apps Script

### GCP Setup
1. Create GCP Project: https://console.cloud.google.com/
2. Enable APIs:
   - Vertex AI API
   - Cloud Run API
   - Cloud Storage API
3. Set up authentication:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud auth application-default login
   ```

## 🚀 Step-by-Step Setup

### Part 1: Backend Setup (15 minutes)

#### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### 2. Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env file
nano .env
```

Set these variables:
```bash
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-2.5-pro
```

#### 3. Test Locally

```bash
# Run backend
python -m app.main

# Or with uvicorn
uvicorn app.main:app --reload --port 8080
```

Visit: http://localhost:8080/docs to see interactive API docs

#### 4. Test API

```bash
# Test generate endpoint
curl -X POST http://localhost:8080/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Nuova collezione primavera",
    "count": 3,
    "tone": "professional"
  }'
```

Expected response:
```json
{
  "variations": [
    "Scopri la nuova collezione primavera/estate",
    "La collezione PE2025 ti aspetta",
    "Novità stagionali: esplora la gamma"
  ],
  "original_text": "Nuova collezione primavera",
  "tone": "professional"
}
```

### Part 2: Deploy to Cloud Run (10 minutes)

#### Option A: Deploy from Source (Easiest)

```bash
cd backend

gcloud run deploy mosaico-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=your-project-id
```

#### Option B: Deploy with Docker

```bash
cd backend

# Build image
docker build -t gcr.io/YOUR_PROJECT/mosaico-backend .

# Push to GCR
docker push gcr.io/YOUR_PROJECT/mosaico-backend

# Deploy
gcloud run deploy mosaico-backend \
  --image gcr.io/YOUR_PROJECT/mosaico-backend \
  --region us-central1 \
  --allow-unauthenticated
```

**Note the Cloud Run URL** - you'll need it for the add-on!
Example: `https://mosaico-backend-abcd123-uc.a.run.app`

### Part 3: Google Sheets Add-on Setup (20 minutes)

#### 1. Create Apps Script Project

1. Open Google Sheets: https://sheets.google.com
2. Create new spreadsheet
3. Extensions → Apps Script
4. Project name: "Mosaico"

#### 2. Copy Code Files

**File 1: Code.gs**
- Copy content from `addon/src/Code.gs`
- **IMPORTANT**: Update `BACKEND_URL` with your Cloud Run URL:
```javascript
const BACKEND_URL = 'https://mosaico-backend-YOUR-URL.run.app';
```

**File 2: Sidebar.html**
- In Apps Script: File → New → HTML file
- Name it "Sidebar" (no extension)
- Copy content from `addon/src/Sidebar.html`

**File 3: appsscript.json**
- In Apps Script: View → Show manifest file
- Replace content with `addon/appsscript.json`

#### 3. Test the Add-on

1. Save all files (Ctrl+S / Cmd+S)
2. Refresh your Google Sheet
3. You should see: "Extensions → Mosaico → Open Mosaico"
4. Click it!

#### 4. First Test

1. In a Sheet cell, type: "Nuova collezione primavera"
2. Select the cell
3. In Mosaico sidebar:
   - Click "📝 Load from Selected Cell"
   - Choose tone: "Professional"
   - Count: 3
   - Click "✨ Generate Variations"
4. Wait ~2 seconds
5. 3 variations appear in cells below! 🎉

## 🎉 You're Done!

You now have:
- ✅ Backend running on Cloud Run
- ✅ Add-on working in Google Sheets
- ✅ AI-powered content generation at your fingertips

## 📊 Next Steps

### Customize Few-Shot Examples

Currently examples are hardcoded in `backend/app/api/generate.py`.

To use Cloud Storage (production-ready):

1. Create GCS bucket:
```bash
gsutil mb gs://mosaico-examples
```

2. Upload examples:
```bash
# Create example JSON
cat > example1.json << 'EOF'
{
  "input": "Your input text",
  "output": ["variation 1", "variation 2", "variation 3"]
}
EOF

gsutil cp example1.json gs://mosaico-examples/newsletter/professional/
```

3. Update `load_few_shot_examples()` in `generate.py` to load from GCS

### Add More Content Types

Edit `backend/app/models/schemas.py`:
```python
class ContentType(str, Enum):
    NEWSLETTER = "newsletter"
    SOCIAL_POST = "social_post"
    PRODUCT_DESCRIPTION = "product_description"
    YOUR_NEW_TYPE = "your_new_type"  # Add this
```

### Monitor Costs

```bash
# Check Vertex AI usage
gcloud billing accounts list
gcloud billing projects link YOUR_PROJECT --billing-account=YOUR_BILLING_ACCOUNT

# Set budget alerts in Console
```

### Share with Team

#### Option A: Share Spreadsheet
- Share your Sheet with colleagues
- They see Extensions → Mosaico automatically

#### Option B: Publish as Add-on
- Apps Script: Deploy → New deployment
- Choose type: "Add-on"
- Configure scopes
- Submit to Google Workspace Marketplace (internal)

## 🐛 Troubleshooting

### Backend Issues

**"Vertex AI API not enabled"**
```bash
gcloud services enable aiplatform.googleapis.com
```

**"Permission denied"**
```bash
# Give Cloud Run service account Vertex AI permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

**"Module not found"**
```bash
cd backend
pip install -r requirements.txt --upgrade
```

### Add-on Issues

**"Failed to call Mosaico API"**
- Check `BACKEND_URL` in Code.gs
- Verify backend is running: visit URL/health
- Check if `--allow-unauthenticated` is set on Cloud Run

**"Script timeout"**
- Apps Script has 6min timeout
- If backend is slow, check Vertex AI quotas

**"Authorization required"**
- First run: Apps Script asks for permissions
- Click "Advanced" → "Go to Mosaico (unsafe)" → "Allow"

## 📚 Learn More

- [Backend README](backend/README.md) - API documentation
- [Add-on README](addon/README.md) - Add-on customization
- [Architecture Overview](README.md) - Project vision

## 💬 Support

For issues or questions:
1. Check backend logs: `gcloud run logs read mosaico-backend`
2. Check add-on logs: Apps Script → Executions
3. Review this guide again

## 🎯 Success Checklist

- [ ] Backend runs locally (http://localhost:8080/docs works)
- [ ] Backend deployed to Cloud Run (health endpoint returns 200)
- [ ] Add-on appears in Google Sheets Extensions menu
- [ ] Generated first variation successfully
- [ ] Translation works
- [ ] Refine operations work

**All checked?** Congratulations! You're ready to scale Mosaico! 🚀

---

**Time to complete**: ~45 minutes  
**Difficulty**: Intermediate  
**Result**: Production-ready AI content assistant

