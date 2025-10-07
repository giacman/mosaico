<script setup>
import {computed} from 'vue'
import { UseClipboard } from '@vueuse/components'
import {json2csv} from "json-2-csv";

const props = defineProps({
  content:     { required: true },
  css_class:      {type: String, default: ""},
  showDownload:   {type: Boolean, default: false},
})

// Cambia source da ref a computed
const source = computed(() => {
  if (!props.content) return null;

  let translations = [
    {
      "lang": props.content.language.lang_alpha2.toUpperCase(),
      "data": props.content.data,
    }
  ]

  for(const translation of props.content.translations) {
    if(translation.status === "validata"){
      translations.push({
        "lang": translation.language.lang_alpha2.toUpperCase(),
        "data": translation.data,
      })
    }
  }

  return buildMergedTemplate(translations)
})

// Computed per il CSV con normalizzazione UTF-8
const csvSource = computed(() => {
  try {
    const csvData = source.value ? json2csv(source.value, {expandArrayObjects: true}) : ''
    // Normalizza la stringa UTF-8 per compatibilità
    return csvData.normalize('NFC')
  } catch (error) {
    console.error('Errore nella conversione CSV:', error)
    return ''
  }
})

// Funzione per scaricare il CSV
const downloadCsv = () => {
  if (!csvSource.value) {
    console.warn('Nessun contenuto CSV da scaricare')
    return
  }

  // Aggiunge BOM UTF-8 per garantire la corretta codifica nei programmi che lo richiedono (come Excel)
  const csvWithBOM = '\uFEFF' + csvSource.value
  const blob = new Blob([csvWithBOM], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = `${props.content?.title}_handlebar.csv`
  link.style.display = 'none'

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}

/**
 * Costruisce per ogni campo stringa un'espressione Handlebars condizionale
 * che seleziona il testo in base a selected_language, con fallback.
 *
 * @param {Array<{ lang: string, data: any }>} translations - lista di oggetti con champi lang e data
 * @param {string} defaultLang - lingua di fallback (es. 'EN')
 * @returns {any} - JSON con la stessa struttura ma valori = condizionali handlebars
 */
function buildMergedTemplate(translations, defaultLang = 'EN') {
  if (!Array.isArray(translations) || translations.length === 0) {
    throw new Error('At least one translation');
  }

  // Mappa lang -> data
  const map = {};
  for (const t of translations) {
    if (!t.lang || t.data === undefined) continue;
    map[t.lang.toUpperCase()] = t.data;
  }

  // Determina lingua di fallback: se defaultLang presente, altrimenti la prima disponibile
  const fallbackLang = map[defaultLang.toUpperCase()] ? defaultLang.toUpperCase() : Object.keys(map)[0];

  // Ordine: mettere fallback alla fine
  const langs = Object.keys(map).filter(l => l !== fallbackLang);
  langs.push(fallbackLang); // fallback last

  // Ricorsione su struttura (prende la struttura dalla traduzione di fallback per sicurezza)
  function recurse(...nodes) {
    // nodes corrispondono ai relativi punti nella struttura per ciascuna lingua, in ordine langs
    const first = nodes[0];
    if (typeof first === 'string' || typeof first === 'number' || typeof first === 'boolean' || first === null) {
      // Leaf primitivo: costruisci condizionale
      // Solo per stringhe ha senso condizione; per altri tipi serializziamo fallback direttamente
      if (typeof first !== 'string') {
        // Non-stringa: usiamo il valore di fallback senza condizionale
        return nodes[langs.length - 1];
      }

      // Costruisci espressione tipo: {{#eq selected_language "IT"}}...{{else eq selected_language "FR"}}...{{else}}fallback{{/eq}}
      let cond = '';
      for (let i = 0; i < langs.length; i++) {
        const lang = langs[i];
        const value = (map[lang] ? nodes[i] : undefined);
        if (i === 0) {
          // primo ramo: usa #eq - CORREZIONE: aggiunti i backtick
          cond += `{{#eq selected_language "${lang}"}}${escapeHandlebars(value)}`;
        } else if (i === langs.length - 1) {
          // fallback: else
          cond += `{{else}}${escapeHandlebars(value)}`;
        } else {
          cond += `{{else eq selected_language "${lang}"}}${escapeHandlebars(value)}`;
        }
      }
      cond += `{{/eq}}`;
      return cond;
    }

    if (Array.isArray(first)) {
      // Supponiamo array con struttura parallela: ricorsione per indice
      const length = first.length;
      const result = [];
      for (let idx = 0; idx < length; idx++) {
        const childNodes = nodes.map(n => (Array.isArray(n) ? n[idx] : undefined));
        result.push(recurse(...childNodes));
      }
      return result;
    }

    if (typeof first === 'object' && first !== null) {
      const result = {};
      // Per ogni chiave nella struttura di fallback (ultima lingua)
      const keys = Object.keys(first);
      for (const key of keys) {
        const childNodes = langs.map(lang => {
          const dataNode = map[lang];
          return dataNode && key in dataNode ? dataNode[key] : undefined;
        });
        result[key] = recurse(...childNodes);
      }
      return result;
    }

    // Default: ritorna fallback
    return nodes[langs.length - 1];
  }

  // Helper per scappare eventuali delimitatori che confliggono se serve (qui semplice)
  function escapeHandlebars(str) {
    if (str == null) return '';
    // Assumiamo che il contenuto non abbia logica handlebars; se serve, si può estendere.
    return String(str);
  }

  // Avvia ricorsione a partire dalla struttura di fallback
  const fallbackData = map[fallbackLang];
  const nodesStart = langs.map(lang => map[lang]); // array di root per ogni lingua nell'ordine langs

  return recurse(...nodesStart);
}
</script>

<template>
  <div class="csv-actions d-flex align-items-center">
    <!-- Pulsante Copia -->
    <UseClipboard v-slot="{ copy, copied }" :source="csvSource">
      <button
          @click="copy()"
          role="button"
          class="btn btn-primary fw-bold text-uppercase"
          :class="css_class"
          :title="'Copy Handlebar CSV in clipboard'"
      >
        <span v-if="!copied" class=" fw-bold text-uppercase d-flex align-items-center">
          <IconFasCopy class="me-2"/>
          Handlebar CSV
        </span>
        <span  v-else class="fw-bold text-uppercase d-flex align-items-center">
          <IconFasCheck class="me-2"/>
          Copied
        </span>

      </button>
    </UseClipboard>

    <button v-if="showDownload"
            @click="downloadCsv()"
            role="button"
            :class="css_class"
            :title="'Download Handlebar CSV File'"
            class="btn btn-primary fw-bold text-uppercase ms-2 d-flex align-items-center"
    >
      <IconFasDownload class="me-2"/>
      Handlebar CSV
    </button>
  </div>
</template>

<style scoped>
</style>