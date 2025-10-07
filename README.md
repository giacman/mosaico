# Project Mosaico

**Versione:** 1.0
**Status:** Fase 1 - Kick-off

## 1. Vision & Executive Summary

**Project Mosaico** è un'iniziativa strategica per costruire una **piattaforma di AI content** aziendale. Invece di partire con una piattaforma rigida e complessa, adottiamo un approccio incrementale: iniziamo con un **co-pilota intelligente** integrato nei workflow esistenti, validando l'approccio prima di espandere verso una piattaforma completa.

La Fase 1 si concentra sulla risoluzione dei problemi più urgenti del team newsletter (contenuti monotoni, scarsa aderenza ai prompt) attraverso un **Add-on per Google Workspace**. Questo add-on fornirà assistenza IA direttamente in Google Sheets, appoggiandosi a un backend intelligente costruito su **Google Cloud Platform** e potenziato da **Vertex AI**. L'obiettivo immediato è trasformare il processo creativo da manuale a potenziato dall'IA, aumentando efficienza, qualità e coerenza del brand. **L'architettura modulare permetterà di espandere progressivamente verso altri use case e canali, costruendo la piattaforma pezzo per pezzo.**

## 2. The Problem

I tentativi precedenti di introdurre strumenti di IA hanno incontrato resistenza a causa di tre problemi fondamentali:
1.  **Frizione nel Workflow:** L'imposizione di un flusso di lavoro rigido si scontra con i metodi collaborativi e flessibili che i team hanno perfezionato su Google Sheets.
2.  **Qualità dei Contenuti:** I testi generati sono spesso monotoni, generici e non riflettono il tono di voce unico del nostro brand.
3.  **Scarsa Affidabilità:** L'IA non riesce a seguire in modo consistente istruzioni di formattazione specifiche (es. grassetto, maiuscole), richiedendo un pesante lavoro di revisione manuale.

## 3. Phase 1: The Co-pilot MVP

L'obiettivo della Fase 1 è lanciare un **Minimum Viable Product (MVP)** che convalidi l'approccio del co-pilota e diventi uno strumento indispensabile per i nostri creatori di contenuti.

**Obiettivi Chiave:**
- **Validare la Soluzione:** Dimostrare il valore di un assistente IA integrato nel workflow esistente.
- **Ottenere Adozione:** Raggiungere un'adozione >80% da parte dei team target entro il primo mese.
- **Aumentare l'Efficienza:** Ridurre significativamente il tempo necessario per la creazione di variazioni, traduzioni e descrizioni di prodotto.
- **Migliorare la Qualità:** Garantire la coerenza con il tone of voice del brand e l'aderenza alle regole di formattazione.

**Metriche di Successo:**
- **Tasso di Adozione:** >80% degli utenti target utilizzano l'add-on almeno 3 volte a settimana.
- **Riduzione Tempo:** -50% del tempo medio per creare variazioni o traduzioni.
- **Qualità Percepita:** Score medio >4/5 nelle valutazioni degli utenti sui contenuti generati.
- **Tasso di Revisione:** <20% dei contenuti generati richiede modifiche sostanziali.
- **Brand Consistency Score:** >90% dei contenuti generati superano la revisione tone of voice.

## 4. Key Features (Phase 1)

L'Add-on di Google Sheets fornirà le seguenti funzionalità:

- [ ] **Autenticazione Semplice:** Login sicuro tramite account Google aziendale.
- [ ] **Generatore di Variazioni Creative:** Crea N alternative di un testo selezionato, con opzioni per cambiare il tono.
- [ ] **Traduzione Contestuale:** Traduce il testo mantenendo il contesto e la formalità richiesta.
- [ ] **Riformulazione Rapida:** Funzioni one-click come "Rendi più corto", "Correggi grammatica", "Migliora chiarezza".
- [ ] **Image-to-Text (Descrizioni Prodotto):** Genera descrizioni di prodotto accattivanti partendo da un URL di immagine.
- [ ] **Coerenza con il Brand:** Tutti i contenuti generati saranno automaticamente allineati con il nostro tone of voice.
- [ ] **Modalità Preview:** Gli utenti possono rivedere i contenuti generati prima di applicarli alle celle, con possibilità di rigenerare.
- [ ] **Feedback Loop:** Sistema di rating (👍/👎) per ogni output generato, per migliorare continuamente i prompt e monitorare la qualità.

