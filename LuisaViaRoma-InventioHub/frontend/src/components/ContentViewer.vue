<script setup>

import {ref, onMounted} from 'vue'
import {
  useStore,
} from '../utils';
import CopyClipboard from "@/components/utils/CopyClipboard.vue";
import GenerationInputs from "@/components/generation/GenerationInputs.vue";
import JSONViewer from "@/components/json/JSONViewer.vue";
import CopyCSVClipboard from "@/components/utils/CopyCSVClipboard.vue";


const store = useStore()
let schema = ref(null);

const props = defineProps({
  content: Object,
});


onMounted(() => {
  store.role = localStorage.getItem("role");
  if (props.content.schema) schema.value = JSON.parse(JSON.stringify(props.content.schema));
})

</script>

<template>
  <div class="container-fluid p-4">

    <GenerationInputs :content="content"></GenerationInputs>

    <!-- Messaggio di bozza rifiutata -->
    <div
        v-if="content.status === 'bozza_rifiutata'"
        class="alert alert-warning d-flex align-items-start p-4 mb-4"
        role="alert"
    >
      <IconFa6SolidTriangleExclamation class="fs-2 me-3"/>
      <div>
        <h6 class="alert-heading mb-1">Rejected Draft</h6>
        <p class="mb-0">{{ content.rejection_message }}</p>
      </div>
    </div>

    <!-- Messaggio di errore generazione AI -->
    <div
        v-if="content.state === 'failed'"
        class="alert alert-danger d-flex align-items-start p-4"
        role="alert"
    >
      <IconFa6SolidTriangleExclamation class="fs-2 me-3"/>
      <div>
        <h6 class="alert-heading mb-1">AI Error</h6>
        <p class="mb-0">{{ content.state_message }}</p>
      </div>
    </div>


    <div class="container-fluid">
    <span class="d-flex align-items-center">
      <span class="display-6 text-body-tertiary fw-bold">
      Content Data
    </span>
      <template  v-if="content?.state === 'success'">
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
      <div class="px-4 py-3 my-2 border borser-1 rounded shadow-sm bg-body">
        <JSONViewer :data="content.data" :schema="content.schema"/>
      </div>
    </div>

  </div>
</template>

<style scoped>


</style>
