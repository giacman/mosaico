# 🚀 Mosaico Quick Start Guide

## ✅ Current Status

**Backend:** Running on http://localhost:8080  
**Frontend:** Running on http://localhost:3000  
**Database:** PostgreSQL ready  
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
4. You'll be redirected to the project editor (404 expected - we'll build it next!)

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
```bash
cd /Users/gvannucchi/Projects/mosaico/backend
source .venv-mosaico/bin/activate
python -m app.main
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8080
```

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
```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# If not running:
brew services start postgresql@15

# Test connection
psql mosaico -c "SELECT COUNT(*) FROM projects;"
```

### Authentication Not Working?
- Make sure `frontend/.env.local` has valid Clerk keys
- Keys should start with:
  - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...`
  - `CLERK_SECRET_KEY=sk_test_...`

---

## 📋 Test the Full Flow

### Step 1: Create a Test Project via API
```bash
# Get your Clerk JWT token from browser DevTools
# (Application > Local Storage > clerk-db-jwt)

curl -X POST http://localhost:8080/api/v1/projects \
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
psql mosaico -c "SELECT id, name, created_at FROM projects;"
```

---

## 🐛 Known Issues (Expected)

1. **Project Editor Page (404)** - We haven't built it yet!
   - When you click "Edit" on a project, you'll get a 404
   - This is expected - it's the next thing to build

2. **"Customer table not available"** warnings in logs
   - These are harmless - we disabled billing features
   - The app gracefully handles this

3. **"STRIPE_SECRET_KEY is not set"** warnings
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

⏳ **Phase 2 Next:**
- Project editor page
- Email structure builder
- Image upload manager
- AI content generation UI
- Translation UI
- Google Sheets export

---

## 🎉 Quick Demo Commands

```bash
# Start everything
cd /Users/gvannucchi/Projects/mosaico

# Terminal 1: Backend
cd backend && source .venv-mosaico/bin/activate && python -m app.main

# Terminal 2: Frontend  
cd frontend && npm run dev

# Terminal 3: Database queries
psql mosaico
```

---

## 💡 Next Steps

**Ready to continue building?** Say:
- "Build the project editor" - I'll create the main editing interface
- "Show me what to test" - I'll guide you through testing
- "Something's broken" - Tell me what and I'll fix it!

---

**Last Updated:** December 16, 2025  
**Status:** Phase 1 Complete ✅ | Phase 2 Ready to Build 🚀


