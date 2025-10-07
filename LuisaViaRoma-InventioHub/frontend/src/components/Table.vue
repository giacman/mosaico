<script setup lang="ts">
import { onMounted, watch, nextTick } from 'vue'
import {openContentModal} from '@/utils.js';

const props = defineProps({
  contents: Array
});

let hasRun = false;

watch(() => props.contents, async (newContents) => {
	if (!hasRun && newContents && newContents.length > 0) {
		hasRun = true;
		await nextTick(); // wait for DOM to update
    openContentModal();
	}
});

</script>

<template>
  <div class="lvr-content-table table-responsive border border-1 rounded m-auto shadow-sm">
    <table class="table table-striped table-hover cursor-pointer m-auto">
      <thead >
      <slot name="header"/>
      </thead>
      <tbody class="table-group-divider">
      <template v-for="content in contents" :key="content.id">
        <slot name="row" :content="content" />
      </template>
      </tbody>
    </table>
  </div>

  <template v-for="(content, idx) in contents" :key="content.id">
    <div
        class="content-modal modal fade"
        :id="'staticBackdrop-' + content.id"
        data-bs-backdrop="static"
        data-bs-keyboard="false"
        data-bs-focus="false"
        tabindex="-1"
        :aria-labelledby="'staticBackdropLabel-' + content.id"
        aria-hidden="true"
    >
      <div class="modal-dialog modal-fullscreen p-5 modal-dialog-scrollable modal-dialog-centered">
        <div class="modal-content border border-2 border-secondary rounded">
          <div class="modal-header">
            <h1 class="modal-title fs-5" :id="'staticBackdropLabel-' + content.id">
              {{ content.title }}
            </h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
          </div>
          <div class="modal-body">

            <slot name="modal-body" :content="content" :index="idx" />
          </div>
          <div class="modal-footer">
            <!-- Slot footer del modal obbligatorio -->
            <slot name="modal-footer" :content="content" />
          </div>
        </div>
      </div>
    </div>
  </template>
</template>

<style scoped>

</style>
