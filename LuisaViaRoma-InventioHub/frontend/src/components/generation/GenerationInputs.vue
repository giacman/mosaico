<script setup>

import {download_s3_file, useStore} from "@/utils.js";

const props = defineProps({
  content: { type: Object, required: true },
});

const store = useStore()

</script>

<template>
  <div class="container-fluid input-values mb-5">
    <div class="row">
      <div class="col">
        <label>Content</label>
        <p>
          {{ content.content_type }}
        </p>
      </div>
      <div class="col">
        <label>Type</label>
        <p>
          {{content.data?.type || "-"}}
        </p>
      </div>
      <div class="col">
        <label>Language</label>
        <div>
          <span class="fi me-2 fis rounded-circle" :class="'fi-' + content.language?.country_alpha2?.toLowerCase()"></span>
          <span class="fw-bold">{{ content.language?.name }} ({{content.language?.lang_alpha2}}-{{content.language?.country_alpha2}})</span>
        </div>
      </div>
      <div class="col">
        <label>LLM Name</label>
        <p>{{ content.selected_llmmodel?.name }}</p>
      </div>
    </div>
    <div class="row">
      <div class="d-flex flex-column col col-lg-6">
        <label>
          Custom Prompt
        </label>
        <div class="border rounded py-3 px-4 ms-2 shadow-sm bg-body">
          {{ content?.custom_prompt || "-"}}
        </div>
      </div>
      <div class="col col-lg-6">
        <label>
          Files
        </label>
        <div v-if="content.s3files?.length > 0" class="ms-2 list-group list-group-numbered shadow-sm">
          <template v-for="file in content.s3files">
            <button v-if="file.name && file.name !== ''"
                    class="list-group-item list-group-item-action d-flex align-items-center bg-body"
                    @click="download_s3_file(store, file.name, file.key)">
              <span class="d-inline-block ms-2 text-black text-truncate">{{file.name}}</span>
              <IconFasDownload class="ms-auto"/>
            </button>
          </template>
        </div>
        <div v-else>-</div>
      </div>
    </div>
  </div>

</template>

<style scoped>
  label {
    color: var(--bs-tertiary-color);
    font-weight: bold;
  }

  p, p span {
    font-weight: bold;
  }
</style>