# 📝 Multi-Section Briefs V2 - Lessons Learned & Better Approach

**Date**: December 14, 2024  
**Status**: Design document for next iteration  
**Previous Attempt**: `feat/multi-section-briefs` (reverted due to architectural issues)

---

## 🎯 Original Goal (Still Valid)

Support multi-topic newsletters where each section has its own brief and images.

**Example:**
- Main Section: "Lancio Collezione" with specific brief
- Section 2: "Categoria Casa" with different brief
- Section 3: "Loyalty Program" with different brief

**CMO Feedback:** Newsletters often cover multiple unrelated topics

---

## ❌ What Went Wrong (V1 Attempt)

### 1. State Synchronization Hell

**Problem:** Mixing server props (`project.components`) with client state  
**Symptom:** Images uploaded but not visible until manual refresh  
**Root cause:** `router.refresh()` doesn't immediately update React props

```tsx
// PROBLEMATIC PATTERN:
await saveComponents(...)
router.refresh()  // ← Async, doesn't wait
// Component still sees old props!
```

### 2. Too Many Find/Filter Inconsistencies

**Problem:** 10+ places where we search components  
**Each used different logic:**
- Some: `component_index` global
- Some: `section_key` only
- Some: `section_order` only
- Some: Both `section_key` OR `section_order`

**Result:** Components found in one place, not found in another

### 3. Backend Upsert Too Complex

**Problem:** Trying to be too smart with update vs create  
**Symptom:** Duplicates, wrong updates, session errors  
**Root cause:** SQL session gets confused after delete/create cycles

### 4. Image Component Handling

**Problem:** Images treated same as text components  
**Reality:** Images need special handling (upload, preview, section tracking)  
**Result:** Image upload broke text rendering, vice versa

### 5. Incremental Testing Failure

**Mistake:** Added too many features at once  
- Multi-section briefs
- Per-section generation
- Section-specific images
- Main section special logic
- Image warning dialog
- All at the same time!

**Result:** Hard to debug which part was broken

---

## ✅ What Worked Well

1. ✅ **Design document** (`MULTI_SECTION_BRIEFS_DESIGN.md`) - clear requirements
2. ✅ **Backend schema** (`SectionStructureCreate` with brief/content_type)
3. ✅ **UX concept** (Main Brief + section briefs) - makes sense
4. ✅ **Debounced inputs** - prevented focus loss
5. ✅ **English generation** enforcement in prompt

---

## 🏗️ Better Architecture (V2)

### Phase 1: State Management First

**Before any multi-section work:**

1. **Refactor data flow** to use proper React Query or SWR
   ```tsx
   // Instead of server props:
   const { data: project, mutate } = useSWR(`/api/projects/${id}`)
   
   // After any mutation:
   await mutate()  // ← Refetches and updates immediately
   ```

2. **Single source of truth**: Components always from API, not mixed state

3. **Test**: Upload image → mutate() → Image appears ✓

### Phase 2: Section Support (Without Multi-Brief Yet)

1. **Add section_key to ALL operations** (proven pattern)
2. **Test**: Single brief but multiple sections work
3. **Verify**: Components render per section correctly

### Phase 3: Multi-Brief (Last)

1. **Add section.brief** field
2. **Test**: Generation uses section brief
3. **No new complexity** - just add brief field

---

## 📋 Technical Debt to Fix First

### 1. Replace Server Props with Client Fetch

**Current (Problematic):**
```tsx
// page.tsx
<ProjectEditor initialProject={await getProject(id)} />  // Server prop

// ProjectEditor
const [project, setProject] = useState(initialProject)  // Stale!
```

**Better:**
```tsx
// page.tsx  
<ProjectEditor projectId={id} />  // Just pass ID

// ProjectEditor
const { data: project, mutate } = useSWR(`/api/projects/${id}`)
await saveComponents(...)
await mutate()  // ← Refetch, always fresh
```

### 2. Unify Component Search Logic

**Create ONE reusable function:**
```tsx
function findComponentForSection(
  components: Component[],
  sectionKey: string,
  sectionOrder: number,
  componentType: string
): Component | undefined {
  return components.find(c =>
    c.component_type === componentType &&
    (c.section_key === sectionKey || c.section_order === sectionOrder)
  )
}

// Use EVERYWHERE - consistent!
```

### 3. Simplify Backend Upsert

**Current:** Complex find-or-create with delete logic  
**Better:** Delete all for project, create fresh (transactional)

```python
def save_generated_content(...):
    # Delete ALL existing (clean slate)
    db.query(Component).filter(
        Component.project_id == project_id
    ).delete()
    
    # Create fresh from data
    for comp_data in components_data:
        db.add(Component(**comp_data))
    
    db.commit()
```

Simpler = less bugs!

---

## 🎯 V2 Implementation Plan

### Step 1: Infrastructure (1 day)
- [ ] Add SWR/React Query to frontend
- [ ] Refactor ProjectEditor to use client fetch
- [ ] Test: Any mutation → immediate UI update
- [ ] No multi-section yet!

### Step 2: Section Awareness (1 day)
- [ ] Ensure section_key in all component operations
- [ ] Create `findComponentForSection()` utility
- [ ] Use utility everywhere
- [ ] Test: Components render correctly per section
- [ ] Still single brief!

### Step 3: Multi-Brief (1 day)
- [ ] Add section.brief field (already done in schema ✓)
- [ ] Update generation to use section brief
- [ ] Test: Different content per section
- [ ] Done!

**Total:** 3 days, incremental, testable

---

## 🐛 Bugs Found (Reference)

1. `ensureKeys()` removing section fields (brief, image_ids)
2. `imagesBySection` using global counter instead of section filter
3. Component rendering without section filter
4. Backend upsert session errors
5. Image upload not saving section_key
6. Generate Content calling wrong endpoint
7. router.refresh() timing issues
8. Duplicate image components
9. Section loop only processing first section
10. State not updating after mutations

**All solvable with better architecture!**

---

## 📚 Carry Forward

**Keep:**
- ✅ Design doc (requirements clear)
- ✅ Schema updates (SectionStructureCreate)
- ✅ UX mockups (Main Brief + section briefs)
- ✅ Backend per-section generation logic (mostly good)

**Redo:**
- ❌ State management (use SWR/React Query)
- ❌ Component search (unify with utility)
- ❌ Backend upsert (simplify to delete-all + create)
- ❌ Testing approach (incremental, not big bang)

---

## 🚀 Next Session Plan

1. **Read this document** (refresh memory)
2. **New branch**: `feat/multi-section-v2`
3. **Step 1 first**: SWR setup only
4. **Test before proceeding**
5. **Incremental commits**

---

## 💡 Alternative: Simpler First Version

**If V2 still too complex**, consider:

**Minimal viable:**
- ✅ Keep single global brief
- ✅ Add "section tags" to components (for organization)
- ✅ Manual brief in component generation (user pastes different text)
- ❌ No automatic per-section brief system

**Then iterate** based on actual user needs vs theoretical requirements.

---

**Status**: Ready for V2 with clear lessons learned  
**Estimated effort**: 3 days (vs 1 day attempted)  
**Success probability**: High (with proper foundation)

