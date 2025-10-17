# Changelog

All notable changes to the Mosaico project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Google Sheets export functionality
- Project templates
- User roles & permissions
- Approval workflow
- Activity audit log

---

## [0.2.6] - 2025-10-17

### ✨ Added
- **UI Improvement**: Unified Generate/Regenerate button for cleaner interface
  - Shows "Generate Email Content" before first generation
  - Changes to "Regenerate All Content" after content exists
  - Single full-width button instead of two separate buttons
  - Reduces UI clutter and improves user experience

### 🔧 Improvements
- **Translation Performance**: Switched to `gemini-2.5-flash` for translations
  - ⚡ **6-7x faster** translations (~9 seconds vs 60+ seconds for 10 translations)
  - 🚀 **Higher rate limits** (60 req/min vs 5 req/min)
  - 💰 **Lower cost** (90% cheaper than gemini-2.5-pro)
  - ✅ **Better reliability** - no more 429 rate limit errors
  - ✅ **Fewer JSON parsing errors** - more stable output format
- Added `use_flash` parameter to `VertexAIClient.generate_content()` for flexible model selection
- Translation quality remains excellent with Flash model

### 🐛 Fixed
- Translation failures with "429 Resource exhausted" errors
- "Unterminated string" JSON parsing errors in batch translations
- Rate limiting issues when translating to multiple languages

### 📊 Performance Metrics
**Before (gemini-2.5-pro):**
- 6 components × 2 languages = ~60-90 seconds
- Frequent rate limit errors (429)
- JSON parsing failures requiring retries

**After (gemini-2.5-flash):**
- 6 components × 2 languages = ~8-12 seconds ⚡
- No rate limit errors
- Clean JSON responses

---

## [0.2.5] - 2025-10-17

### ✨ Added
- **Project Duplication**: Complete project cloning functionality
  - New "Duplicate" option in project card dropdown menu
  - Duplicates all project settings (brief, structure, tone, languages)
  - Copies all generated components with their content
  - Copies all translations for all languages
  - References same images in GCS (no file duplication)
  - Adds "(Copy)" suffix to duplicated project name
  - Activity log tracks duplication for audit trail
  - New backend endpoint `POST /api/v1/projects/{id}/duplicate`

### 🔧 Improvements
- Enhanced project card dropdown menu with separator
- Better workflow for creating campaign variations
- Instant project cloning without regenerating content

### 🐛 Fixed
- Fixed `user_id` NOT NULL constraint error when duplicating images
- Proper user attribution for duplicated project resources

---

## [0.2.4] - 2025-10-17

### ✨ Added
- **Client-Side Image Compression**: Automatic image compression before upload
  - Accepts files up to 10MB original size
  - Compresses to max 2MB using `browser-image-compression`
  - Max dimension 1920px for email-optimized images
  - JPEG format with 0.8 quality balance
  - Real-time feedback during compression process
  - Toast notifications showing original → compressed size

### 🔧 Improvements
- Better upload performance with smaller file sizes
- Reduced storage costs with automatic compression
- Improved state management in image upload component
- Fixed image preview display after upload
- Enhanced user feedback with compression progress

### 🐛 Fixed
- Image preview not showing after upload (state tracking issue)
- Missing drag & drop handler functions

---

## [0.2.3] - 2025-10-17

### ✨ Added
- **Handlebar Export Without Translations**: "Copy Handlebar" button now visible immediately after content generation
  - No need to translate first for English-only campaigns
  - Exports English-only handlebar if no translations exist
  - Exports multi-language handlebar when translations are present
  - Toast message shows language count for clarity

### 🔧 Improvements
- Better UX for single-language campaigns
- Clearer feedback with language count in success message

---

## [0.2.2] - 2025-10-17

### ✨ Added
- **Persistent Component Storage**: Generated content now automatically saves to database
  - Auto-save after AI generation
  - Auto-save after translation
  - Auto-save on inline edits
  - Content persists across page refreshes and sessions
- **Visual Feedback**: "Saving..." indicator shows when content is being saved
- **Automatic Loading**: Saved components load automatically when opening a project
- **Backend API**: New `/api/v1/projects/{id}/components` endpoint for batch component saving
- **Database Integration**: Full integration with Components and Translations tables

### 🔧 Improvements
- Project settings (brief, tone, structure) still use manual "Save" button for user control
- Generated components use Google Docs-style auto-save for zero data loss
- Improved data flow between frontend and backend with proper TypeScript types

---

## [0.2.1] - 2025-10-17

