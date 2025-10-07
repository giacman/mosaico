<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { Popover } from 'bootstrap'
import { UseClipboard } from '@vueuse/components'


const props = defineProps({
  source:     { required: true },
  css_class:      {type: String, default: ""},
})



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

</script>

<template>
  <UseClipboard v-slot="{ copy, copied }" :source="(!Array.isArray(source) && source !== null && typeof source === 'object') ? JSON.stringify(source, null, 2) : source">
    <a ref="popoverTrigger"
       @click="copy()"
       tabindex="-1"
       role="button"
       data-bs-toggle="popover"
       data-bs-trigger="focus"
       data-bs-placement="right"
       data-bs-custom-class="custom-copied-popover"
       :data-bs-content="(!Array.isArray(source) && source !== null && typeof source === 'object') ? 'Copied in JSON!' : 'Copied!'"
       :class="css_class"
    >
      <IconFasCopy v-if="!copied" class="me-2"/>
      <IconFasCheck v-else class=""/>
    </a>
  </UseClipboard>
</template>

<style scoped>

</style>