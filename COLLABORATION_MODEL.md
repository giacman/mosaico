# Mosaico Collaboration Model

## Overview

Mosaico Phase 2 is designed from the ground up to support **real-time team collaboration** on email campaign projects. Unlike traditional single-user tools, Mosaico allows multiple team members (Art Directors, Editors, Merchandising) to work together seamlessly on the same projects.

---

## Key Principles

### 1. **Shared Access**
- ✅ All authenticated users can see **all projects**
- ✅ No project "ownership" - projects belong to the team, not individuals
- ✅ Role-based visibility (everyone with appropriate roles can access everything)

### 2. **Equal Permissions**
- ✅ All users can create, edit, and delete projects
- ✅ No field-level restrictions based on roles
- ✅ Trust-based model: the team decides who does what

### 3. **Activity Transparency**
- ✅ Complete audit trail of who did what and when
- ✅ Activity log visible to all team members
- ✅ Helps avoid conflicts and coordinate work

### 4. **Conflict Resolution**
- ✅ "Last save wins" approach (simple and predictable)
- ✅ Polling-based updates to show recent changes
- ✅ Warning if someone else modified the same field recently

---

## Architecture Changes

### Database Schema

#### Before (User-Isolated):
```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- Projects tied to individual users
    name VARCHAR(255),
    ...
);
```

#### After (Collaboration-Ready):
```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    
    -- Audit fields (not ownership)
    created_by_user_id VARCHAR(255),
    created_by_user_name VARCHAR(255),
    updated_by_user_id VARCHAR(255),
    updated_by_user_name VARCHAR(255),
    
    ...
);

CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    user_id VARCHAR(255) NOT NULL,
    user_name VARCHAR(255),
    action VARCHAR(100),  -- "updated_subject", "uploaded_image", etc.
    field_changed VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Changes

#### Before:
```python
# Projects filtered by user_id
GET /api/v1/projects?user_id=123

# User could only see their own projects
```

#### After:
```python
# All projects visible to authenticated users
GET /api/v1/projects

# Activity log for transparency
GET /api/v1/projects/{id}/activity

# Every mutation logs who did it
PUT /api/v1/projects/{id}
# → Automatically logs: user_id, user_name, action, timestamp
```

---

## Real-Time Collaboration Strategy

### Phase 2 MVP: Polling-Based (Simple)

**Implementation:**
- Every 10 seconds, frontend checks if project was updated
- If `updated_at` timestamp changed → show notification
- User can choose to reload or continue editing

**Pros:**
- ✅ Simple to implement (3-4 hours)
- ✅ No WebSocket infrastructure needed
- ✅ Works with standard HTTP/REST
- ✅ Good enough for team of 5-10 users

**Cons:**
- ⏱️ 10-second delay (not instant)
- 📡 More API calls (but negligible cost)

**Code Example:**
```typescript
// Frontend polling
useEffect(() => {
  const interval = setInterval(async () => {
    const latest = await fetchProject(projectId)
    if (latest.updated_at > currentProject.updated_at) {
      showNotification(`Project updated by ${latest.updated_by_user_name}`)
      // Offer to reload
    }
  }, 10000) // 10 seconds
  
  return () => clearInterval(interval)
}, [projectId])
```

### Phase 3 (Future): WebSocket-Based (Advanced)

**Implementation:**
- WebSocket server pushes updates in real-time
- Live presence indicators ("Sarah is editing...")
- Field-level locking (optional)

**Effort:** ~2-3 days additional work

---

## User Experience

### Scenario 1: Simultaneous Editing

**Setup:**
- Art Director (Sarah) and Editor (Marco) both open Project #42
- Sarah starts editing the subject line
- Marco starts editing body text

**What Happens:**
1. Sarah saves subject line → Backend logs: "Sarah updated subject"
2. Marco's UI polls (10s later) → Shows: "Sarah updated this project 5s ago"
3. Marco saves body text → Backend logs: "Marco updated body_1"
4. Both changes are preserved (different fields)

**Result:** ✅ No conflicts, both edits saved

### Scenario 2: Same Field Editing

**Setup:**
- Sarah and Marco both edit the same subject line
- Sarah types: "Spring Collection Launch 🌸"
- Marco types: "New Arrivals: Spring 2025"

**What Happens:**
1. Sarah clicks "Save" at 10:00:05
2. Marco clicks "Save" at 10:00:12
3. Marco's version wins (last save)

**Frontend Protection:**
```typescript
// Before saving, check if field was modified recently
if (field.updated_at > lastFetched && field.updated_by !== currentUser) {
  showWarning(`${field.updated_by_user_name} just edited this field. Refresh to see their changes or overwrite?`)
  // User can choose: "Refresh" or "Save Anyway"
}
```

**Result:** ⚠️ Conflict detected, user makes informed decision

### Scenario 3: Activity Log

**Sarah's View:**
```
Activity Log - Project: Spring Campaign

