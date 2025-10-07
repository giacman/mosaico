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

const emit = defineEmits(['sent']);


async function fetchSendInReview() {
  try {
    const response = await auth_fetch(
        `/api/send_to_final_review/${props.content_id}/`,
        {method: 'GET'}
    );

    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    toast.add({severity: 'success', summary: 'Confirmed', detail: "Sent to Approver", life: 3000});
    emit('sent', {contentId: props.content_id});
    refreshContents()
  } catch (err) {
    toast.add({severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000});
  }
}

function onSendInReview() {
  confirm.require({
    group: 'firstConfirmDialog',
    message: 'Do you want to send this content for final review?',
    header: 'Final Review',
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: 'Cancel',
    rejectProps: {
      icon: 'pi pi-times',
      label: 'Cancel',
      severity: 'danger',
      outlined: true
    },
    acceptProps: {
      label: 'Send',
      severity: 'success',
      icon: 'pi pi-send'
    },
    accept: () => {
      fetchSendInReview();
    },
    reject: () => {
    }
  });
}

</script>

<template>
  <button class="btn btn-success me-2 fw-bold text-uppercase"
          @click="onSendInReview">
    <IconFasEnvelope class="me-1"/>
    Send in Review
  </button>

</template>

<style scoped>

</style>