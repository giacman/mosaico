# 📝 Multi-Section Briefs - Design Document

## Problem Statement

**Current limitation**: One project = one global brief

```
Project: "Holiday Newsletter"
Brief: "Promuovi nuova collezione autunno"  ← Applies to ALL sections
Structure:
  - Section 1: Title, Body, CTA
  - Section 2: Title, Body, CTA
  - Section 3: Title, Body, CTA
```

**CMO Feedback**: Newsletters often have sections about different topics:
- Section 1: Lancio nuova collezione
- Section 2: Categoria casa
- Section 3: Loyalty program

Each section needs **its own brief** to generate relevant content.

---

## Proposed Solution

### Section-Level Briefs

```json
{
  "name": "Black Friday Campaign",
  "brief_text": "Multi-channel Black Friday 2025 campaign",  ← Optional global context
  "structure": [
    {
      "key": "section_1",
      "name": "Lancio Collezione",
      "brief": "Nuova collezione autunno/inverno 2025 con focus su sustainability",
      "content_type": "newsletter",
      "components": ["title", "body", "cta"]
    },
    {
      "key": "section_2",
      "name": "Categoria Casa",
      "brief": "Promuovi articoli per la casa, target famiglie",
      "content_type": "newsletter",
      "components": ["title", "body", "cta"]
    },
    {
      "key": "section_3",
      "name": "Loyalty Program",
      "brief": "Incoraggia iscrizione loyalty con benefit esclusivi",
      "content_type": "newsletter",
      "components": ["title", "body"]
    }
  ]
}
```

---

## Architecture Changes

### Backend Schema

#### `SectionStructureCreate` (Updated)

```python
class SectionStructureCreate(BaseModel):
    key: str
    name: str
    brief: Optional[str] = None  # ← NEW: Section-specific brief
    content_type: ContentType = ContentType.NEWSLETTER  # ← NEW: Future-proof
    image_ids: List[int] = []  # ← NEW: Section-specific images (recommended)
    components: List[str]
```

**Backward Compatibility:**
- If `section.brief` is None → fallback to `project.brief_text`
- Existing projects continue to work

#### Generation Logic (Updated)

```python
# Before (global brief)
prompt = build_generation_prompt(
    text=project.brief_text,  # ← Global brief for all
    structure=all_components
)

# After (section-specific)
for section in project.structure:
    section_brief = section.get("brief") or project.brief_text  # ← Fallback
    prompt = build_generation_prompt(
        text=section_brief,  # ← Section-specific!
        structure=section["components"],
        content_type=section.get("content_type", "newsletter")
    )
```

---

## Frontend Changes

### Current UI

```
┌──────────────────────────────┐
│ Creative Brief (Global)      │
│ ┌──────────────────────────┐ │
│ │ Promuovi collezione...   │ │
│ └──────────────────────────┘ │
└──────────────────────────────┘

Email Structure:
├─ Section 1: Title, Body, CTA
├─ Section 2: Title, Body, CTA
└─ Section 3: Title, Body
```

### New UI

```
Email Structure:

┌─────────────────────────────────────────┐
│ Section 1: Lancio Collezione            │
│ ┌───────────────────────────────────┐   │
│ │ Brief: Nuova collezione autunno   │   │  ← Brief per sezione
│ └───────────────────────────────────┘   │
│ 🖼️ Images: [Upload] ⚠️ Consigliato    │  ← Immagini per sezione
│ Components: Title, Body, CTA            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Section 2: Categoria Casa               │
│ ┌───────────────────────────────────┐   │
│ │ Brief: Promuovi articoli casa     │   │  ← Brief diverso!
│ └───────────────────────────────────┘   │
│ 🖼️ Images: casa_1.jpg ✅               │  ← Immagine caricata
│ Components: Title, Body, CTA            │
└─────────────────────────────────────────┘

Global Context (Optional):
"Black Friday 2025 Campaign" ← Fallback
```

### Image Warning System

**When user clicks "Generate Content":**

```
┌────────────────────────────────────┐
│ ⚠️ Missing Images                  │
├────────────────────────────────────┤
│ The following sections don't have  │
│ images:                            │
│                                    │
│ • Section 1: Lancio Collezione     │
│ • Section 3: Loyalty Program       │
│                                    │
│ Adding images helps AI generate    │
│ more relevant and contextualized   │
│ content.                           │
│                                    │
│ [Upload Images] [Proceed Anyway]   │
└────────────────────────────────────┘
```

