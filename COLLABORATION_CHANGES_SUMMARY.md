# Collaboration Model Changes - Summary

## What Changed?

Based on your requirements for multi-user collaboration, I've updated the Mosaico backend to support team-based project access with activity tracking.

---

## Your Requirements ✓

1. ✅ **All users with the right role can access all projects** (not user-isolated)
2. ✅ **Everyone can do everything** (no role-based field restrictions)
3. ✅ **Activity logging** (track who did what)
4. ✅ **Real-time collaboration support** (via polling, simple implementation)

---

## Files Modified

### 1. **Database Models** (`backend/app/db/models.py`)
**Changes:**
- Removed `user_id` from `Project` model (no ownership)
- Added audit fields: `created_by_user_id`, `created_by_user_name`, `updated_by_user_id`, `updated_by_user_name`
- Added new `ActivityLog` model for tracking all project activities
- Added `activity_logs` relationship to `Project`

### 2. **Pydantic Schemas** (`backend/app/models/project_schemas.py`)
**Changes:**
- Updated `ProjectResponse` to include audit fields instead of `user_id`
- Added `ActivityLogResponse` schema for activity log endpoints

### 3. **Authentication** (`backend/app/core/auth.py`)
**Changes:**
- Created `User` named tuple with `id` and `name`
- Updated `get_current_user()` to return `User` object (not just string)
- Now extracts both user ID and name from Clerk JWT tokens

### 4. **Service Layer** (`backend/app/services/project_service.py`)
**Complete Rewrite:**
- Removed all `user_id` filtering from queries
- All methods now accept `user_id` and `user_name` for audit purposes only
- Added `_log_activity()` helper method to track all changes
- Activity logging for: create, update, delete, component changes, translations
- `get_project()` and `list_projects()` no longer filter by user
- Added `get_activity_log()` method to retrieve project history

### 5. **API Endpoints** (`backend/app/api/projects.py`)
**Changes:**
- Updated all endpoints to use `User` object from auth
- Removed user-based authorization checks
- All authenticated users can now:
  - List all projects
  - View any project
  - Edit any project
  - Delete any project
- Added new `/projects/{id}/activity` endpoint for activity logs
- Better documentation explaining shared access model

### 6. **Database Migration** (`backend/migrations/versions/002_add_collaboration.py`)
**New File:**
- Migration to transform schema from user-isolated to collaboration-ready
- Removes `user_id` column
- Adds audit fields
- Creates `activity_logs` table
- Includes rollback capability

### 7. **Documentation** 
**New Files:**
- `COLLABORATION_MODEL.md` - Complete guide to collaboration features
- `COLLABORATION_CHANGES_SUMMARY.md` - This file

---

## Database Schema Changes

### Projects Table

**Before:**
```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- ❌ Removed
    name VARCHAR(255),
    ...
);
```

**After:**
```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    -- Audit fields (not ownership)
    created_by_user_id VARCHAR(255),      -- ✅ Added
    created_by_user_name VARCHAR(255),    -- ✅ Added
    updated_by_user_id VARCHAR(255),      -- ✅ Added
    updated_by_user_name VARCHAR(255),    -- ✅ Added
    ...
);
```

### New Activity Logs Table

