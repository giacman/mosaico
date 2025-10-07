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
      "language": props.content.language.lang_alpha2.toUpperCase(),
      ...props.content.data
    }
  ]

  for(const translation of props.content.translations) {
    translations.push({
      "language": translation.language.lang_alpha2.toUpperCase(),
      ...translation.data,
    })
  }
  return translations
})

// Computed per il CSV (senza BOM per il copy)
const csvSource = computed(() => {
  try {
    return source.value ? json2csv(source.value, {expandArrayObjects: true}) : ''
  } catch (error) {
    console.error('Errore nella conversione CSV:', error)
    return ''
  }
})

// Computed per il CSV con BOM UTF-8 per il copy
const csvSourceWithBOM = computed(() => {
  return csvSource.value ? '\uFEFF' + csvSource.value : ''
})

// Funzione per scaricare il CSV
const downloadCsv = () => {
  if (!csvSource.value) {
    console.warn('Nessun contenuto CSV da scaricare')
    return
  }

  // Aggiunge BOM UTF-8 per garantire la corretta codifica
  const csvWithBOM = '\uFEFF' + csvSource.value
  const blob = new Blob([csvWithBOM], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = `${props.content?.title}.csv`
  link.style.display = 'none'

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}

</script>

<template>
  <div class="csv-actions d-flex align-items-center">
    <!-- Pulsante Copia -->
    <UseClipboard v-slot="{ copy, copied }" :source="csvSourceWithBOM">
      <button
          @click="copy()"
          role="button"
          class="btn btn-primary fw-bold text-uppercase"
          :class="css_class"
          :title="'Copy Handlebar CSV in clipboard'"
      >
        <span v-if="!copied" class=" fw-bold text-uppercase d-flex align-items-center">
          <IconFasCopy class="me-2"/>
          Content CSV
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
      Content CSV
    </button>
  </div>
</template>

<style scoped>
</style>