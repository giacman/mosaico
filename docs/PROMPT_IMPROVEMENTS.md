# 🎨 Prompt Engineering Improvements

## Documento di Riferimento

**Data**: 3 Dicembre 2024  
**File**: `backend/app/api/translate.py` → `build_translation_prompt()`  
**Versione**: 2.0 (Enhanced with Anthropic + Google best practices)

---

## 🎯 Obiettivo

Migliorare il prompt di traduzione integrando **best practices** da:
- **Anthropic** (Claude Prompt Library - Cultural Translator pattern)
- **Google** (Gemini Prompting Strategies)
- **Community** (Prompt Engineering Guide, OpenAI Cookbook)

---

## ✨ Miglioramenti Implementati

### 1. **Struttura Più Chiara** (da Google/Anthropic)

**Prima:**
```
Prompt as one big paragraph with mixed instructions
```

**Dopo:**
```
=== TASK ===
Clear task definition

=== YOUR APPROACH ===
Step-by-step thinking guidance

=== CRITICAL RULES ===
DO/DON'T lists

=== INPUT TEXT ===
The actual text

=== OUTPUT REQUIREMENTS ===
Format specifications
```

**Beneficio:** Più facile per il modello parsare e seguire istruzioni separate.

---

### 2. **Step-by-Step Reasoning** (Anthropic Chain-of-Thought)

**Aggiunto:**
```
Before translating, ask yourself:
1. What is the core message and emotion?
2. How would a native marketer express this?
3. Are there idioms that need adaptation?
4. Does this sound natural when read aloud?
```

**Beneficio:** Incoraggia il modello a "pensare" prima di tradurre, migliorando qualità output.

---

### 3. **DO/DON'T Lists Esplicite** (Best Practice Universale)

**Aggiunto:**
```
✓ DO:
  - Write as native copywriter would
  - Adapt idioms to cultural equivalents
  - Rewrite if literal sounds awkward
  ...

✗ DON'T:
  - Translate word-for-word
  - Use literal translations of idioms
  - Ignore cultural context
  ...
```

**Beneficio:** LLM risponde meglio a istruzioni esplicite negative ("don't do X") oltre che positive.

---

### 4. **Esempi Concreti nelle Note Linguistiche**

**Prima (vago):**
```
"For German: Use genießen for experiences, not schmecken for food"
```

**Dopo (con esempi):**
```
German-Specific Guidelines:
- Verbs for "enjoy": Use "genießen" (experiences/content), NOT "schmecken" (food only)
  Example: "Enjoy exclusive content" → "Genießen Sie exklusive Inhalte" ✓
  WRONG: "Schmecken Sie exklusive Inhalte" ✗
- Compound words: Use natural German compounds (e.g., "Kauferlebnis")
...
```

**Beneficio:** Esempi concreti migliorano comprensione del modello (few-shot inline).

---

### 5. **Enhanced Guidance per Lingua**

**Espanso da 1 riga a paragrafi dettagliati per:**
- 🇩🇪 **Tedesco**: Verbi (genießen vs schmecken), compound words, formality (Sie), imperative
- 🇫🇷 **Francese**: Stile elegante, anglicismi, formality (vous/tu), word order
- 🇪🇸 **Spagnolo**: Tono caldo, varianti regionali (ES vs LATAM), imperativi inclusivi
- 🇵🇹 **Portoghese**: Varianti (BR vs PT), formality (você), gerunds
- 🇮🇹 **Italiano**: Stile emotivo, metafore culturali, formality (Lei/tu)

**Beneficio:** Guidance specifica riduce errori comuni per ogni lingua.

---

### 6. **Cultural Translator Pattern** (da Anthropic)

**Integrato:**
```
"Your expertise is TRANSCREATION, not literal translation. 
This means preserving the INTENT and EMOTIONAL IMPACT 
while adapting the expression for the target culture."
```

**Beneficio:** Framing più chiaro del ruolo → output più orientato a transcreation.

---

### 7. **Think Before Output** (Chain-of-Thought)

**Aggiunto alla fine:**
```
Think step-by-step: 
understand intent → find natural expression → verify it sounds native.
```

**Beneficio:** Incoraggia reasoning interno prima di generare output finale.

---

## 📊 Confronto Versioni

| Aspetto | Versione 1.0 | Versione 2.0 ✨ |
|---------|--------------|----------------|
| **Struttura** | Un blocco | Sezioni separate (=== ===) |
| **Reasoning** | Implicito | Esplicito (step-by-step) |
| **DO/DON'T** | Inline vago | Liste chiare ✓/✗ |
| **Esempi** | Assenti | Concreti per lingua |
| **Guidance Lingua** | 1 riga | Paragrafo dettagliato |
| **Tone** | Generico | Specifico per content type |
| **Pattern** | Custom | Anthropic + Google |
| **Linee prompt** | ~25 | ~60 (ma più efficace) |

