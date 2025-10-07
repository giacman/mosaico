<script setup lang="js">

import Dialog from "primevue/dialog";
import {inject, ref} from "vue";
import {auth_fetch, error_message} from "@/utils.js";
import {useToast} from "primevue/usetoast";
import {useRoute} from "vue-router";

const route = useRoute();
const toast = useToast();
const refreshContents = inject('refreshContents');

const rejectionMessage = ref('')
const isRejecting = ref(false);

const props = defineProps({
  content_id: {required: true},
})

const emit = defineEmits(['reject']);

async function rejectContent() {
  try {
    if (!rejectionMessage.value) return;
    let body_data = {
      "rejection_message": rejectionMessage.value,
    }
    const response = await auth_fetch(
        `/api/reject_content/${props.content_id}/`,
        {method: 'PUT', body: JSON.stringify(body_data)}
    );
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    toast.add({severity: 'warn', summary: 'Rejected', detail: "Content rejected...", life: 3000});
    emit('reject', {
      contentId: props.content_id,
      message: rejectionMessage.value
    });
    refreshContents()
  } catch (err) {
    toast.add({severity: 'error', summary: 'Error', detail: err.message || "Connection error", life: 3000});
  }
  isRejecting.value = false
}

</script>

<template>
  <Dialog v-model:visible="isRejecting" modal header="Rejecting..." :style="{ width: '25rem' }" appendTo="body"
          :baseZIndex="1500" tabindex="-1">
    <div class="mb-3">
      <label for="rejectionMessage" class="form-label">Give to the copywriter a rejection message:</label>
      <textarea
          id="rejectionMessage"
          class="form-control w-100"
          v-model="rejectionMessage"
          placeholder="Change this and that..."
      ></textarea>
    </div>
    <div class="d-flex justify-content-end gap-2">
      <button
          type="button"
          class="btn btn-outline-secondary rounded"
          @click="isRejecting = false"
      >Cancel
      </button>
      <button
          type="button"
          class="btn btn-danger fw-bold text-uppercase"
          :disabled="!rejectionMessage.trim()"
          @click="rejectContent"
      >
        <IconFasThumbsDown/>
        Reject
      </button>
    </div>
  </Dialog>

  <button class="btn btn-danger ms-2 text-uppercase fw-bold" @click="isRejecting = true"
          aria-label="Reject Content">
    <IconFasThumbsDown class=""/>
    {{route.path === '/approvatore/drafts' ? 'Reject' : 'Reject All'}}
  </button>

</template>

<style scoped>

</style>