10:15 AM - Marco updated body_1
10:12 AM - Sarah updated subject
10:05 AM - Marco uploaded image_3
 9:58 AM - Sarah created project
```

**Benefits:**
- 👀 See what teammates are working on
- 🔄 Understand recent changes
- 💬 Coordination without Slack messages

---

## API Endpoints

### List All Projects (Shared)
```http
GET /api/v1/projects
Authorization: Bearer {token}

Response:
[
  {
    "id": 1,
    "name": "Spring Campaign",
    "created_by_user_name": "Sarah Chen",
    "updated_by_user_name": "Marco Rossi",
    "updated_at": "2025-10-16T10:15:00Z",
    ...
  }
]
```

### Get Project with Activity
```http
GET /api/v1/projects/1
Authorization: Bearer {token}

Response:
{
  "id": 1,
  "name": "Spring Campaign",
  "components": [...],
  "activity_logs": [
    {
      "user_name": "Marco Rossi",
      "action": "updated_subject",
      "created_at": "2025-10-16T10:15:00Z"
    }
  ]
}
```

### Get Activity Log
```http
GET /api/v1/projects/1/activity
Authorization: Bearer {token}

Response:
[
  {
    "id": 123,
    "user_id": "user_abc123",
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

## Migration Path

### From Phase 1 (Single User) to Phase 2 (Collaboration)

**Database Migration:**
```bash
# Run migration to add collaboration support
cd backend
alembic upgrade head  # Applies migration 002_add_collaboration.py
```

**Changes Applied:**
1. ✅ Remove `user_id` column from `projects`
2. ✅ Add `created_by_*` and `updated_by_*` audit fields
3. ✅ Create `activity_logs` table
4. ✅ Existing projects become accessible to all users

**Data Handling:**
- Existing projects: `created_by_user_id` set to `NULL` (legacy projects)
- Activity logs: Start fresh from migration date
- No data loss

---

## Configuration

### Environment Variables
```bash
# No new env vars needed for collaboration!
# Uses existing Clerk authentication
CLERK_SECRET_KEY=sk_...
```

### Clerk Setup
Clerk JWT tokens now include:
- `sub` (user ID) - Used for `user_id` in logs
- `name` or `email` - Used for `user_name` in logs

---

## Testing Collaboration

### Manual Test Scenario

1. **Create 2 Test Users in Clerk:**
   - `sarah@example.com`
   - `marco@example.com`

2. **Test Shared Access:**
   ```bash
   # Login as Sarah, create project
   curl -X POST /api/v1/projects \
     -H "Authorization: Bearer {sarah_token}" \
     -d '{"name": "Test Project", ...}'
   
   # Login as Marco, list projects
   curl /api/v1/projects \
     -H "Authorization: Bearer {marco_token}"
   
   # Marco should see Sarah's project ✓
   ```

3. **Test Activity Logging:**
   ```bash
   # Marco edits Sarah's project
   curl -X PUT /api/v1/projects/1 \
     -H "Authorization: Bearer {marco_token}" \
     -d '{"name": "Updated by Marco"}'
   
   # Check activity log
   curl /api/v1/projects/1/activity \
     -H "Authorization: Bearer {sarah_token}"
   
   # Should show: "Marco updated name" ✓
   ```

---

## Comparison: InventioHub vs Mosaico

| Feature | InventioHub | Mosaico |
|---------|-------------|---------|
| **Access Model** | User-isolated projects | Shared team projects |
| **Permissions** | Complex role-based ACLs | Simple trust-based model |
| **Collaboration** | None (single user) | Real-time with polling |
| **Activity Log** | None | Complete audit trail |
| **Conflict Resolution** | N/A | Last save wins + warnings |
| **Complexity** | High | Low |

---

## Future Enhancements (Phase 3)

### Possible Additions:
1. **WebSocket Real-Time** - Instant updates without polling
2. **Live Presence** - See who's currently viewing/editing
3. **Field-Level Locking** - Prevent simultaneous edits (optional)
4. **Comments** - Add discussion threads to projects
5. **Version History** - View and restore previous versions
6. **Notifications** - Email/Slack alerts for important changes

---

## Summary

Mosaico's collaboration model is designed to be:
- ✅ **Simple**: No complex permission systems
- ✅ **Transparent**: Full activity visibility
- ✅ **Practical**: Solves real team workflows
- ✅ **Scalable**: Easy to add advanced features later

**Key Takeaway:** Start with shared access + activity logs. Add real-time features only if users request them.

---

**Last Updated:** October 16, 2025  
**Status:** Implemented and ready for testing

