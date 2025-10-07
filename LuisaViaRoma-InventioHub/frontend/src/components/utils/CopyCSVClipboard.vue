<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { Popover } from 'bootstrap'
import { UseClipboard } from '@vueuse/components'
import { json2csv } from 'json-2-csv';

const props = defineProps({
  source:      { required: true },
  css_class:      {type: String, default: ""},
  filename:       { type:String, required: true },
  showDownload:   {type: Boolean, required: true},
})

const sourceToCopy = computed(() => {
  if (!props.source) return null;

  // Se è un oggetto (ma non array), convertilo in CSV
  if (!Array.isArray(props.source) &&
      props.source !== null &&
      typeof props.source === 'object') {
    return json2csv(props.source, {expandArrayObjects: true});
  }

  // Altrimenti restituisci così com'è (array o stringa)
  return props.source;
});

// --- POPPER / POPOVER SETUP ---
const popoverTrigger = ref(null)
let popoverInstance = null

onMounted(() => {
  // aspetta che il DOM sia aggiornato
  nextTick(() => {
    if (popoverTrigger.value) {
      popoverInstance = new Popover(popoverTrigger.value, {
        trigger: 'focus'
      })
    }
  })
})

onBeforeUnmount(() => {
  // pulisci per evitare memory leak
  if (popoverInstance) {
    popoverInstance.dispose()
    popoverInstance = null
  }
})

// Funzione per scaricare il CSV
const downloadCsv = () => {
  if (!sourceToCopy.value) {
    console.warn('Nessun contenuto CSV da scaricare')
    return
  }

  const blob = new Blob([sourceToCopy.value], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = `${props.filename}`
  link.style.display = 'none'

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}

</script>

<template>
  <UseClipboard v-slot="{ copy, copied }" :source="sourceToCopy">
    <a ref="popoverTrigger"
       @click="copy()"
       tabindex="-1"
       role="button"
       data-bs-toggle="popover"
       data-bs-trigger="focus"
       data-bs-placement="right"
       data-bs-custom-class="custom-copied-popover"
       data-bs-content="Copied in CSV!"
       :class="css_class"
    >
      <IconFasFileCsv v-if="!copied" class="me-2"/>
      <IconFasCheck v-else class=""/>
    </a>

    <a v-if="showDownload"
       @click="downloadCsv()"
       role="button"
       :class="css_class"
       :title="'Download CSV File'"
       class="ms-2"
    >
      <IconFasDownload class=""/>
    </a>
  </UseClipboard>
</template>

<style scoped>

</style>