## 5. Technical Architecture (Google Cloud)

L'infrastruttura sarà interamente serverless e basata su GCP per garantire sicurezza, affidabilità e costi ottimizzati.

**Flusso Architetturale:**
`Utente (Google Sheet)` → `Google Workspace Add-on` → `Cloud Run Service` → `Vertex AI (Gemini)`

| Componente | Tecnologia | Scopo |
| :--- | :--- | :--- |
| **Frontend** | Google Apps Script (TypeScript) | UI/UX all'interno di Google Sheets. |
| **Backend** | Cloud Run (Python & FastAPI) | Logica di business, prompt engineering, gestione RAG, autenticazione. |
| **AI Layer** | Vertex AI | Accesso ai modelli di linguaggio (Gemini 2.5 Pro). |
| **Caching** | Cloud Memorystore (Redis) | Cache per richieste ripetute e riduzioni costi API. |
| **Storage** | Cloud Storage | Repository per prompt templates e esempi tone of voice. |
| **Monitoring** | Cloud Logging + Cloud Monitoring | Tracciamento errori, performance, e uso delle API. |
| **Secrets** | Secret Manager | Gestione sicura di API keys e credenziali OAuth. |

**Note Architetturali:**

- **Caching Strategy:** Richieste identiche (stesso testo + parametri) verranno servite dalla cache per 24h, riducendo latenza e costi.
- **Fallback Mechanism:** Se Vertex AI non è disponibile, il sistema restituirà un errore user-friendly e loggerà l'incidente per analisi.

## 6. Core Components Deep Dive

### 6.1. Frontend: Google Workspace Add-on
- Sviluppato in **Google Apps Script** con TypeScript per la robustezza.
- L'interfaccia utente (sidebar) sarà costruita con HTML/CSS/JS.
- Gestirà l'autenticazione OAuth2 per comunicare in modo sicuro con il nostro backend.

**Strategia di Autenticazione:**
- **Google Workspace Identity:** Gli utenti si autenticano automaticamente tramite il loro account Google aziendale.
- **Service Account con Domain-Wide Delegation:** Il backend usa un service account GCP con delega a livello di dominio per validare le richieste.
- **JWT Token Flow:** L'add-on genera un JWT firmato con l'identità dell'utente, il backend lo valida tramite Google's token verification API.
- **Session Management:** Token con scadenza di 1 ora, refresh automatico gestito dall'add-on.
- **Security:** Nessuna password o API key esposta nel frontend; tutto gestito tramite OAuth2 e service accounts GCP.

### 6.2. Backend Service: Cloud Run
- Un container Docker con un'applicazione **Python/FastAPI**, scelto per le sue performance e l'ecosistema IA.
- Sarà **stateless**: ogni richiesta API conterrà tutte le informazioni necessarie.
- **Architettura Model-Agnostic:** Sebbene la Fase 1 utilizzerà esclusivamente un **adattatore per Vertex AI (Gemini)**, il servizio sarà progettato con un **livello di astrazione** che renderà semplice in futuro aggiungere e instradare richieste ad altri fornitori di modelli (es. OpenAI, Anthropic).

**Prompt Management & Versioning:**
- I **prompt templates** saranno memorizzati come file YAML/JSON in **Cloud Storage**, separati dal codice.
- Ogni template avrà un numero di versione (es. `v1.2.3`) per consentire rollback rapidi.
- Il backend caricherà i template all'avvio e li metterà in cache in memoria.
- Gli esempi di "tone of voice" saranno organizzati per categoria (newsletter, prodotto, social) e facilmente aggiornabili senza rideploy.
- **A/B Testing:** Il sistema supporterà l'esecuzione di più versioni di prompt in parallelo per ottimizzazione continua.

**Error Handling & Reliability:**
- **Timeout Management:** Timeout di 30s per chiamate Vertex AI, con retry automatico (max 2 tentativi).
- **Graceful Degradation:** Se il caching fallisce, il sistema continua a funzionare chiamando direttamente Vertex AI.
- **Circuit Breaker:** Dopo 5 errori consecutivi da Vertex AI, il servizio entra in modalità "maintenance" per 5 minuti.

