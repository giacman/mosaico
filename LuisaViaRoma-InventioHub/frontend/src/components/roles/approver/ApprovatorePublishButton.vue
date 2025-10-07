<script setup lang="js">

import {auth_fetch, error_message} from "@/utils.js";
import {useToast} from "primevue/usetoast";
import {useConfirm} from "primevue/useconfirm";
import {inject} from "vue";

const confirm = useConfirm();
const toast = useToast();
const refreshContents = inject('refreshContents');
const props = defineProps({
  content_id: {required: true},
})

const emit = defineEmits(['published']);

async function fetchPublishContent() {
  try {
    const response = await auth_fetch(
        `/api/publish_content/${props.content_id}/`,
        {method: 'PUT'}
    );
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    toast.add({severity: 'success', summary: 'Published', detail: 'Content published!', life: 3000});
    emit('published', {contentId: props.content_id});
    refreshContents()
  } catch (err) {
    toast.add({severity: 'error', summary: 'Error', detail: err.message || "Connection error", life: 3000});
  }
}

function onClick() {
  const baseOptions = {
    group: 'firstConfirmDialog',
    header: 'Publish?',
    rejectProps: {
      icon: 'pi pi-times',
      label: 'Cancel',
      severity: 'secondary',
      outlined: true
    },
    acceptProps: {
      label: 'Publish',
      severity: 'success',
      icon: 'pi pi-thumbs-up-fill'
    },
  };

  confirm.require({
    ...baseOptions,

    message: 'Do you want to publish this content?',
    icon: 'pi pi-question-circle',
    accept: () => {
      fetchPublishContent()
    },
    reject: () => {
    }
  })
}

</script>

<template>
  <button class="btn btn-success me-2 fw-bold text-uppercase"
          @click="onClick">
    <IconFasCloudUploadAlt class="me-1"/>
    Publish
  </button>

</template>

<style scoped>

</style>