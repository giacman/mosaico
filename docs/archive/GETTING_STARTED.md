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

#### 1. Create GCP Project
- Visita: https://console.cloud.google.com/
- Click "Select a project" → "New Project"
- Nome: "Mosaico" (o quello che preferisci)
- Organization: Seleziona la tua org LuisaViaRoma
- **Annota il Project ID** (es. `mosaico-prod-12345`)

#### 2. Enable Required APIs

```bash
# Set il progetto
gcloud config set project YOUR_PROJECT_ID

# Abilita le API necessarie
gcloud services enable aiplatform.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
```

#### 3. Setup Authentication (Local Development)

**Usiamo un Service Account dedicato per Mosaico** per isolare le credenziali da altri progetti.

```bash
# A. Login base (per gcloud CLI)
gcloud auth login

# B. Crea Service Account per sviluppo locale
gcloud iam service-accounts create mosaico-dev \
  --display-name="Mosaico Local Development"

# C. Dai permessi Vertex AI al Service Account
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:mosaico-dev@$(gcloud config get-value project).iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# D. Crea chiave JSON e salvala nella home
gcloud iam service-accounts keys create ~/mosaico-dev-key.json \
  --iam-account=mosaico-dev@$(gcloud config get-value project).iam.gserviceaccount.com

# E. Aggiungi path della chiave al file .env (dopo averlo creato)
echo "" >> backend/.env
echo "# Local Development Credentials" >> backend/.env
echo "GOOGLE_APPLICATION_CREDENTIALS=/Users/gvannucchi/mosaico-dev-key.json" >> backend/.env

echo "✅ Service Account configurato!"
```

**Nota:** La chiave JSON (`~/mosaico-dev-key.json`) è già nel `.gitignore` quindi non verrà committata per sbaglio.

## 🚀 Step-by-Step Setup

### Part 1: Backend Setup (15 minutes)

#### 1. Setup Virtual Environment & Install Dependencies

```bash
cd backend

# Create virtual environment
python3 -m venv .venv-mosaico

# Activate virtual environment
# On macOS/Linux:
source .venv-mosaico/bin/activate
# On Windows:
# .venv-mosaico\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure Environment

```bash
# Copy environment template (crea file .env dalla copia)
cp env.example .env

# Apri il file .env per modificarlo
nano .env
# O usa il tuo editor preferito:
# code .env    (VS Code)
# vim .env     (Vim)
# open .env    (TextEdit su Mac)
```

**IMPORTANTE: Ora devi EDITARE il file `.env` che hai appena creato**

Il file `.env` è una copia di `env.example` - ora devi personalizzarlo con i TUOI valori.

**Step-by-step:**

1. **Trova il tuo Project ID:**
```bash
gcloud config get-value project
```
Output esempio: `mosaico-prod-12345` ← Questo è il tuo Project ID

2. **Apri il file `.env` in un editor:**
```bash
# Con nano (editor terminale)
nano .env

# O con VS Code
code .env

# O con qualsiasi editor di testo
```

3. **Modifica SOLO questa riga:**

PRIMA (nel file):
```bash
GCP_PROJECT_ID=your-project-id
```

DOPO (con il tuo vero ID):
```bash
GCP_PROJECT_ID=mosaico-prod-12345
```


**Note on Region:**
- `europe-west1` (Belgium) - Raccomandato, supporto completo
- `europe-west8` (Milan) - Più vicino, verifica supporto Vertex AI
- `europe-west4` (Netherlands) - Alternativa valida

#### 3. Test Locally

```bash
# Make sure virtual environment is activated!
# You should see (.venv-mosaico) in your terminal prompt

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
  --region europe-west1 \
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
  --region europe-west1 \
  --allow-unauthenticated
```

**Note the Cloud Run URL** - you'll need it for the add-on!
Example: `https://mosaico-backend-abcd123-uc.a.run.app`

### Part 3: Google Sheets Add-on Setup (20 minutes)

This section explains how to connect the Add-on to your **deployed Cloud Run backend**. If you want to test the Add-on with your **local backend**, please see the next section (Part 3a).

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

### Part 3a: Local Add-on Testing with ngrok (10 minutes)

To test the Google Sheets Add-on with your backend running on your local machine, you need to expose your local server to the public internet. Google's servers can't connect to `localhost:8080`. We'll use a tool called `ngrok` to create a secure tunnel.

**1. Install and run ngrok**

If you don't have ngrok, download it from [https://ngrok.com/download](https://ngrok.com/download).

Open a **new terminal window** (while your backend server is still running in another) and start ngrok. The project is configured to run on port `8080`.

```bash
# This will create a public URL for your local server on port 8080
ngrok http 8080
```

**2. Get your public URL**

After running the command, ngrok will display a public URL. Copy the `https` address. It will look something like this:

```
Forwarding                    https://1a2b-3c4d-5e6f.ngrok-free.app -> http://localhost:8080
```

**3. Configure the Add-on**

Follow the steps in "Part 3" to create the Apps Script project. When you get to the step to edit `Code.gs`, use your public `ngrok` URL.

```javascript
// In addon/src/Code.gs
// Use your public ngrok URL for local testing
const BACKEND_URL = 'https://1a2b-3c4d-5e6f.ngrok-free.app';
```

Now, your Google Sheet Add-on will send requests to your local backend server through the secure tunnel. Remember to keep ngrok running while you test.

#### 4. Test the Add-on

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

