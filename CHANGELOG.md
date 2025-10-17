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

