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

const emit = defineEmits(['approve']);

async function fetchApproveContent() {
  try {
    const response = await auth_fetch(
        `/api/approve_content/${props.content_id}/`,
        {method: 'PUT'}
    );
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    toast.add({severity: 'success', summary: 'Approved', detail: 'Content approved!', life: 3000});
    emit('approve', {contentId: props.content_id});
    refreshContents()
  } catch (err) {
    toast.add({severity: 'error', summary: 'Error', detail: err.message || "Connection error", life: 3000});
  }
}

function onApprove() {
  const baseOptions = {
    group: 'firstConfirmDialog',
    header: 'Approve',
    rejectProps: {
      icon: 'pi pi-times',
      label: 'Cancel',
      severity: 'secondary',
      outlined: true
    },
    acceptProps: {
      label: 'Approve',
      severity: 'success',
      icon: 'pi pi-thumbs-up-fill'
    },
  };

  confirm.require({
    ...baseOptions,

    message: 'Do you want to approve this content?',
    icon: 'pi pi-question-circle',
    accept: () => {
      fetchApproveContent()
    },
    reject: () => {
    }
  })
}

</script>

<template>
  <button class="btn btn-success me-2 fw-bold text-uppercase"
          @click="onApprove">
    <IconFasThumbsUp class="me-1"/>
    Approve
  </button>

</template>

<style scoped>

</style>