```sql
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    user_id VARCHAR(255) NOT NULL,
    user_name VARCHAR(255),
    action VARCHAR(100),           -- e.g., "updated_subject"
    field_changed VARCHAR(100),    -- e.g., "subject"
    old_value TEXT,
    new_value TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Changes

### Endpoint Behavior Changes

#### `GET /api/v1/projects`
**Before:** Returns only projects owned by authenticated user  
**After:** Returns ALL projects (shared access)

#### `GET /api/v1/projects/{id}`
**Before:** Returns 404 if user doesn't own project  
**After:** Returns project if it exists (no ownership check)

#### `PUT /api/v1/projects/{id}`
**Before:** Returns 404 if user doesn't own project  
**After:** Allows any authenticated user to edit, logs who made changes

#### `DELETE /api/v1/projects/{id}`
**Before:** Only owner can delete  
**After:** Any authenticated user can delete, logs who deleted

### New Endpoints

#### `GET /api/v1/projects/{id}/activity`
**Purpose:** Retrieve activity log for a project  
**Response:**
```json
[
  {
    "id": 123,
    "project_id": 1,
    "user_id": "user_abc",
    "user_name": "Marco Rossi",
    "action": "updated_subject",
    "field_changed": "subject",
    "old_value": "Spring Collection",
    "new_value": "Spring Collection Launch",
    "created_at": "2025-10-16T10:15:00Z"
  }
]
```

---

## Activity Tracking

### What Gets Logged?

Every project mutation automatically logs:
- ✅ Project creation
- ✅ Project updates (each field changed)
- ✅ Project deletion
- ✅ Component creation
- ✅ Component updates
- ✅ Translation additions/updates

### Activity Log Entry Example

```python
# When user updates project name
activity_log = {
    "project_id": 1,
    "user_id": "user_abc123",
    "user_name": "Marco Rossi",
    "action": "updated_name",
    "field_changed": "name",
    "old_value": "Spring Collection",
    "new_value": "Spring Campaign 2025",
    "created_at": "2025-10-16T10:15:00Z"
}
```

---

## Real-Time Collaboration

### Implementation Strategy

**Phase 2 MVP:** Polling-Based (Simple)
- Frontend polls every 10 seconds
- Checks `updated_at` timestamp
- Shows notification if project was modified by someone else
- User can reload or continue editing

**Complexity:** Low (~3-4 hours implementation)  
**Good for:** Teams of 5-15 users

**Code Example (Frontend):**
```typescript
useEffect(() => {
  const interval = setInterval(async () => {
    const latest = await fetchProject(projectId)
    if (latest.updated_at > currentProject.updated_at) {
      toast.info(`${latest.updated_by_user_name} just updated this project`)
      // Show "Reload" button
    }
  }, 10000)
  return () => clearInterval(interval)
}, [projectId])
```

---

## Migration Guide

### To Apply These Changes:

1. **Update Code:**
   ```bash
   # Code is already updated in your workspace
   git status  # See all modified files
   ```

2. **Run Database Migration:**
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **Restart Backend:**
   ```bash
   python -m app.main
   ```

4. **Test:**
   ```bash
   # Login as User A, create project
   curl -X POST /api/v1/projects ...
   
   # Login as User B, list projects
   curl /api/v1/projects ...
   # Should see User A's project ✓
   ```

### Rollback (If Needed):
```bash
cd backend
alembic downgrade -1  # Back to user-isolated model
```

---

## What You Answer Questions About Alembic:

### Q1: What is Alembic?

**Answer:** Alembic is a database migration tool for SQLAlchemy. It's like "version control for your database schema."

**Why You Need It:**
- When you change database models (add column, create table), the actual database needs to be updated
- Alembic creates "migration files" that describe how to evolve the database
- It tracks which migrations have been applied

**Example:**
```bash
# You just removed user_id from Project model
# Generate migration automatically
alembic revision --autogenerate -m "remove user_id"

# Apply migration to database
alembic upgrade head
```

---

## Impact on Frontend

### What Frontend Needs to Show:

1. **Project List:**
   - Show all projects (not filtered by user)
   - Display `created_by_user_name` and `updated_by_user_name`
   - Sort by `updated_at` (most recent first)

2. **Project Editor:**
   - Poll for changes every 10 seconds
   - Show notification: "Marco just updated this project 30s ago"
   - Offer "Reload" button

3. **Activity Feed (Optional but Recommended):**
   - Sidebar showing recent activity
   - "Marco updated subject line 5m ago"
   - "Sarah uploaded image 12m ago"

---

## Testing Checklist

- [ ] Create project as User A
- [ ] Login as User B, verify can see User A's project
- [ ] User B edits project, check activity log shows User B's action
- [ ] User A and User B edit same project simultaneously (last save wins)
- [ ] Delete project as User C, verify activity log shows deletion
- [ ] Check `/projects/{id}/activity` endpoint returns full history

---

## Next Steps

1. ✅ **Backend collaboration support** - DONE
2. ⏳ **Frontend implementation** - Next phase
3. ⏳ **Real-time polling** - Implement in frontend
4. ⏳ **Activity feed UI** - Build activity log component

---

## Questions?

- **Q: Can we add role-based restrictions later?**  
  A: Yes! You can add permission checks in the service layer without changing the database schema.

- **Q: What if we want WebSockets instead of polling?**  
  A: Easy to add in Phase 3. The activity log foundation is already in place.

- **Q: How do we handle conflicts?**  
  A: "Last save wins" by default. Frontend can warn users if field was recently edited by someone else.

---

**Status:** ✅ Backend collaboration support complete  
**Next:** Build frontend with McKay's template  
**Estimated Frontend Work:** 25-30 hours