### 6.3. AI & Intelligence Layer: Vertex AI
- Useremo **Gemini 2.5 Pro** come modello di partenza, sfruttando le sue capacità avanzate di ragionamento, di seguire istruzioni e, soprattutto, multimodali (testo e immagini).

## 7. The "Mosaico" RAG Approach

"Mosaico" assembla diverse "tessere" di informazione per creare un contenuto finale ricco e coerente. In Fase 1, implementeremo due tipi di **Retrieval-Augmented Generation (RAG)**.

### 7.1. RAG for Tone of Voice (Few-Shot)
Per garantire la coerenza del brand, ogni prompt inviato a Gemini sarà automaticamente "aumentato" con esempi "gold standard" del nostro copywriting.

**Storage degli Esempi:**
- Gli esempi di tone of voice saranno memorizzati in **Cloud Storage** in formato strutturato (JSON).
- Organizzati per tipo di contenuto: `tone_of_voice/newsletter/`, `tone_of_voice/product_descriptions/`, `tone_of_voice/social/`.
- Ogni esempio include: testo, contesto, target audience, e rating di qualità.
- Il backend selezionerà automaticamente i 3-5 esempi più rilevanti basandosi sul tipo di richiesta.

**Esempio di Prompt Ingegnerizzato dal Backend:**
```
### ISTRUZIONI DI SISTEMA ###
Sei un copywriter esperto per il brand [NOME_AZIENDA]. Il tuo stile deve rispecchiare esattamente gli esempi forniti di seguito.

### ESEMPI DI TONE OF VOICE ###
Esempio 1: "✨ Pronta a brillare? La nostra collezione estiva ti aspetta."
Esempio 2: "Ciao [Nome], non è solo il sole a splendere oggi. Abbiamo appena lanciato qualcosa di speciale..."
Esempio 3: "Scoprila subito ->"

### RICHIESTA UTENTE ###
Crea 3 variazioni per il titolo: "Nuova collezione di borse in pelle"
```

### 7.2. RAG from Product Images (Multimodal)
Sfrutteremo le capacità multimodali di Gemini per eliminare il context-switching per i copywriter.
- L'utente inserirà un URL di immagine in una cella.
- Il backend invierà l'immagine e un'istruzione testuale a Gemini.
- Gemini "vedrà" il prodotto e genererà una descrizione testuale basata sulle sue caratteristiche visive.

## 8. API Endpoints (Phase 1)

Il backend su Cloud Run esporrà i seguenti endpoint:

- `POST /auth/google`: Gestisce il flusso di login OAuth2.
- `POST /api/v1/generate`: Endpoint generico per creare variazioni, cambiare tono, ecc.
- `POST /api/v1/translate`: Per le traduzioni.
- `POST /api/v1/refine`: Per correzioni e miglioramenti stilistici.
- `POST /api/v1/generate-from-image`: Accetta un URL di immagine e un'istruzione.

**Esempio Request Body per `/api/v1/generate`:**
```json
{
  "task": "CREATE_VARIATIONS",
  "source_text": "Scopri la nostra nuova collezione estiva.",
  "params": {
    "count": 3,
    "tone": "entusiasta"
  },
  "context": {
    "product_name": "Sandali 'Riviera'",
    "target_audience": "Donne 25-40"
  }
}
```

## 9. Cost Model & Budget Estimates

**Assunzioni:**
- 10 utenti attivi
- Utilizzo medio: 20 richieste/utente/giorno lavorativo (22 giorni/mese)
- Total richieste/mese: ~4.400

| Componente | Costo Mensile Stimato | Note |
| :--- | :--- | :--- |
| **Vertex AI (Gemini 2.5 Pro)** | $70-100 | ~$0.02 per richiesta (input + output tokens). Cache riduce del 30%. |
| **Cloud Run** | $5-10 | 1M richieste gratuite/mese, poi $0.40 per 1M. |
| **Cloud Memorystore (Redis)** | $25-40 | Istanza Basic da 1GB (configurazione minima). |
| **Cloud Storage** | $5-10 | Storage per prompt templates e esempi (~10GB). |
| **Cloud Logging & Monitoring** | $5-10 | Log retention 30 giorni. |
| **Networking & Egress** | $5-10 | Trasferimento dati in uscita. |
| **TOTALE STIMATO** | **$115-180/mese** | **~$11-18/utente/mese** |