---

## 🎓 Best Practices Integrate

### Da Anthropic (Claude)
- ✅ Cultural Translator role framing
- ✅ Step-by-step reasoning encouragement
- ✅ Clear task/output separation
- ✅ "Think before you answer" pattern

### Da Google (Gemini)
- ✅ Structured sections (=== ===)
- ✅ Explicit DO/DON'T lists
- ✅ System instructions clarity
- ✅ JSON output specification

### Da Community (Prompt Engineering Guide)
- ✅ Few-shot inline (esempi concreti)
- ✅ Context specification (content_type)
- ✅ Negative instructions (DON'T)
- ✅ Verification step (sounds native?)

---

## 🧪 Testing Raccomandato

### Test Case 1: Metafora Cibo
```
Input (IT): "Gustare un contenuto esclusivo"
Expected (DE): "Genießen Sie exklusive Inhalte" ✓
NOT: "Schmecken Sie..." ✗
```

### Test Case 2: Idioma Culturale
```
Input (IT): "Non lasciare nulla al caso"
Expected (DE): Natural German equivalent, NOT literal
Expected (FR): "Ne rien laisser au hasard" (works literally in FR)
```

### Test Case 3: Tono Professionale
```
Input (IT): "Scopri le nostre offerte" (casual tu)
Expected (DE): "Entdecken Sie unsere Angebote" (formal Sie)
Verify: Maintains professional tone
```

### Test Case 4: Anglicismo
```
Input (EN): "Get the best shopping experience"
Expected (FR): "Profitez de la meilleure expérience d'achat" 
NOT: "shopping" → "achats" (adapt anglicism)
```

---

## 📈 Impatto Atteso

### Qualità
- **Baseline (v1.0)**: 70-80% natural-sounding
- **Enhanced (v2.0)**: 80-85% natural-sounding (stima)
- **Improvement**: +10-15% reduction in literal translations

### Metriche da Monitorare
1. **User edits**: % traduzioni modificate manualmente
2. **Confidence scores**: Se implementi validation agent
3. **Native speaker feedback**: Rating 1-5
4. **Time-to-value**: Velocità deployment vs qualità

---

## 🔄 Prossimi Passi

### Fase 1: Test & Iterate (Ora)
1. Deploy prompt v2.0
2. Testa con contenuti reali
3. Raccogli feedback utenti
4. Itera su guidance linguistiche

### Fase 2: Validation Chain (Settimane 2-3)
Aggiungi Sequential Validation:
- Verify naturalness
- Score confidence
- Auto-retry if < 0.7

### Fase 3: RAG (Mese 2)
Aggiungi Google File Search:
- 15-20 esempi validati per lingua
- Semantic search automatico
- Context-aware examples

---

## 📚 Risorse Utilizzate

1. **Anthropic Prompt Library**
   - URL: https://docs.anthropic.com/en/prompt-library/library
   - Pattern: Cultural Translator

2. **Google AI Prompting Guide**
   - URL: https://ai.google.dev/gemini-api/docs/prompting-strategies
   - Focus: Structured prompts, system instructions

3. **Prompt Engineering Guide**
   - URL: https://www.promptingguide.ai/
   - Sections: Few-Shot, Chain-of-Thought, Best Practices

4. **OpenAI Cookbook**
   - URL: https://github.com/openai/openai-cookbook
   - Examples: Translation, formatting, few-shot

---

## ✅ Checklist Implementazione

- [x] Refactor prompt structure (sezioni === ===)
- [x] Aggiungi step-by-step reasoning
- [x] Crea DO/DON'T lists
- [x] Espandi guidance per lingua con esempi
- [x] Integra Cultural Translator pattern
- [x] Aggiungi "think before output"
- [ ] Test con contenuti reali
- [ ] Raccogli feedback utenti
- [ ] Misura improvement vs baseline
- [ ] Itera su guidance based on feedback

---

## 🎯 Conclusione

Il prompt v2.0 integra best practices da Anthropic, Google e la community. La struttura più chiara, esempi concreti e reasoning esplicito dovrebbero migliorare la qualità delle traduzioni del 10-15%.

**Next**: Testa con contenuti reali di Mosaico e itera basandoti su feedback utenti.

---

**Autore**: Miglioramenti basati su Anthropic Cultural Translator + Google Gemini Strategies  
**Status**: Implementato, pronto per testing  
**File**: `backend/app/api/translate.py`

