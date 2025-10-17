# Team Workflow & Notification System

## Overview

Mosaico now includes a **dual notification system** designed to support team collaboration across different stages of email campaign creation.

---

## Notification Types

### 🍞 Toast Notifications (Temporary)
- **Duration**: 3-5 seconds
- **Location**: Bottom corner of screen
- **Purpose**: Immediate feedback for user actions
- **Behavior**: Disappears automatically

### 🔔 Notification Center (Persistent)
- **Duration**: Until manually dismissed
- **Location**: Bell icon in top-right header
- **Purpose**: Team handoff tracking and activity history
- **Behavior**: Shows badge count, persists across actions

---

## Team Workflow Integration

### **Phase 1: Project Setup** (CRM Team)
**When**: Project is created
**Triggers**:
- ✅ **Toast**: "Project created successfully"
- 🔔 **Notification Bell**: 
  - **Title**: Project Created
  - **Message**: Campaign "[Name]" has been created. CRM team can now add structure and brief.

**Team Actions**:
- CRM team creates project
- Designers add images to `Image Upload Manager`
- Merchandising team adds product URLs

---

### **Phase 2: Content Generation** (Content Team Review)
**When**: AI generates email content
**Triggers**:
- ✅ **Toast**: "Content generated successfully!"
- 🔔 **Notification Bell**:
  - **Title**: Content Generated
  - **Message**: AI has generated [X] components. Content team can now review for quality.

**Team Actions**:
- Content team reviews generated copy
- Edits/refines using inline editing or regenerate buttons
- Adjusts temperature for better results if needed
- **Future**: Could be fully automated (skip human review)

---

### **Phase 3: Translation** (Translation Team Review)
**When**: Batch translation completes
**Triggers**:
- ✅ **Toast**: "Translated to [X] languages!"
- 🔔 **Notification Bell**:
  - **Title**: Translation Completed
  - **Message**: Content translated to [X] language(s). Translation team can now review. Ready for Airship export.

**Team Actions**:
- Translation team reviews translations for accuracy
- Checks cultural/idiomatic appropriateness
- Makes manual adjustments if needed
- **Future**: Could be fully automated (skip human review)

---

### **Phase 4: Export to Airship** (CRM Team)
**When**: Content and translations are approved
**Action**: CRM team manually copies handlebars to Airship

**How to Export**:
1. Click the **file icon** (📄) next to each component
2. Copies handlebar template with all language conditionals
3. Paste into Airship email editor

**Handlebar Format Example**:
```handlebars
{{#eq selected_language "IT"}}Scopri la nuova collezione{{else eq selected_language "FR"}}Découvrez la nouvelle collection{{else eq selected_language "EN"}}Discover the new collection{{else}}Discover the new collection{{/eq}}
```

---

## Notification Center Features

### UI Elements
- **Bell Icon**: Always visible in header
- **Badge Count**: Shows number of unread notifications (red badge)
- **Notification List**: Scrollable list with timestamps
- **Actions**: Mark as read, dismiss individual, mark all as read

### Persistence
- **Current**: In-app state (resets on page reload)
- **Future Enhancement**: Can be persisted to PostgreSQL database for cross-session/cross-device access

---

## Backend Integration (Slack)

In addition to frontend notifications, the backend **also sends Slack webhooks** for:
- Project created
- Content generated
- Translation completed

**Setup**: Add `SLACK_WEBHOOK_URL` to `backend/.env`

**Format**: 
```
*Project Created*
Project 'Summer Collection' has been created by user@example.com.
```

This allows managers/stakeholders to track campaign progress without being in the app.

---

## Future Enhancements

1. **Database Persistence**: Store notifications in PostgreSQL for history across sessions
2. **Real-time WebSocket Updates**: Push notifications to all team members when events occur
3. **Email Notifications**: Send digest emails for important events
4. **Custom Filters**: Filter by team, project, or notification type
5. **Notification Preferences**: Let users choose which events to track
6. **Activity Timeline**: Visual timeline showing all project milestones

---

## Testing the System

### 1. Create a Project
- Click "+ New Project"
- Fill in name and brief
- ✅ Toast appears immediately
- 🔔 Bell badge shows "1"
- Click bell to see persistent notification

### 2. Generate Content
- Go to project editor
- Add structure, brief, images
- Click "Generate Email Content"
- ✅ Toast appears
- 🔔 Bell badge increments
- Check notification center for details

### 3. Translate Content
- After generation, add target languages
- Click "Translate to [X] language(s)"
- ✅ Toast appears
- 🔔 Bell badge increments
- Notification shows ready for Airship export

---

## Implementation Details

### Files Modified

**Frontend**:
- `frontend/app/(authenticated)/dashboard/_components/create-project-dialog.tsx`
  - Added `useNotifications()` hook
  - Calls `addNotification()` after successful project creation
  
- `frontend/app/(authenticated)/dashboard/_components/content-generator.tsx`
  - Added `useNotifications()` hook
  - Calls `addNotification()` after generation and translation

**Backend** (already implemented):
- `backend/app/utils/notifications.py` - Slack webhook sender
- `backend/app/api/projects.py` - Triggers Slack notification on project create
- `backend/app/api/generate.py` - Triggers Slack notification on generation
- `backend/app/api/translate.py` - Triggers Slack notification on translation

### Key Patterns

**Dual Notification Pattern**:
```typescript
// Immediate feedback (toast)
toast.success("Action completed!")

// Persistent tracking (notification center)
addNotification({
  type: "success",
  title: "Action Completed",
  message: "Details about what happened and next steps."
})
```

**Benefits**:
- Users get instant feedback (toast)
- Teams can review history (notification center)
- Managers can track via Slack
- Clear handoff points between teams

---

## Comparison: Before vs After

| Feature | Before | After |
|---------|--------|-------|
| User Feedback | Toast only | Toast + Persistent notification |
| Team Visibility | None | Notification center with history |
| Cross-team Handoff | Manual communication | Automatic notifications |
| Manager Oversight | Check app manually | Slack updates |
| Activity History | None | Notification center (dismissible) |

---

**Result**: Clear visibility into campaign progress with minimal friction. Each team knows when their work is ready to begin. 🎯

