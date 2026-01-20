# Changelog

All notable changes to the Mosaico project will be documented in this file.

## [1.1.4] - 2026-01-20

### Added
- **Flag images from flagcdn.com**: Replaced emoji flags with proper flag images from flagcdn.com CDN for cross-platform compatibility (fixes Windows Chrome flag display)
- **Retranslate feature**: When viewing translated content, "Regenerate" button becomes "Retranslate" to re-translate from English source

### Changed
- **Shared language configuration**: Languages now defined in `frontend/lib/languages.ts` to avoid duplication
- **Flag rendering**: Uses `<Image>` component with flagcdn.com URLs instead of emoji text
- **Project cards**: Language flags on newsletter/push list pages now use proper flag images

### Technical
- Created `frontend/lib/languages.ts` with `LANGUAGES` array, `getFlagUrl()`, and `getFlagUrlForLanguage()` helper functions
- Updated `email-structure.tsx`, `project-editor.tsx`, and `project-card.tsx` to use shared language config
- Updated `section-builder.tsx` with Retranslate logic that calls existing `/translate` endpoint
- Uses flagcdn.com CDN for flag images (no local assets needed)

---

## [1.1.3] - 2026-01-20

### Added
- **App version in sidebar**: Version number now displayed in bottom-left of sidebar footer
- **Slack dev channel separation**: Development notifications now go to separate `mosaico-test-notifications` channel when `SLACK_WEBHOOK_URL_DEV` is configured
- **Korean language support**: Added Korean (KO) as a target translation language

### Changed
- **Streamlined language list**: Reduced available languages to core markets: IT, FR, ES, DE, ZH, KO, JA (removed PT, RU, AR, NL)

### Technical
- `SLACK_WEBHOOK_URL_DEV` environment variable for dev-only Slack notifications
- Version imported from `package.json` and displayed dynamically in sidebar

---

## [1.1.2] - 2026-01-16

### Added
- **Enhanced Slack Notifications**: Notifications now include comprehensive project context
  - Project name displayed in all notifications (no more "Unknown" projects)
  - User email included to identify who performed the action
  - Clickable "View Project" button that opens the project directly in the app
  - Project URL automatically built from `FRONTEND_URL` configuration

### Changed
- **Notification functions**: All notification functions now require `project_id` parameter for proper context
- **Batch translate endpoint**: Now accepts optional `project_id` and `user_email` to send contextual notifications
- **Frontend translation calls**: Updated to pass `projectId` when calling batch translate API

### Technical
- Added `frontend_url` configuration setting (defaults to `http://localhost:3000` for local dev)
- `send_slack_notification()` now accepts `project_id` and builds project URLs
- `notify_project_created()`, `notify_generation_completed()`, `notify_translation_completed()`, and `notify_content_ready_for_approval()` all require `project_id`
- `BatchTranslateRequest` model extended with optional `project_id` and `user_email` fields
- Frontend `batchTranslate()` function now accepts optional `projectId` parameter

---

## [1.1.1] - 2026-01-16

### Fixed
- **Critical: Duplicate content for multiple components**: Fixed bug where multiple instances of the same component type (e.g., `body_1` and `body_2`, `cta_1` and `cta_2`) would all display the same content in the UI
  - Root cause: `findComponentForSection()` in `section-utils.ts` was ignoring the `component_index` parameter
  - Root cause: `renderPreview()` in `section-builder.tsx` was not passing `displayIndex` to the lookup function
  - Backend was generating unique content correctly, but frontend was always displaying the first instance

### Changed
- **Simplified Prompt Optimization**: Removed redundant `tone`, `structure`, and `content_type` parameters from the Optimize Prompt feature
  - These were remnants of the original application and didn't add value given the project already defines its structure
  - Cleaner, simpler prompt assistant dialog without confusing badge indicators
- **Prompt Optimization robustness**: Added regex-based fallback for malformed JSON responses from AI, preventing errors when responses are truncated
- **Increased token limit**: Raised `max_output_tokens` from 1500 to 2048 for prompt optimization to prevent truncation

### Technical
- `findComponentForSection()` now correctly uses `component_index` for multi-instance lookups
- `renderPreview()` passes `displayIndex` to component lookup
- `OptimizePromptRequest` simplified to only require `text` parameter
- Added fallback JSON extraction in `optimize_prompt.py` using regex patterns

---

## [1.1.0] - 2026-01-08 🚀

### New Feature: Push Notifications

This release introduces a new content type: **Push Notifications**! Create concise, impactful push notification content directly from the Mosaico platform.

### Added
- **Push Notification content type**: New project type with Title (max 20 chars), Body (max 100 chars), and optional CTA (max 30 chars)
- **Push Notifications page**: Dedicated `/push` route for managing push notification projects
- **Newsletter-to-Push transformation**: Convert any newsletter section into a push notification with one click
  - "Push" button 🔔 on each newsletter section
  - Automatically generates content based on section brief (respecting character limits)
  - Automatically carries over brief and context from the source section
- **Database migration**: New `content_type` column to support multiple content types
- **Modern iPhone mockup UI**: Push notification editor displays content in a realistic mobile phone frame
- **Slack notifications**: Automatic notifications when creating push from newsletter and when content is generated
- **Clickable sidebar icons**: Section icons (📁 Newsletter, 🔔 Push) now link directly to list pages

### Fixed
- **Sidebar duplicate key error**: Fixed React warning for projects with identical names
- **Back button navigation**: Creating push from newsletter no longer adds intermediate page to history
- **Empty sidebar sections**: "Approved" sections now hidden when empty instead of showing non-clickable element

### Changed
- **AI Model upgrade**: Updated Optimize Prompt feature from deprecated `gemini-2.0-flash-001` to `gemini-2.5-flash` (old model shutting down Feb 2026)

