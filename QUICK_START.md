# 🚀 Mosaico Quick Start Guide

## ✅ Current Status

**Backend:** Running on http://localhost:8000 (Docker)  
**Frontend:** Running on http://localhost:3000 (Next.js)  
**Database:** PostgreSQL ready (Docker)  
**Auth:** Clerk configured

---

## 🎯 What's Working Right Now

### 1. Projects Dashboard
Visit: **http://localhost:3000/dashboard**

You should see:
- Empty state if no projects ("No Projects Yet")
- OR grid of project cards if projects exist
- "+ New Project" button in top right

### 2. Create a Project
1. Click "+ New Project"
2. Enter:
   - **Name:** "Spring Campaign 2025"
   - **Brief:** "Promote our new handbag collection"
3. Click "Create Project"
4. You'll be redirected to the project editor!

### 3. View Projects
- Each project card shows:
  - Name
  - Brief (first 2 lines)
  - Component count
  - Target languages count
  - "Updated X ago by [User]"
- Hover to see Edit/Delete menu

### 4. Delete a Project
- Click the "⋮" menu on a project card
- Click "Delete"
- Confirm deletion

---

## 🔧 If Something's Not Working

### Backend Not Running?

We use Docker Compose now.

```bash
cd /Users/gvannucchi/Projects/mosaico
docker compose up -d --build
```

You should see:
- `mosaico_backend_local`
- `mosaico_db_local`

Check status: `docker compose ps`

### Frontend Not Running?

```bash
cd /Users/gvannucchi/Projects/mosaico/frontend
npm run dev
```

You should see:
```
▲ Next.js 15.3.3 (Turbopack)
- Local:        http://localhost:3000
```

### Database Connection Issues?

The database runs in Docker on port `5433` (host).

```bash
# Test connection
psql -h localhost -p 5433 -U mosaico -d mosaico -c "SELECT COUNT(*) FROM projects;"
```

### Authentication Not Working?

- Make sure `frontend/.env.local` has valid Clerk keys:
  - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...`
  - `CLERK_SECRET_KEY=sk_test_...`

### API Connection Refused?

Make sure `frontend/.env.local` points to `127.0.0.1`:
```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
```

---

## 📋 Test the Full Flow

### Step 1: Create a Test Project via API

```bash
# Get your Clerk JWT token from browser DevTools
# (Application > Local Storage > clerk-db-jwt)

curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "name": "Test Campaign",
    "brief_text": "This is a test",
    "structure": [
      {"component": "subject", "count": 1},
      {"component": "pre_header", "count": 1}
    ],
    "tone": "professional",
    "target_languages": ["it", "fr"]
  }'
```

### Step 2: Verify in Frontend
- Visit http://localhost:3000/dashboard
- You should see "Test Campaign" card

### Step 3: Verify in Database
```bash
psql -h localhost -p 5433 -U mosaico -d mosaico -c "SELECT id, name, created_at FROM projects;"
```

---

## 🐛 Known Issues (Expected)

1. **"Customer table not available"** warnings in logs
   - These are harmless - we disabled billing features
   - The app gracefully handles this

2. **"STRIPE_SECRET_KEY is not set"** warnings
   - Also harmless - Stripe is optional
   - Billing features are disabled

---

## 📊 What We've Built So Far

✅ **Phase 1 Complete:**
- Projects list dashboard
- Create/Delete projects
- Server actions for API communication
- Clerk authentication
- Clean UI with shadcn/ui components

✅ **Phase 2 Progress:**
- Project editor page (in progress)
- Email structure builder (V2 drag & drop)
- Image upload manager (GCS integration)
- AI content generation UI
- Translation UI

⏳ **Coming Soon:**
- Google Sheets export

---

## 🎉 Quick Demo Commands

```bash
# 1. Start Backend & DB (Root)
cd /Users/gvannucchi/Projects/mosaico
docker compose up -d

# 2. Start Frontend (Frontend dir)
cd frontend
npm run dev

# 3. View logs
docker logs -f mosaico_backend_local
```

---

**Last Updated:** November 19, 2025
**Status:** Phase 2 Active Development 🚀