**Behavior:**
- Not mandatory (can proceed)
- Recommends adding for better results
- Shows which sections are missing images

---

## Future-Proofing for Multi-Content

### Phase 1: Multi-Section Newsletter (Now)
```
All sections: content_type="newsletter"
Different briefs per section
```

### Phase 2: Content Reuse (Next)
```
Newsletter Section 2 → "Convert to Social Post"
    ↓
Creates new social_post project
Reuses: brief, content, translations
```

### Phase 3: Hybrid Projects (Future)
```
One project = multiple content types
Section 1: newsletter (email body)
Section 2: social_post (Instagram)
Section 3: social_post (Facebook)
```

---

## Database Changes

### No Migration Needed! ✅

**Why?**
- `structure` is already JSON column → flexible schema
- Just add `brief` and `content_type` to JSON objects
- No SQL schema change required

**Migration strategy:**
```python
# Old projects (no section.brief):
section = {
  "key": "main",
  "components": ["title", "body"]
  # No "brief" field
}

# Code handles fallback:
section_brief = section.get("brief") or project.brief_text

# Works perfectly! ✅
```

---

## Implementation Plan

### Step 1: Backend Schema ✅ (Done)
- [x] Update `SectionStructureCreate` with `brief` and `content_type`
- [x] Ensure backward compatibility in validators

### Step 2: Backend Logic
- [ ] Update generation logic to use section.brief
- [ ] Update `generate_project_content()` endpoint
- [ ] Ensure fallback to project.brief_text

### Step 3: Frontend UI
- [ ] Add brief textarea to each section
- [ ] Update EmailStructure component
- [ ] Maintain global brief as fallback/context

### Step 4: Testing
- [ ] Test new projects with section briefs
- [ ] Test old projects still work (backward compatibility)
- [ ] Test mixed (some sections with brief, some without)

---

## Example Use Case

### Use Case: Black Friday Multi-Topic Campaign

```
Project Name: "Black Friday 2025 Campaign"
Global Context: "Luxury brand, Black Friday focus"

Section 1: "Lancio Collezione Autunno"
Brief: "Nuova collezione A/I 2025, sustainability focus, target 25-45 anni"
Components: image, title, body, cta
→ AI genera contenuto specifico per collezione

Section 2: "Categoria Casa - Offerte Esclusive"
Brief: "Promuovi articoli casa con sconto 40%, target famiglie"
Components: title, body, cta  
→ AI genera contenuto specifico per casa

Section 3: "Loyalty Program"
Brief: "Incoraggia iscrizione loyalty con 500 punti benvenuto"
Components: title, body
→ AI genera contenuto specifico per loyalty
```

**Result**: Email coerente ma con sezioni diverse e rilevanti! 🎯

---

## Backward Compatibility Strategy

### Existing Projects

```python
# Old project (no section.brief)
project = {
  "brief_text": "Global brief",
  "structure": [{
    "key": "main",
    "name": "Main Section",
    "components": ["title", "body"]
    # No "brief" field
  }]
}

# Code behavior:
section_brief = section.get("brief") or project.brief_text
# → Uses "Global brief" ✅

# UI behavior:
if (!section.brief) {
  // Show global brief as placeholder
  // Or hide section brief field
}
```

**Zero breaking changes!** ✅

---

## Next Steps After This Feature

### Phase 2: Content Reuse
```
Button: "Convert Section to Social Post"
    ↓
Creates new project {
  name: "Social: Categoria Casa",
  brief_text: section_2.brief,  // Reuse!
  structure: [{
    content_type: "social_post",
    components: ["caption", "hashtags"]
  }]
}
```

### Phase 3: Activate Other Content Types
```
- /social → content_type: social_post
- /magazine → content_type: editorial
- /push → content_type: push_notification
- /marketing → content_type: ad_copy
```

All reuse same section-based architecture! 🔄

---

## Questions & Decisions

### Q: Keep global brief_text?
**A**: YES - Use as fallback and optional global context

### Q: content_type per section or per project?
**A**: Per section (more flexible for future hybrid projects)

### Q: Database migration needed?
**A**: NO - JSON column is flexible, just update application logic

### Q: UI complexity?
**A**: Slightly higher, but manageable with collapsible sections

---

**Status**: Ready for implementation  
**Complexity**: Medium (2-3 days)  
**Risk**: Low (backward compatible)  
**Value**: High (solves CMO feedback + future-proofs architecture)

