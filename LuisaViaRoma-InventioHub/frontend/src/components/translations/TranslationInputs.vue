<script setup>
import {computed, onMounted, ref, watch} from 'vue'
import Multiselect from 'vue-multiselect'
import {auth_fetch, error_message} from '@/utils.js'
import {useToast} from "primevue/usetoast";


const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  content: {
    type: Object,
    required: true
  }
})

const toast = useToast();

const emit = defineEmits(['update:modelValue'])

const options = ref([])
const selectedLangs = ref(props.modelValue)
const submitted = ref(false)
const canSubmit = computed(() =>
    selectedLangs.value.length > 0
)

watch(selectedLangs, v => emit('update:modelValue', v))

onMounted(async () => {
  try {
    options.value = await retrieveActiveLanguages()
  } catch (e) {
    console.error('Errore nel caricamento delle lingue:', e)
  }
})


async function retrieveActiveLanguages() {
  try {
    const response = await auth_fetch('/api/get_languages/', {method: 'GET'}, false)
    if (!response.ok) {
      console.error(await error_message(response))
      return []
    }
    const langs = await response.json()
    return langs.map(l => ({complete_name: `${l.name} (${l.lang_alpha2}-${l.country_alpha2})`, ...l}))

  } catch (err) {
    toast.add({severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000});
  }
}

// invio delle traduzioni selezionate
async function submitTranslations() {
  submitted.value = true

  // validazione: almeno una lingua
  if (!canSubmit.value) {
    return
  }

  const payload = {
    content_id: props.content.id,
    language_ids: selectedLangs.value.map(l => l.id)
  }

  try {
    const res = await auth_fetch('/api/translate_content/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    })

    if (!res.ok) {
      const err = await error_message(res)
      toast.add({severity: 'error', summary: 'Rejected', detail: err.message || "Fatal error", life: 3000});
      return
    }

    // successo: resetto lo stato
    selectedLangs.value = []
    submitted.value = false

    toast.add({severity: 'success', summary: 'Confirmed', detail: "Translation sent to AI", life: 3000});
  } catch (err) {
    toast.add({severity: 'error', summary: 'Rejected', detail: err.message || "Fatal error", life: 3000});
  }
}
</script>

<template>
  <div>
    <label class="form-label text-body-tertiary fw-bold">
      Select translation languages
    </label>
    <div class="d-flex align-items-center flex-nowrap">
      <Multiselect
          class="flex-grow-1 me-2 shadow-sm"
          v-model="selectedLangs"
          :options="options"
          :multiple=true
          :close-on-select=false
          :clear-on-select=false
          :preserve-search=true
          :hide-selected=true
          placeholder="Choose languages"
          label="complete_name"
          track-by="complete_name"
          :preselect-first=false
      >
        <template #option="{ option }">
        <span
            class="fi me-2 fis rounded-circle"
            :class="'fi-' + option.country_alpha2.toLowerCase()"
        ></span>
          <span>{{ option.complete_name }}</span>
        </template>
        <template #tag="{ option, remove }">
        <span class="multiselect__tag py-1" :key="option.id">
          <span
              class="fi me-2 fis rounded-circle"
              :class="'fi-' + option.country_alpha2.toLowerCase()"
          ></span>
          {{ option.complete_name }}
          <i
              class="multiselect__tag-icon"
              @mousedown.prevent="remove(option)"
              @keypress.enter.prevent="remove(option)"
              tabindex="-1"
          ></i>
        </span>
        </template>
      </Multiselect>

      <button
          :disabled="!canSubmit"
          @click="submitTranslations"
          class="btn btn-primary flex-shrink-0 text-nowrap text-uppercase fw-bold"
      >
        <IconFasLanguage/>
        Translate
      </button>
    </div>


    <div v-if="submitted && !canSubmit" class="text-danger mt-1">
      Seleziona almeno una lingua prima di procedere.
    </div>


  </div>
</template>

<style scoped>

</style>