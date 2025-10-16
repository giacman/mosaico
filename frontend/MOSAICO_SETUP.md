# Mosaico Frontend Setup

## Quick Start

This frontend connects to the Mosaico backend API for AI-powered email campaign creation.

### 1. Create `.env.local` File

Create `frontend/.env.local` with the following:

```bash
# Mosaico Backend API
NEXT_PUBLIC_API_URL=http://localhost:8080

# Database (optional - using backend's PostgreSQL)
DATABASE_URL=postgresql://localhost:5432/mosaico

# Clerk Auth (REQUIRED - create a Clerk app first)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/login
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/signup

# Stripe (OPTIONAL for MVP - can leave blank)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PAYMENT_LINK_YEARLY=
NEXT_PUBLIC_STRIPE_PAYMENT_LINK_MONTHLY=
```

### 2. Setup Clerk (Required for Auth)

1. Go to https://clerk.com/ and create a free account
2. Create a new application named "Mosaico"
3. In the Clerk dashboard:
   - Go to "API Keys"
   - Copy "Publishable key" → `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
   - Copy "Secret key" → `CLERK_SECRET_KEY`
4. Paste these values into your `.env.local`

### 3. Start Development Server

```bash
cd frontend
npm run dev
```

The frontend will run on `http://localhost:3000`

### 4. Verify Backend Connection

Make sure your backend is running on `http://localhost:8080`:
```bash
# In another terminal
cd backend
source .venv-mosaico/bin/activate
python -m app.main
```

---

## Architecture

**Frontend Stack:**
- Next.js 15 (App Router)
- React 19
- Tailwind CSS 4
- Shadcn UI components
- Clerk Authentication
- Framer Motion animations

**Backend API:**
- FastAPI (Python)
- PostgreSQL database
- Vertex AI (Gemini)
- Google Cloud Storage

---

## Project Structure

```
frontend/
├── app/
│   ├── (authenticated)/
│   │   └── dashboard/          # Protected routes
│   │       ├── page.tsx        # Projects list (TO BE BUILT)
│   │       └── projects/
│   │           └── [id]/
│   │               └── page.tsx # Project editor (TO BE BUILT)
│   └── (unauthenticated)/
│       └── (marketing)/        # Landing pages (keep as-is)
├── actions/                     # Server actions for API calls (TO BE BUILT)
├── components/
│   ├── ui/                     # Shadcn components (reuse)
│   └── mosaico/                # Custom Mosaico components (TO BE BUILT)
│       ├── email-structure-builder.tsx
│       ├── image-upload-manager.tsx
│       ├── brief-editor.tsx
│       └── generation-preview.tsx
└── lib/
    └── api.ts                  # API client (TO BE BUILT)
```

---

## What's Next

### Phase 1: Core Setup ✓
- [x] Clone template
- [x] Install dependencies
- [ ] Create `.env.local` with Clerk keys
- [ ] Test authentication flow

### Phase 2: Projects List Page
- [ ] Create projects list UI
- [ ] Connect to `/api/v1/projects` endpoint
- [ ] Add create/edit/delete actions

### Phase 3: Project Editor
- [ ] Build email structure builder
- [ ] Build image upload manager
- [ ] Build brief editor
- [ ] Build generation preview

### Phase 4: API Integration
- [ ] Create server actions for all backend endpoints
- [ ] Handle authentication tokens
- [ ] Error handling & loading states

---

## Key Features to Build

### 1. Projects List (`/dashboard`)
- Card grid showing all projects
- Create new project button
- Edit/Delete actions
- Search and filter

### 2. Project Editor (`/dashboard/projects/[id]`)
- **Structure Builder**: Select components (Subject, Pre-header, Body×N, CTA×N)
- **Image Manager**: Upload multiple images, assign to components
- **Brief Editor**: Write creative prompt, select tone & languages
- **Generation Preview**: View generated content with inline editing
- **Actions**: Generate, Translate, Export to Google Sheets

### 3. Collaboration Features
- Activity log showing who did what
- Real-time updates (polling every 10s)
- "Last edited by..." indicators

---

## Development Tips

### Using Shadcn Components

The template includes many pre-built components:
```tsx
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
```

### API Calls with Server Actions

```typescript
// actions/projects.ts
"use server"

export async function getProjects() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/projects`)
  return res.json()
}
```

### Authentication

Clerk is already set up in the template:
```tsx
import { auth } from "@clerk/nextjs/server"

export default async function Page() {
  const { userId } = await auth()
  // userId available for API calls
}
```

---

## Troubleshooting

### "Clerk keys not found"
- Make sure you created `.env.local` with valid Clerk keys
- Restart the dev server after adding keys

### "Cannot connect to backend"
- Check backend is running on port 8080
- Verify `NEXT_PUBLIC_API_URL=http://localhost:8080` in `.env.local`

### "Port 3000 already in use"
- Kill the process: `lsof -ti:3000 | xargs kill -9`
- Or use a different port: `npm run dev -- -p 3001`

---

## Comparison: Template vs. Mosaico

### Keep (From Template)
- ✅ Authentication flow (Clerk)
- ✅ Dashboard layout & sidebar
- ✅ UI components (buttons, inputs, etc.)
- ✅ Marketing pages (landing, about, pricing)

### Replace/Remove
- ❌ Stripe integration (not needed for MVP)
- ❌ Billing page (not needed)
- ❌ Example customer data
- ❌ Supabase (using our PostgreSQL backend instead)

### Build New
- 🆕 Projects list page
- 🆕 Project editor with all Mosaico components
- 🆕 API integration with FastAPI backend
- 🆕 Real-time collaboration UI

---

**Ready to code?** Start by creating your Clerk app and adding the keys to `.env.local`!