**Strategie di Ottimizzazione Costi:**
- **Caching aggressivo:** Riduce del 30-40% le chiamate a Vertex AI.
- **Prompt optimization:** Ridurre i token di input/output del 20% può dimezzare i costi Vertex AI.
- **Tiered usage:** Implementare quote per utente (es. 100 richieste/mese gratuite, poi pay-per-use).
- **Model selection:** Usare Gemini Flash per richieste semplici (80% più economico).

**Budget Alert:** Configureremo Cloud Billing alerts a $150, $200 e $250/mese.

## 10. Out of Scope for Phase 1
- Una piattaforma web autonoma.
- Un database persistente per salvare la cronologia dei contenuti.
- Dashboard di analytics e performance dei contenuti.
- Flussi di approvazione complessi.

## 11. Next Steps

### Fase 1.1: Infrastructure Setup
1.  **Setup Progetto GCP:**
    - Creare progetto GCP e abilitare le API necessarie (Cloud Run, Vertex AI, Memorystore, Storage, Logging).
    - Configurare Identity & Access Management (IAM) e service accounts.
    - Impostare Cloud Billing alerts ($150, $200, $250/mese).
2.  **Configurazione Storage:**
    - Creare bucket Cloud Storage per prompt templates e esempi tone of voice.
    - Definire struttura delle directory (`prompts/v1/`, `tone_of_voice/newsletter/`, ecc.).
    - Caricare i primi 10-15 esempi "gold standard" del brand.
3.  **Setup Monitoring:**
    - Configurare Cloud Logging workspaces.
    - Creare dashboard personalizzate in Cloud Monitoring per tracciare latenza, errori, e uso API.

### Fase 1.2: Backend Development
4.  **Sviluppo Core Backend:**
    - Creare servizio FastAPI su Cloud Run con struttura model-agnostic.
    - Implementare adattatore per Vertex AI (Gemini 2.5 Pro).
    - Sviluppare sistema di prompt management con caricamento da Cloud Storage.
5.  **Implementazione Features:**
    - Endpoint `/api/v1/generate` con RAG per tone of voice.
    - Sistema di caching con Cloud Memorystore.
    - Error handling con retry logic e circuit breaker.
6.  **Testing & Security:**
    - Unit tests per prompt engineering e adattatori AI.
    - Integration tests per flusso end-to-end.
    - Security review: autenticazione, rate limiting, input validation.

### Fase 1.3: Frontend Development
7.  **Sviluppo Google Workspace Add-on:**
    - Scheletro dell'add-on con Google Apps Script (TypeScript).
    - UI/sidebar con HTML/CSS/JS moderno e responsive.
    - Implementazione OAuth2 flow per comunicazione con backend.
8.  **Features UI:**
    - Modalità Preview con possibilità di rigenerare.
    - Sistema di feedback (👍/👎) integrato.
    - Gestione errori user-friendly.

### Fase 1.4: Integration & Testing
9.  **Integrazione End-to-End:**
    - Implementare la prima feature completa: Generatore di Variazioni Creative.
    - Test del flusso completo: autenticazione → richiesta → caching → Vertex AI → risposta → UI.
10. **Quality Assurance:**
    - Test di coerenza del brand voice con panel interno.
    - Performance testing: latenza, throughput, fallback mechanisms.
    - Cost validation: verificare che i costi reali siano allineati alle stime.

### Fase 1.5: Alpha Release
11. **Alpha Test:**
    - Rilascio a 5-10 utenti selezionati dal team newsletter.
    - Raccolta feedback strutturato (survey + interviste).
    - Monitoraggio metrics: adoption rate, quality scores, error rate.
12. **Iteration:**
    - Ottimizzazione prompt basata su feedback qualitativo.
    - Fix bug critici e miglioramenti UX.
    - Preparazione per beta release estesa.
