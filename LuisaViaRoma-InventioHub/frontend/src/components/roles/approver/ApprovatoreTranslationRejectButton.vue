<script setup lang="js">

import Dialog from "primevue/dialog";
import {inject, ref} from "vue";
import {auth_fetch} from "@/utils.js";
import {useToast} from "primevue/usetoast";

const toast = useToast();

const refreshContents = inject('refreshContents');

const rejectionMessage = ref('')
const isRejecting = ref(false);

const props = defineProps({
  trans_id: {required: true},
})

const emit = defineEmits(['reject']);

async function rejectTranslation() {
  try {
    const res = await auth_fetch(`/api/reject_translation/${props.trans_id}/`, {
      method: 'PATCH',
      body: JSON.stringify({
        "rejection_message": rejectionMessage.value,
      })
    })

    if (!res.ok) {
      const err = await error_message(res)
      toast.add({severity: 'error', summary: 'Rejected', detail: err.message || "Fatal error", life: 3000});
      return
    }
    toast.add({severity: 'warning', summary: 'Confirmed', detail: "Translation rejected...", life: 3000});
    emit('reject', {
      transId: props.trans_id,
      message: rejectionMessage.value
    });

    refreshContents()
  } catch (err) {
    toast.add({severity: 'error', summary: 'Rejected', detail: err.message || "Fatal error", life: 3000});
  }
  isRejecting.value = false
}

</script>

<template>
  <Dialog v-model:visible="isRejecting" modal header="Rejecting..." :style="{ width: '25rem' }" appendTo="body"
          :baseZIndex="1500" tabindex="-1">
    <div class="mb-3">
      <label for="rejectionMessage" class="form-label">Give to the translator a rejection message:</label>
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
          @click="rejectTranslation"
      >
        <IconFasThumbsDown/>
        Reject
      </button>
    </div>
  </Dialog>

  <button class="btn btn-danger ms-2 text-uppercase fw-bold" @click="isRejecting = true"
          aria-label="Reject Translation">
    <IconFasThumbsDown class=""/>
    Reject
  </button>

</template>

<style scoped>

</style>