<script setup>
import {computed, onMounted, ref, watch} from 'vue'
import {useCarouselController} from '@/stores/useCarouselStore.js'
import Multiselect from 'vue-multiselect'
import {auth_fetch, error_message, getAIStateClassColor, getAIStateLabel, useStore,} from "@/utils.js";

import {useToast} from "primevue/usetoast";
import {
  getTranslationStatusClassColor,
  getTranslationStatusLabel
} from "@/components/translations/translation_utils.js";
import Dialog from "primevue/dialog";

const toast = useToast();
const store = useStore();

const retryCustomPrompt = ref('')
const isRetrying = ref(false);

const props = defineProps({
  translations: {type: Array, default: () => []}
})

const {currentSlide} = useCarouselController()

// Ricavo un array di option con tutti i campi utili
const options = ref([])


watch(() => props.translations, val => {
  options.value = props.translations.map(t => ({
    ...t.language, ...{
      complete_name: `${t.language.name} (${t.language.lang_alpha2}-${t.language.country_alpha2})`,
      state: t.state,
      status: t.status
    }
  }))
}, {immediate: true, deep: true})

onMounted(() => {
  options.value = props.translations.map(t => ({
    ...t.language, ...{
      complete_name: `${t.language.name} (${t.language.lang_alpha2}-${t.language.country_alpha2})`,
      state: t.state,
      status: t.status
    }
  }))
})

const selectedOption = computed({
  get() {
    return options.value[currentSlide.value] ?? options.value[0] ?? null
  },
  set(opt) {
    const idx = options.value.findIndex(o => o.complete_name === opt.complete_name)
    if (idx !== -1) currentSlide.value = idx
  }
})

async function retryTranslation() {
  const currentTranslation = props.translations[currentSlide.value]

  if (currentTranslation.status === "validata" && currentTranslation.state === "pending")
    return

  try {
    const res = await auth_fetch(`/api/retry_translation/`, {
      method: 'PUT',
      body: JSON.stringify({
        "trans_id": currentTranslation.id,
        "retry_custom_prompt": retryCustomPrompt.value,
      })
    })

    if (!res.ok) {
      const err = await error_message(res)
      toast.add({severity: 'error', summary: 'Rejected', detail: err.message || "Fatal error", life: 3000});
      return
    }
    toast.add({severity: 'success', summary: 'Confirmed', detail: "Retry translation", life: 3000});
  } catch (err) {
    toast.add({severity: 'error', summary: 'Rejected', detail: err.message || "Fatal error", life: 3000});
  }
  isRetrying.value = false
}
</script>

<template>
  <Dialog v-model:visible="isRetrying" modal header="Retrying..." :style="{ width: '25rem' }" appendTo="body"
          :baseZIndex="1500" tabindex="-1">
    <div class="mb-3">
      <label for="rejectionMessage" class="form-label">Give AI retry instructions:</label>
      <textarea
          id="rejectionMessage"
          class="form-control w-100"
          v-model="retryCustomPrompt"
          placeholder="Leave empty if you want to do a simple retry..."
      ></textarea>
    </div>
    <div class="d-flex justify-content-end gap-2">
      <button
          type="button"
          class="btn btn-outline-secondary rounded"
          @click="isRetrying = false"
      >Cancel
      </button>
      <button
          type="button"
          class="btn btn-warning"
          @click="retryTranslation"
      >
        <IconFa6SolidArrowRotateLeft/>
        Retry
      </button>
    </div>
  </Dialog>


  <div class="mb-3">
    <label class="form-label text-body-tertiary fw-bold mb-1">
      Select a translation:
    </label>
    <div class="d-flex align-items-center flex-nowrap">
      <Multiselect
          class="shadow-sm"
          v-model="selectedOption"
          :options="options"
          track-by="complete_name"
          label="complete_name"
          :searchable=false
          :allow-empty=false
          :close-on-select=true
          :hide-selected=true
      >
        <template #singleLabel="{ option }">
          <span :class="['fi fis rounded-circle me-2', 'fi-'+option.country_alpha2.toLowerCase()]"/>
          <span>{{ option.complete_name }}</span>
        </template>

        <template #option="{ option }">
          <span :class="['fi fis rounded-circle me-2', 'fi-'+option.country_alpha2.toLowerCase()]"/>
          <span class="option__title me-2">{{ option.complete_name }}</span>
          <span class="badge ms-2 text-uppercase"
                :class="getTranslationStatusClassColor(option.status)">{{
              getTranslationStatusLabel(option.status)
            }}</span>
          <span class="badge ms-2 text-uppercase"
                :class="getAIStateClassColor(option.state)">{{ getAIStateLabel(option.state) }}</span>
        </template>
      </Multiselect>

      <button
          v-if="store.role === 'traduttore'"
          :disabled="translations[currentSlide]?.status === 'validata' || translations[currentSlide]?.state === 'pending'"
          @click="isRetrying = true"
          class="ms-2 btn btn-warning flex-shrink-0 text-nowrap text-uppercase fw-bold"
      >
        <IconFa6SolidArrowRotateLeft/>
        Retry

      </button>
    </div>


  </div>
</template>


<style scoped>
.multiselect__option--highlight {
  background: inherit !important;
  outline: none;
  color: inherit !important;
}
</style>