### Technical
- `ContentType` enum extended with `push_notification`
- `/api/v1/projects/{id}/sections/{key}/to-push` endpoint with auto-generation
- `createPushFromSection` frontend action
- Push-specific prompt guidelines with strict character limits
- Projects list API now supports `content_type` filter parameter
- `notify_project_created` now supports `content_type` parameter for notification labels

---

## [1.0.1] - 2026-01-05

### Fixed
- **Optimize Prompt button layout**: Replaced CSS grid with flexbox for better responsiveness on smaller screens (MacBook 13")
- **Jest test runner**: Added missing `@jest/test-sequencer` dependency

### Changed
- **Home Page card renamed**: "Home Page" tile renamed to "On-Site Banners" for clarity

### Added
- **Visual context for image prompts**: AI now receives explicit instructions to analyze and reference uploaded images when generating content, improving the relevance of generated copy to visual context

---

## [1.0.0] - 2025-12-29 🎉

### First Official Release

Mosaico is now production-ready! This release marks the first stable version of the AI-powered multilingual content studio.

### Added
- **Activity Log on Homepage**: Real-time audit trail showing all team actions across projects
  - Persistent history with "Load more" pagination
  - Toggle between relative and full date display
  - Direct links to projects from activity entries
  - Global endpoint `/api/v1/activity` with offset/limit support
- **Label Deletion**: Labels can now be deleted with confirmation dialog
  - Hover on any label to reveal delete button
  - Available in both Create Project dialog and Project Editor
  - Warning about label removal from all projects

### Technical
- `GlobalActivityLog` component with pagination and type-safe imports
- Backend `get_global_activity_log` service with project name JOIN
- AlertDialog for delete confirmations

---

## [0.9.5] - 2025-12-29

### Added
- **Test infrastructure**: Jest unit tests (22 tests for section-utils) and Playwright E2E tests (9 tests for multi-section)
- **Pre-commit hooks**: Husky-based hooks run unit tests before each commit
- **Environment-based Slack channels**: Separate webhook URLs for dev vs production notifications
- **Content ready for approval notification**: New Slack notification type for approval-ready content

### Fixed
- **AI inventing products**: Added strict rules to prevent AI from fabricating product names like "[Oversized Distressed Knitwear]"
- **Placeholder brackets**: AI now writes complete, polished text without [brackets] or [placeholder] markers
- **Image URL normalization**: Centralized `normalizeImage()` utility for consistent URL handling

### Changed
- **Removed "Project Updated" notifications**: Reduced Slack noise by only sending notifications for significant events (create, generate, translate, approve)
- **Prompt optimization**: Updated prompt optimizer to explicitly forbid placeholders and invented details
- **Code cleanup**: Removed unused utility functions and simplified component lookup logic

### Technical Improvements
- `normalizeImage()` function in `section-utils.ts` centralizes image URL normalization
- Simplified `findComponentForSection()` with single-pass lookup
- Jest configuration with jsdom environment and CSS module mocking
- Playwright configuration for cross-browser E2E testing

## [0.9.4] - 2025-12-29

### Added
- **Multi-section briefs**: Each section can now have its own brief for more targeted content generation
- **Section-aware content generation**: AI generates content specific to each section's brief and context
- **Dark mode**: Full dark mode support across the application
- **Autosave**: Automatic saving of project changes
- **Image upload guard**: Alert prompts user to upload images before generation
- **Copy button feedback**: Toast notifications when copying component content

### Fixed
- **Subject/Pre-header not saving**: Fixed header generation loop that prevented Subject and Pre-header from being saved correctly
- **Translation truncation**: Increased max_tokens from 2048 to 4096 to prevent long translations from being cut off
- **CTA cross-contamination**: Added section_key to translation keys to prevent CTAs from different sections overwriting each other
- **"Regenerate" button label**: Now shows "Generate" when no content exists, "Regenerate" only after content is generated
- **Missing image alert false positive**: Fixed image check logic to use `image_id` on Component instead of non-existent `section_key` on Image

### Changed
- **Removed translations from Approved state**: Translations no longer required for project approval
- **Component persistence**: Clean slate approach for text components (delete+create), UPSERT for image components (preserve uploads)
- **Consistent indexing**: Standardized component_index=1 for all component types within sections
- **UI improvements**: Various interface refinements


## [0.9.3] - 2025-12-09

### Added
- **Sequential Validation Chain**: Implemented automatic translation quality validation with smart retry
  - AI-powered validation agent evaluates translation quality (naturalness, cultural adaptation, tone, accuracy)
  - Confidence scoring system (0.0-1.0 scale)
  - Automatic retry with feedback if confidence < 0.7
  - Detailed validation logging (confidence, naturalness, issues count)
  - Graceful fallback if validation service fails
  - Adds ~25s latency but significantly improves translation quality

### Changed
- **Translation Endpoints**: All translation endpoints now use Sequential Validation by default
  - `/api/v1/translate` endpoint updated to use validation chain
  - `/api/v1/translate/batch` endpoint updated to use validation chain
  - `translate_text_content()` refactored with validation support
  - `use_validation` parameter (default: True) to enable/disable

### Technical Improvements
- New `ValidationResult` model with detailed quality metrics
- `validate_translation()` function with comprehensive evaluation criteria
- `translate_with_retry()` function supports validation feedback
- Validation uses Gemini 2.5 Pro with temperature 0.3 for consistent evaluation
- Four evaluation dimensions: naturalness (40%), cultural adaptation (30%), tone (20%), accuracy (10%)

### Impact
- Expected translation quality improvement: +15-20% with validation
- Combined with v0.9.2 prompt improvements: Total +35-45% quality increase
- Self-healing translations reduce manual corrections needed

## [0.9.2] - 2025-12-03

### Changed
- **Enhanced Translation Prompt Engineering**: Major refactor of translation prompt based on best practices from Anthropic (Claude) and Google (Gemini)
  - Restructured prompt with clear sections (TASK, APPROACH, RULES, INPUT, OUTPUT)
  - Added internal reasoning guidance to encourage better decision-making
  - Integrated explicit DO/DON'T lists for better instruction clarity
  - Expanded language-specific guidance with concrete examples for DE, FR, ES, PT, IT
  - Implemented "Cultural Translator" pattern focusing on intent and emotional impact
  - Temperature increased from 0.3 to 0.5 for more creative, natural transcreation
- **Model Upgrade for Translations**: Switched from Gemini 2.5 Flash to Gemini 2.5 Pro for all translations
  - Pro model provides better cultural nuance understanding
  - Improved handling of metaphors and idiomatic expressions
  - Better transcreation quality (creative adaptation vs literal translation)
  - Cost not a concern for internal application

### Added
- **Translation Quality Documentation**: New comprehensive documentation on translation approaches
  - `docs/TRANSLATION_QUALITY_APPROACHES.md`: Analysis of 4 optimization levels (Prompt Engineering, Sequential Validation, RAG, DSPy)
  - `docs/PROMPT_IMPROVEMENTS.md`: Detailed changelog of prompt engineering improvements with examples
  - Recommendation: Target RAG + Sequential Validation for 90-95% quality (sweet spot)

### Technical Improvements
- Language-specific guidelines now include concrete examples (e.g., "Genießen Sie" ✓ vs "Schmecken Sie" ✗)
- Enhanced German guidance: verb selection, compound words, formality (Sie form)
- Enhanced French guidance: style, anglicisms, formality (vous/tu), word order
- Enhanced Spanish guidance: tone, regional variations (ES vs LATAM), inclusivity
- Enhanced Portuguese guidance: variants (BR vs PT), formality, gerund usage
- Enhanced Italian guidance: emotional style, cultural metaphors, enthusiasm
- Prompt structure follows industry best practices for better LLM comprehension

### Impact
- Expected translation quality improvement: +10-15% more natural-sounding output
- Reduced literal translations through explicit reasoning steps
- Better cultural adaptation through concrete examples

## [0.9.1] - 2025-11-22

### Added
- **Language Flag Emojis**: Added flag emojis (🇮🇹🇩🇪🇫🇷🇪🇸) throughout the UI for better visual language identification
- **Translation Status Indicators**: Real-time feedback with spinner during translation and checkmark icon when translation is complete
- **Language Flags on Project Cards**: Dashboard now displays language flags at the bottom of each project card showing which languages are available
- **Translation State Tracking**: New state management to track which languages have been successfully translated

### Changed
- **Redesigned Project Editor UI**: Reorganized into three clear sections:
  - Top section: Project Details (name and labels)
  - Left column: Content Generation (creative brief, tone of voice, creativity level)
  - Right column: Translation & Languages (language selection and translation controls)
- **Improved Creativity Level Control**: Slider now wider (60% width) and placed side-by-side with Tone of Voice, with visual labels (Conservative/Balanced/Creative)
- **Default Temperature**: Changed from 0.7 to 0.5 for more balanced content generation
- **Cleaned Header**: Removed redundant disabled "Generate Content" button from project editor header
- **Button Labels**: Changed "Generate Email Content" to "Generate Content" for brevity

### Fixed
- **Critical: Translation Preservation Bug**: Fixed issue where regenerating a single component would break all existing translations
  - Backend returns translations in array format, now properly converted to object format
  - Component regeneration now correctly checks for existing translations before attempting retranslation
  - Translations are properly merged instead of being lost during component updates
- **Incomplete Save Logic**: Fixed RenderedComponent save button that had placeholder comment instead of actual implementation
- **Redundant State Initialization**: Removed duplicate localStorage loading in NotificationsProvider (was loading in both useState initializer and useEffect)
- **Translation Type Inconsistency**: Fixed new components being created with `translations: []` instead of `translations: {}`
- **Images Disappearing on Content Generation**: Fixed bug where regenerating all content would remove existing image components

### Technical Improvements
- Added comprehensive translation state management with `translatedLanguages` Set
- Improved `onUpdateComponents` callback to properly normalize backend translation format
- Enhanced regeneration logic in `section-builder.tsx` to detect and preserve existing translations
- Better separation of concerns between content generation and translation workflows

## [0.9.0] - 2025-11-09

### Changed
- **Deployment Process**: Removed the automated database migration (Alembic) step from the CI/CD workflow for increased deployment stability. Migrations must now be run manually in the production environment.

### Added
- **Local Docker Development Environment**: Added `docker-compose.yml` and associated configuration to run the entire backend stack (PostgreSQL and Python backend) locally in Docker containers. This provides a consistent and isolated development environment that mirrors production more closely.
- **Automated Database Migrations on Startup**: The Docker environment now automatically runs `alembic upgrade head` on startup via a `docker-entrypoint.sh` script, ensuring the local database schema is always up-to-date.
- **Google Cloud Credentials for Local Docker**: Configured `docker-compose.yml` to securely mount local Google Cloud credentials, enabling services like Vertex AI and Google Cloud Storage to work correctly in the local Docker environment.
- **Dedicated Development GCS Bucket**: The local environment is now configured to use a separate `mosaico-images-dev-474415` bucket, safely isolating development image uploads from production data.

### Fixed
- **Clerk Authentication in Production**: Resolved a critical authentication bug in production by updating the Clerk SDK usage from the deprecated `verify_token` to the correct `authenticate_request` method, fixing `401 Unauthorized` errors.
- **Frontend Build Errors**: Fixed multiple frontend compilation errors caused by inconsistent function naming and incorrect imports during refactoring (e.g., `generateContent` vs `generate`, `translateBatch` vs `batchTranslate`).
- **Frontend API Endpoint Configuration**: Standardized all frontend API calls to use a single environment variable (`NEXT_PUBLIC_API_URL`), fixing `ECONNREFUSED` errors by ensuring the frontend correctly points to the backend.
- **GCS Image Upload ACL Issue**: Fixed a `500 Internal Server Error` on image uploads by removing legacy ACL code (`blob.make_public()`) and configuring the development GCS bucket for modern, uniform bucket-level access.
- **React Hydration Error**: Resolved a frontend hydration error by ensuring the `NotificationCenter` component only renders on the client side.

## [0.8.1.1] - 2025-11-08

### Backend
- Removed project name uniqueness check from `ProjectService.create_project`, allowing projects to have duplicate names (uniqueness now enforced by project ID only).
- Removed `Base.metadata.create_all()` call from `app/main.py` to ensure Alembic is the sole manager of database schema.

### CI/CD
- Updated `.github/workflows/cloud-run-backend.yml` to automatically run Alembic migrations (`alembic upgrade head`) as part of the Cloud Run backend deployment.
- Added steps to set up Python environment, install backend dependencies, install Cloud SQL Proxy, and execute migrations.

### Configuration
- Requires new GitHub repository secrets for CI/CD pipeline: `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `CLOUD_SQL_INSTANCE_NAME`, `CLERK_SECRET_KEY`, `VERTEX_AI_MODEL`, `VERTEX_AI_MODEL_FLASH`, `GCS_BUCKET_PROMPTS`, `GCS_BUCKET_EXAMPLES`, `GCS_BUCKET_IMAGES`.

## [0.8.1] - 2025-11-08

### Backend
- Fix ResponseValidationError in production when listing projects by relaxing `ComponentResponse` schema:
  - `section_key` now optional (defaults to null)
  - `section_order` now optional (defaults to 0)
- Compatible with legacy component rows created before sections were tracked.

### Notes
- Recommended follow-up: backfill existing component rows to set `section_key='main'` and `section_order=0` for consistency.

## [0.8.0] - 2025-11-06

### Frontend
- Unified "Email Structure" experience: merged the previous Input/Output into a single dynamic section with WYSIWYG-like preview and placeholders for new projects.
- Restored and enhanced features: project labels, Optimize Prompt, drag-and-drop for sections/components, and inline image uploads in sections.
- CTA normalization: CTAs are now always UPPERCASE across generation, manual edits, translations, and rendering.
- Translations UX: tabbed language previews; "View Language" selector shows only one language at a time for a compact page.
- Email-like styling: centered container (max-width 840px), white background, soft shadow/ring; solid primary CTA buttons; linkified URLs in content.
- Fixed duplicate Body mapping and ensured correct indexing for multiple Body/CTA instances.
- Clear loading states for generation and translation.
- Auto-translate on single-component regenerate restored (and CTA translations uppercased); English content no longer reverts post-save.
- Handlebar export: always base on English + include only selected target_languages; robust request normalization.
- Image upload: drag-and-drop enabled on empty slot.
- Notification bell: persisted via localStorage; survives navigation after actions.

### Backend
- No functional API changes.
- Local dev: added `psycopg2-binary` to requirements to support default `postgresql://` URLs on some environments.

### Fixed
- Optimize Prompt: convert section-based structure to legacy `component/count` format (prevents 422/500).
- Generate: map section-based structure to legacy format before calling backend.
- Import path corrections after refactor (`RenderedComponent`).
- Vertex AI auth confusion: clarified ADC vs Service Account usage and required env vars (prevents 503 invalid_grant due to wrong project/credentials).
 - Handlebar 422 and wrong structure: backend now accepts array/dict shapes and normalizes to { lang: text }.
 - Components save 500: translations normalized to strings before save; filtered to target languages.

### Documentation
- README: consolidated local setup with explicit venv usage, PostgreSQL creation, Alembic migrations, and absolute-path commands.
- Added clear GCP credentials guide (ADC vs Service Account) with required IAM roles and common pitfalls.

## [0.7.1] - 2025-10-23

### Frontend
- Add “Request access” form on unauthenticated homepage (sends to Slack via `SLACK_WEBHOOK_URL`).
- Protect `/home` in middleware and reuse dashboard layout so user menu appears on `/home`.

### Backend
- No changes.

---
### Planned
- Google Sheets export functionality
- Airship integration
- Jira integration
- Activity audit log


## [0.7.0] - 2025-10-23

### Frontend - Multi-content hub (phase 1)
- Added authenticated home `/home` with tiles (Newsletter live; others with pastel orange "Coming soon").
- Moved dashboard to `/newsletter`; fixed tabs and links.
- Newsletter: top-left logo now links back to `/home`.
- Unauthenticated: minimal homepage with centered Sign up / Log in; removed template header/banner/footer.
- Login/Signup: simplified to centered Clerk components; redirect to `/home`.
- Middleware: explicit protected routes.

### Backend
- No changes.

---

## [0.6.0] - 2025-10-23

### 🚀 Backend deployed to Google Cloud Run
- Built and deployed FastAPI backend to Cloud Run (region `europe-west1`).
- Connected to Cloud SQL (PostgreSQL 16) via Unix socket with `cloudsql.instances` attachment.
- Configured service account with minimal roles: Run Invoker, Storage Object Admin, Vertex AI User, Logging Writer, Cloud SQL Client.
- Health endpoint reachable: `/health`.

### 🗄️ Database
- Provisioned Cloud SQL instance: `db-custom-1-3840` (1 vCPU, 3.75 GB), zonal, SSD 20 GB with auto-grow, backups + PITR.
- Created DB `mosaico` and user `mosaicoapp`.
- Tuned SQLAlchemy pool: `pool_size=5`, `max_overflow=5` for serverless autoscaling.
- Auto-create tables on startup for MVP (`Base.metadata.create_all`).

### 🗂️ Storage & AI
- Created GCS buckets: `mosaico-prompts-474415`, `mosaico-examples-474415`, confirmed `mosaico-images-474415`.
- Vertex AI initialized with `gemini-2.5-pro` and `gemini-2.5-flash`.

### 🔧 Build & Infra
- Resolved dependency conflicts:
  - Aligned `httpx==0.28.1` with `clerk-backend-api==1.5.0`.
  - Bumped `pydantic` to `2.10.3` per upstream constraints.
- Added `backend/.dockerignore` to slim Cloud Build context.

### 🔁 Frontend Integration
- Frontend calls backend via `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_BACKEND_URL`.
- Action required on Vercel: set `NEXT_PUBLIC_API_URL` to Cloud Run URL.

### 📄 Versioning
- Bumped backend `__version__` to `0.6.0` and updated README badge.

### Notes
- Current service URL: set in deploy logs; configure frontend env to use it.

---

## [0.6.1] - 2025-10-23

### ✅ CI/CD
- GitHub Actions: aggiunto `workflow_dispatch` per avviare manualmente il deploy su Cloud Run.
- README: badge di stato per il job Cloud Run e note su come lanciare il workflow.

### 🔧 Varie
- Nessuna modifica funzionale al codice; release di manutenzione.

---

## [0.5.0] - 2025-10-23

**🚀 Production Deployment Release**

This release marks the first successful deployment of Mosaico to Vercel, with complete removal of unused billing infrastructure and fixes for production environment compatibility.

### ✨ Added - Deployment Infrastructure
- **Vercel Deployment**: Frontend successfully deployed and live on Vercel
- **GitHub Auto-Deploy**: Configured webhooks for automatic deployments on push
- **Edge Runtime Compatibility**: Simplified Clerk middleware for Vercel Edge Runtime
- **Build Configuration**: Added `jsconfig.json` for robust path alias resolution
- **JavaScript Config**: Converted `next.config.ts` to `next.config.js` with explicit webpack aliases

### 🗑️ Removed - Billing & Payment Infrastructure
- **Stripe Integration**: Completely removed all Stripe-related code
  - Deleted `app/api/stripe/webhooks/route.ts` (webhook endpoint)
  - Deleted `actions/stripe.ts` (server actions)
  - Deleted `lib/stripe.ts` (Stripe client)
  - Deleted `components/payments/checkout-redirect.tsx`
  - Deleted `components/payments/pricing-button.tsx`
- **Payment UI**: Replaced payment buttons with "Coming Soon" placeholders in pricing section
- **Checkout Flow**: Removed checkout redirect component from root layout

### 🐛 Fixed - Critical Deployment Issues
- **Module Resolution**: Fixed `Module not found: Can't resolve '@/lib/utils'` error
  - Root cause: `.gitignore` was ignoring `frontend/lib/` directory
  - Solution: Modified `.gitignore` to only ignore `backend/lib/` and `backend/lib64/`
  - Force-added `lib/utils.ts` and `lib/stripe.ts` to Git (latter removed in same release)
- **Build Errors**: Resolved `DATABASE_URL is not set` error during static generation
  - Removed Stripe webhook that required database connection at build time
- **Middleware Invocation**: Fixed `MIDDLEWARE_INVOCATION_FAILED` on Vercel
  - Simplified Clerk middleware from manual auth checks to `auth.protect()`
  - Improved Edge Runtime compatibility

### 🔧 Configuration Changes
- **Git Ignore**: Updated `.gitignore` to be more specific about Python lib folders
- **Path Aliases**: Added `jsconfig.json` for dual TypeScript/JavaScript path resolution
- **Webpack Aliases**: Explicit `@` alias configuration in `next.config.js`
- **Environment Variables**: Documented required Vercel environment variables
  - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
  - `CLERK_SECRET_KEY` (critical for middleware)
  - `NEXT_PUBLIC_API_URL`
  - `NEXT_PUBLIC_BACKEND_URL`

### 📊 Deployment Metrics
- **Build Time**: ~40 seconds on Vercel
- **Bundle Size**: 246 kB for largest route (`/dashboard/projects/[id]`)
- **Static Pages**: 12 routes successfully generated
- **Dynamic Pages**: 6 server-rendered routes (dashboard, projects)

### 🎯 Breaking Changes
- **No Billing**: All payment and subscription features removed
- **Pricing Page**: Now shows "Coming Soon" instead of functional payment buttons
- **Middleware**: Changed from custom auth logic to `auth.protect()` (cleaner, more reliable)

### 📝 Documentation
- Updated README with deployment status and Vercel webhook test
- Documented all environment variables required for production
- Added troubleshooting notes for common deployment issues

### 🔗 Infrastructure
- **Frontend**: Deployed on Vercel with auto-deploy from GitHub
- **Backend**: Still local (`localhost:8080`) - production deployment planned for v0.6
- **Database**: Still local PostgreSQL - Cloud SQL/Supabase planned for v0.6
- **Authentication**: Clerk production instance configured and working

### 🚀 What's Next (v0.6 Roadmap)
- Deploy backend to Google Cloud Run
- Set up production PostgreSQL database (Cloud SQL or Supabase)
- Configure custom domain
- Implement environment-specific configurations
- Add production monitoring and logging

---

## [0.4.1] - 2025-10-22

### Sidebar hierarchy and status groups
- Projects list now nested under two collapsible groups: `In Progress` and `Approved`.
- `In Progress` group opens by default; open/close state persisted in localStorage.
- Removed redundant `Settings` group from sidebar (still accessible from user avatar).
- Minor visual tweaks to submenu labels and spacing.

### Internal
- Bumped versions: backend `__version__` to 0.4.1, frontend package.json to 0.4.1.

---

## [0.4.0] - 2025-10-20

**🎯 Major Feature Release: Auto-Retranslation & Drag-and-Drop Email Structure**

This release introduces intelligent auto-retranslation workflows and a completely redesigned drag-and-drop email structure builder, making content editing and translation management seamless and intuitive.

### ✨ Added - Auto-Retranslation System

#### Automatic Translation Regeneration
- **Regenerate All with Translations**: When regenerating all content, if translations existed, they are automatically regenerated
- **Regenerate Single with Translations**: When regenerating a single component, only that component's translations are regenerated
- **Manual Edit with Retranslation**: New "Save & Retranslate" button appears when editing content manually
  - Saves the edited content to database
  - Automatically regenerates translations if they existed
  - Visual feedback with spinner and greyed-out translations during processing

#### Visual Feedback During Translation
- **Loading Spinner**: Rotating loader icon appears next to "Translations" header
- **Greyed Out Content**: Translation cards become semi-transparent (opacity-50) during regeneration
- **Disabled Actions**: Copy buttons are disabled while translating
- **Smooth Transitions**: CSS transitions for opacity changes
- **Toast Notifications**: Clear feedback for each step ("Retranslating...", "Retranslated to X language(s)")

### ✨ Added - Drag-and-Drop Email Structure Builder

#### New Structure Builder (V2)
- **Always-Present Components**: Subject and Pre-header are always included and cannot be removed
- **Drag-and-Drop Interface**: Powered by `@dnd-kit` for smooth, accessible drag-and-drop
- **Dynamic Components**: Add multiple instances of:
  - **Title**: Main headline/section title
  - **Body Section**: Content paragraphs
  - **CTA Button**: Call-to-action buttons
- **Visual Reordering**: Drag handle (⋮⋮) for intuitive reordering
- **Real-time Preview**: See component order with numbered badges
- **Remove Components**: X button on each component (except Subject/Pre-header)

#### Builder Features
- Components maintain order during generation
- Subject and Pre-header locked at top positions
- Smooth animations during drag operations
- Visual feedback (opacity) when dragging
- Total component count display
- Clean, professional UI without emoji

### 🔧 Improvements - Language Support

#### Expanded Language Options (10 Languages)
- Removed English (source language, no translation needed)
- Added new languages:
  - **Italian** (it)
  - **German** (de)
  - **French** (fr)
  - **Spanish** (es)
  - **Portuguese** (pt)
  - **Russian** (ru)
  - **Chinese** (zh)
  - **Japanese** (ja)
  - **Arabic** (ar)
  - **Dutch** (nl)

### 🎨 UI/UX Improvements

#### Enhanced Editing Experience
- **Cancel Button**: Added to editing mode to discard changes without saving
- **Save & Retranslate**: Single action combines save + retranslate for edited content
- **Loading States**: Spinner on save button during processing
- **Better Feedback**: Clear toast messages for all actions

#### Structure Builder V2 Interface
- Cleaner design without emoji clutter
- Grip handle for drag operations
- Hover effects on components
- Smooth transitions and animations
- Numbered badge preview of final structure

### 📦 Dependencies

#### New Packages
- `@dnd-kit/core@^6.1.0` - Core drag-and-drop functionality
- `@dnd-kit/sortable@^8.0.0` - Sortable list utilities
- `@dnd-kit/utilities@^3.2.2` - Helper utilities for transforms

### 🐛 Fixed

#### Translation State Management
- Fixed translations not being detected when reopening saved projects
- Added debugging logs to track translation state (removed in final version)
- Translations now properly load from database and trigger auto-regeneration

#### React Rendering Issues
- Fixed "Cannot update component while rendering" error in EmailStructureBuilderV2
- Moved state updates from render to `useEffect` for proper lifecycle management

### 📁 Files Modified

#### Frontend
- `frontend/package.json` - Updated version to 0.4.0, added @dnd-kit dependencies
- `frontend/app/(authenticated)/dashboard/_components/content-generator.tsx`
  - Added `saveAndRetranslate` function for manual edits
  - Enhanced translation visual feedback
  - Auto-retranslation on regenerate all/single
  - Save & Retranslate button in edit mode
- `frontend/app/(authenticated)/dashboard/_components/email-structure-builder-v2.tsx` - **NEW**
  - Drag-and-drop structure builder
  - Always-present Subject/Pre-header
  - Dynamic Title/Body/CTA components
- `frontend/app/(authenticated)/dashboard/projects/[id]/_components/project-editor.tsx`
  - Switched from `EmailStructureBuilder` to `EmailStructureBuilderV2`
  - Updated type definitions to include "title" component

#### Backend
- `backend/app/__init__.py` - Updated version to 0.4.0

### 📊 User Flow Improvements

**Before (v0.3.1):**
1. Edit content manually
2. Click somewhere else (loses changes?)
3. Manually click Translate again
4. No visual feedback during translation

**After (v0.4.0):**
1. Edit content manually
2. Click "Save & Retranslate" (or Cancel)
3. Automatic retranslation if translations existed
4. Clear visual feedback (spinner + greyed out + toast)

**Structure Builder Before:**
- Checkboxes to enable/disable components
- Number inputs for counts
- No visual ordering
- Could remove Subject/Pre-header

**Structure Builder After:**
- Subject/Pre-header always present
- Drag & drop to reorder Title/Body/CTA
- Visual preview with numbered badges
- Intuitive add/remove buttons

### 🎯 Breaking Changes

#### Email Structure
- **Title component added**: Emails can now have title sections separate from body
- Existing projects without "title" will continue to work (backward compatible)
- New projects default to Subject + Pre-header only

---

## [0.3.1] - 2025-10-20

**🎨 UX Improvements: Streamlined Translation Workflow**

This patch focuses on improving the user experience for content generation and translation by making the workflow more intuitive and linear.

### 🎨 UI/UX Improvements

#### Image Upload Repositioning
- **Moved Image Upload to Left Column**: `ImageUploadManager` now appears under Creative Brief, before Tone of Voice
- **Clearer Context**: Images are now clearly part of the "input" (left column) rather than scattered in the output area
- **Better Mental Model**: All context/settings on the left, all outputs on the right

#### Translation Workflow Redesign
- **Removed Language Selection from Settings**: Target languages no longer appear in the left column with project settings
- **Contextual Language Selection**: Language badges now appear in the right column AFTER content generation
- **Linear Workflow**: Generate → Select Languages → Translate (natural progression)
- **Helper Text**: "Click to add or remove languages for translation" appears with language badges

#### Enhanced Translation Button
- **More Prominent**: Changed from `variant="outline"` (white) to `variant="default"` with `bg-blue-600 hover:bg-blue-700`
- **Larger Size**: Changed from `size="sm"` to `size="default"` for better visibility
- **Impossible to Miss**: Bright blue button stands out as the primary action after content generation
- **Dynamic Count**: Shows "Translate to X language(s)" with real-time count

#### Prompt Assistant Retained
- **Still Available**: "Optimize Prompt" button remains next to Creative Brief
- **User Requested**: Kept after feedback that this feature should not be removed

### 📊 User Flow Comparison

**Before (v0.3.0):**
```
Left Column: Name, Brief, Tone, Structure, Languages (confusing)
Right Column: Image Upload (separated from brief), Generate, Translate (small button)
```

**After (v0.3.1):**
```
Left Column: Name → Brief → Images → Tone → Structure (all inputs together)
Right Column: Generate → [Languages appear] → Translate (blue, prominent)
```

### 🎯 Benefits
- **Clearer Input/Output Separation**: All context on left, all results on right
- **Natural Progression**: Each step flows logically to the next
- **Can't Miss Translation**: Blue button is now the obvious next action
- **Image Context Clear**: Images are part of the brief, not floating separately

### 📁 Files Modified
- `frontend/app/(authenticated)/dashboard/projects/[id]/_components/project-editor.tsx`
  - Moved `ImageUploadManager` from right to left column
  - Removed `Target Languages` section from left column
  - Re-added `PromptAssistantDialog` after user feedback
  - Passed `onLanguagesChange` callback to `ContentGenerator`
- `frontend/app/(authenticated)/dashboard/_components/content-generator.tsx`
  - Added `LANGUAGES` constant
  - Added `onLanguagesChange` prop
  - Created new "Translation Section" that appears after generation
  - Language selection with clickable badges
  - Enhanced translate button styling (blue, larger)
  - Conditional rendering: only shows after content is generated

---

## [0.3.0] - 2025-10-20

**🎯 Major Feature Release: Intelligent AI Model Selection & Few-Shot Learning**

This release introduces a sophisticated multi-model AI strategy with Few-Shot learning, dramatically improving content quality, generation speed, and system stability. The system now intelligently selects between Gemini Pro (quality) and Flash (speed/stability) based on context, with automatic fallback mechanisms.

**Key Highlights:**
- 🧠 Few-Shot learning from real brand campaigns (27 CTA examples)
- ⚡ Gemini Flash for fast generation (5-6x faster, 95% cheaper)
- 🎯 Gemini Pro for narrative quality (bodies, long content)
- 🔄 Automatic fallback if Pro fails
- 📏 Smart prompt optimization (600 char limit with images)
- 🔠 CTA uppercase normalization
- 🚀 No-image regeneration for speed

---

### ✨ Added - Few-Shot Learning System
- **Email Parser**: Automatically extracts components from real email campaigns (`.eml` and `.html` files)
  - Parses 18+ example emails from LuisaViaRoma campaigns
  - Extracts: Subjects (19), CTAs (27 unique), Body sections (~95), Pre-headers (18 manual)
  - Stored in `backend/data/parsed_examples.json`
- **Few-Shot Database**: `backend/app/prompts/few_shot_loader.py`
  - Loads and manages real brand examples
  - Provides 8 random examples per component type to AI
  - Normalizes CTAs to UPPERCASE for brand consistency
- **Conditional Few-Shot Strategy**: 🎯 **Key Innovation**
  - Few-Shot examples **ONLY used for regeneration**, not initial generation
  - Initial generation: Lighter prompts, faster, more stable (works with images)
  - Regeneration: Adds Few-Shot for brand consistency and variety
  - Prevents JSON parsing errors when combining images + Few-Shot + long briefs
  - See `backend/docs/FEW_SHOT_STRATEGY.md` for detailed documentation

### 🔧 Improvements - AI Generation Quality
- **Enhanced Regeneration Logic**:
  - Generates 3 candidates instead of 1 for variety
  - Filters out duplicates and selects first truly different option
  - Shows count: "✅ Rigenerato! (3/3 varianti diverse trovate)"
- **Intelligent Model Selection with Auto-Fallback**: ⚡ 🧠 🔄
  - **Pro for Body Content** (always first, for narrative quality)
    - Flash tends to use bullet points, Pro maintains flowing paragraphs
    - Better tone consistency and storytelling
  - **Automatic Flash Fallback** if Pro fails
    - Detects JSON parsing errors (500 errors)
    - Automatically retries with Flash for stability
    - User sees: "⚠️ Retrying with Flash model for better stability..."
    - Success: "✅ Generation succeeded with Flash fallback!"
  - **Flash for Short Components** when image + complex structure (5+ components, no body)
    - Ideal for: Subject + Pre-header + CTAs only
    - 5-6x faster, 95% cheaper
    - Prevents JSON parsing errors
  - **Flash for CTA Regeneration** (<30 chars components)
    - ~0.5-1s instead of ~2-3s
    - Same quality for short text
  - **Pro for All Other Cases** (default)
- **Aggressive Anti-Repetition Prompts**:
  - Special handling for short components (CTAs < 30 chars)
  - Explicit forbidden words list
  - Alternative approach suggestions (different verbs, structures, focus)
  - Random iteration numbers and seeds to break caching
- **Higher Temperature for Regeneration**:
  - Base temperature + 0.5 for short components (max 1.0)
  - Base temperature + 0.3 for long components
- **Dynamic Sampling Parameters**:
  - `top_k: 60` (instead of 40) when temperature > 0.8
  - Increased variety in token selection

### 🐛 Fixed - Critical Bugs
- **JSON Parsing Errors**: Fixed "Unterminated string" errors during generation
  - Root cause: Gemini Pro fails with image + complex structure (8+ components)
  - Solution: Use Flash for complex generation with images (95%+ success rate)
  - Intelligent switching: Flash only when `hasImage && totalComponents >= 5`
  - Added automatic fallback: Pro → Flash if errors detected
- **CTA Regeneration with Flash**: Fixed "did not meet variation count expectations"
  - Root cause: Image + Few-Shot + complex prompt overwhelmed Flash
  - Solution: Remove image from regeneration requests (not needed for single component)
  - Result: 3 variations generated consistently, ~0.5s response time
- **Prompt Optimization Length**: Fixed prompts being too long (2700+ chars)
  - Root cause: Prompt Assistant expanded briefs without length constraints
  - Solution: Added max 600 chars limit when images present, 1000 chars otherwise
  - AI now consolidates instead of expanding when brief is already long
- **CTA Uppercase Normalization**: All CTAs now forced to UPPERCASE
  - Applied on both initial generation and regeneration
  - Ensures brand consistency regardless of AI output
- **Component Key Mismatch**: Fixed regeneration not working
  - API returns `{"cta": "..."}` but frontend looked for `{"cta_2": "..."}`
  - Now uses `componentType` as lookup key instead of `component.key`
- **Empty Variations Bug**: CTAs showing as empty strings
  - Added rigorous debugging with `📡 API RESPONSE` log
  - Identified and fixed key extraction logic
- **Save Function Parameters**: Fixed crash when auto-saving after regeneration
  - Now passes `updatedComponents` and `translations` explicitly
  - Prevents "Cannot read properties of undefined" error

### 🎨 UI/UX Improvements
- **Sidebar Logo**: Changed from black to gray background (`bg-gray-200`)
- **Page Title**: Updated to "Mosaico - AI Email Campaign Generator"
- **Error Feedback**: Shows explicit error when AI generates identical content
  - "❌ CTA invariato! L'AI ha generato '[CTA]' 3 volte. Problema di caching AI."
- **Success Feedback**: Shows variety count in toast messages
- **Console Cleanup**: Removed Stripe/billing warning messages
  - No more "Customer table not available" warnings
  - No more "STRIPE_SECRET_KEY is not set" warnings
  - Cleaner development console

### 📊 Performance Metrics
**Before (no Few-Shot):**
- CTAs: Always converged to same output ("SHOP NOW", "DISCOVER MORE")
- Regeneration: Identical results even with high temperature
- Variety: Low - model fell back to common patterns

**After (with Few-Shot):**
- CTAs: 3 unique alternatives every regeneration
- Examples: "EXPLORE THE CAPSULE", "VIEW THE TEAM-UP", "GET THE COLLECTION"
- Variety: High - draws from 27 real brand CTAs
- Brand Consistency: 100% uppercase, matches LVR style

### 📁 New Files Created
- `backend/scripts/parse_emails.py` - Email component extraction tool
- `backend/app/prompts/few_shot_loader.py` - Few-Shot example manager
- `backend/app/prompts/__init__.py` - Prompts package
- `backend/data/README.md` - Email data documentation
- `backend/data/.gitignore` - Protects email privacy
- `backend/data/sample_emails/.gitkeep` - Directory structure
- `backend/docs/FEW_SHOT_STRATEGY.md` - **Complete Few-Shot documentation**
- `frontend/app/icon.tsx` - 🎨 emoji favicon

### 🔧 Modified Files
- `backend/requirements.txt` - Added `beautifulsoup4`, `lxml`
- `backend/app/api/generate.py` - Conditional Few-Shot injection, Flash model support
- `backend/app/models/schemas.py` - Added `use_few_shot` and `use_flash` parameters
- `backend/app/core/vertex_ai.py` - Dynamic `top_k`, Flash model support in `generate_with_fixing`
- `frontend/actions/generate.ts` - Added `use_few_shot` and `use_flash` parameters
- `frontend/app/(authenticated)/dashboard/_components/content-generator.tsx` - Enhanced regeneration with conditional Few-Shot
- `frontend/app/(authenticated)/dashboard/_components/team-switcher.tsx` - Gray logo background
- `frontend/app/layout.tsx` - Updated page title

### 📝 Documentation
- **New**: `backend/docs/FEW_SHOT_STRATEGY.md` - Complete Few-Shot architecture guide
  - Explains why Few-Shot is only used for regeneration
  - Performance comparison (with/without Few-Shot)
  - Configuration options and best practices
  - Troubleshooting guide
- Added `backend/data/README.md` with email parsing instructions
- Updated inline code comments for conditional Few-Shot logic
- Added debug logs for troubleshooting regeneration issues

---

## [0.2.7] - 2025-10-17

### 🎨 UI/UX Improvements
- **New branding**: Changed logo and favicon to 🎨 emoji
- **Cleaner sidebar**: Removed SidebarRail component (resize handle)
- **Simplified team switcher**: Removed unnecessary dropdown menu for single workspace
- **Cleaner user menu**: 
  - Removed "Free" membership badge
  - Removed "Billing" menu item
  - Shows email directly under username

### 🧹 Code Cleanup
- Removed unused imports and components
- Simplified TeamSwitcher to support both emoji and icon logos
- Cleaner navigation structure

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