### 🐛 Fixed
- **UI Responsiveness**: Fixed dashboard becoming unresponsive after deleting projects
  - Added hard page refresh after delete to ensure UI updates correctly
  - Prevents buttons and links from becoming unclickable
- **TypeScript Compilation**: Fixed type errors preventing frontend build
  - Fixed type assertions in `project-editor.tsx`
  - Fixed onChange callbacks in `image-upload-manager.tsx`
  - Added null checks in Stripe webhook handler
- **Next.js Cache**: Resolved corrupted build manifest errors in development

---

## [0.2.0] - 2025-10-17

### Breaking Changes
- **Removed Google Sheets Add-on approach**: Pivoted to standalone web platform
- Deleted entire `addon/` directory
- Complete architecture change: Google Apps Script → Next.js + FastAPI

### ✨ Added - New Features
- **Frontend Platform**: Complete Next.js 15 web application
  - Modern dashboard with project management
  - Real-time project editor with live updates
  - Email structure builder with dynamic components
  - Image upload manager with drag & drop
  - AI content generation UI with temperature control
  - Batch translation interface
  
- **Notification System** (Dual approach)
  - In-app notification center with bell icon and badge counter
  - Persistent notification inbox with read/unread status
  - Toast notifications for immediate feedback
  - Slack webhooks for team-wide visibility
  
- **Content Generation Features**
  - Temperature control slider (0.0-1.0) for AI creativity
  - Regenerate all content functionality
  - Regenerate individual components with context preservation
  - Default to 1 variation instead of 3
  - Prompt Assistant for brief optimization
  - Image-context aware generation
  
- **Translation System**
  - Batch parallel translation to multiple languages
  - Context-aware translation with retry logic
  - Rate limiting to prevent quota exhaustion
  
- **Export Features**
  - Per-component handlebar template generation
  - Multi-language handlebar with English fallback
  - Copy to clipboard functionality
  
- **Database & Backend**
  - PostgreSQL database with full schema
  - SQLAlchemy ORM with Alembic migrations
  - Project CRUD endpoints
  - Activity logging for audit trails
  - Clerk authentication integration
  - Google Cloud Storage for image uploads

### 🐛 Fixed
- Hydration errors in sidebar navigation (localStorage handling)
- Backend 500 errors in prompt optimization endpoint
- Backend 500 errors in generate endpoint (parameter ordering)
- Backend 500 errors in translate endpoint (async handling)
- Translation rate limiting issues (increased to 30 req/s for dev)
- UI not updating after project creation/deletion (added revalidatePath)
- Missing user email attribute in notifications (graceful fallback)
- GCS bucket configuration issues
- Notification context provider scope issues
- CTA regeneration producing identical output (enhanced prompts with context)

### 🔧 Improvements
- Enhanced translation performance with parallel processing (+40% faster)
- Improved AI regeneration prompts with full email context
- Better error handling across all API endpoints
- Graceful degradation when optional services unavailable
- Comprehensive logging for debugging

### 📝 Documentation
- Complete rewrite of main README.md
- Added CHANGELOG.md for version tracking
- Added TEAM_WORKFLOW_NOTIFICATIONS.md
- Added REFINEMENTS_COMPLETE.md
- Archived outdated addon documentation
- Updated all setup and deployment guides

### 🏗️ Technical Stack (New)
- **Frontend**: Next.js 15.1, React, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Python 3.11, FastAPI 0.115, SQLAlchemy, Alembic
- **Database**: PostgreSQL 14+
- **AI**: Google Vertex AI (Gemini 2.5 Pro/Flash)
- **Storage**: Google Cloud Storage
- **Auth**: Clerk
- **Monitoring**: Cloud Logging, Slack Webhooks

---

## [0.1.0] - 2024-10-07 (Deprecated)

### Initial Release (Google Sheets Add-on Approach)
- Google Workspace Add-on with Apps Script
- Generate variations endpoint
- Translate endpoint
- Refine endpoint
- Multimodal image-to-text generation
- Basic prompt engineering with Vertex AI

**Note**: This approach was deprecated in favor of the standalone web platform (v0.2.0+)

---

## Version History

- **v0.2.0** (Current): Full web platform with Next.js + FastAPI
- **v0.1.0** (Deprecated): Google Sheets Add-on approach

---

## Versioning Strategy

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (x.0.0): Breaking changes, incompatible API changes
- **MINOR** (0.x.0): New features, backward-compatible
- **PATCH** (0.0.x): Bug fixes, backward-compatible

**Pre-1.0 Status**: During v0.x.x development, the API and architecture may change significantly. v1.0.0 will mark the first production-ready stable release.

