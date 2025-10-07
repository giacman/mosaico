<script setup>

import {useStore} from "@/utils.js";

import {onMounted, ref} from "vue";

import CopyClipboard from "@/components/utils/CopyClipboard.vue";
import JSONViewer from "@/components/json/JSONViewer.vue";
import GenerationInputs from "@/components/generation/GenerationInputs.vue";
import TranslationInputs from "@/components/translations/TranslationInputs.vue";
import TranslationLanguageController from "@/components/translations/TranslationLanguageController.vue";
import TranslationStatusCarousel from "@/components/translations/TranslationStatusCarousel.vue";
import TranslationEditorCarousel from "@/components/translations/TranslationEditorCarousel.vue";
import TranslationViewerCarousel from "@/components/translations/TranslationViewerCarousel.vue";
import CopyCSVClipboard from "@/components/utils/CopyCSVClipboard.vue";

const store = useStore()

let schema = ref(null);

const content = defineModel("content", {type: Object, required: true})

onMounted(() => {
  if (content.value.schema) schema.value = JSON.parse(JSON.stringify(content.value.schema));
})

</script>

<template>
  <div v-if="content" class="container-fluid p-3 px-lg-5">
    <div class="row">
      <div class="col-6 p-0 pe-2 pe-lg-4">
        <GenerationInputs :content="content"></GenerationInputs>
      </div>
      <div class="col-6 p-0 ps-2 ps-lg-4">

        <TranslationInputs
            v-if="store.role==='copywriter' && ['bozza_validata','review_traduzioni','bozza_rifiutata'].includes(content.status)"
            :content="content"></TranslationInputs>

        <div class="mt-3">
          <TranslationLanguageController :translations="content.translations"></TranslationLanguageController>
        </div>

        <TranslationStatusCarousel :translations="content.translations"></TranslationStatusCarousel>

      </div>
    </div>
    <div v-if="content.state === 'failed' " class="container-fluid p-4">
      {{ content.state_message }}
    </div>

    <div class="row mt-5">

      <div class="col-6 p-0 pe-2 pe-lg-4">
        <span class="d-flex align-items-center">
          <span class="display-6 text-body-tertiary fw-bold">
            Content Data
          </span>
          <template v-if="content?.state === 'success'">
            <CopyClipboard
                :source="content?.data"
                :css_class="'fs-4 ms-3 text-black'"
            />
            <CopyCSVClipboard
                :source="content?.data"
                :css_class="'fs-4 ms-3 text-black'"
                :filename="`${content?.id}_${content?.language?.name}.csv`"
                :show-download="true"
            />
          </template>
        </span>
        <div class="px-4 py-3 my-2 border border-1 rounded shadow-sm">
          <JSONViewer :data="content.data" :schema="content.schema"/>
        </div>
      </div>

      <div class="col-6 p-0 ps-2 ps-lg-4">
        <template v-if="content.translations?.length > 0 && schema">
          <TranslationViewerCarousel
              v-if="content.status==='pubblicata'"
              v-model:translations="content.translations"
              :schema="content.schema"
          />
          <TranslationEditorCarousel
              v-else
              v-model:translations="content.translations"
              :schema="content.schema"
              :view-mode="content.status !== 'review_traduzioni'"
          />
        </template>

      </div>
    </div>


  </div>
</template>

<style scoped>

.input-values label {
  color: var(--bs-tertiary-color);
  font-weight: bold;
}

.input-values p, .input-values p span {
  font-weight: bold;
}
</style>