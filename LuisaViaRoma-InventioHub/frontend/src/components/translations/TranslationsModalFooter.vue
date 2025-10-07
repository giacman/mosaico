<script setup>
import {getUniformTranslationStatuses} from "@/components/translations/translation_utils.js";
import {auth_fetch, error_message, useStore} from "@/utils.js";
import {useToast} from "primevue/usetoast";
import {useDeleteConfirm} from "@/composables/useDeleteConfirm.js";
import ApprovatoreContentRejectButton from "@/components/roles/approver/ApprovatoreContentRejectButton.vue";
import ApprovatorePublishButton from "@/components/roles/approver/ApprovatorePublishButton.vue";
import CopywriterSendInReviewButton from "@/components/roles/copywriter/CopywriterSendInReviewButton.vue";
import CopyNEWSLETTERClipboard from "@/components/utils/CopyNEWSLETTERClipboard.vue";

const toast = useToast();

const {confirmDelete} = useDeleteConfirm()

const props = defineProps({
  content: {required: true}
})

const store = useStore()


const {status: uniformTranslationStatus, status_num: num} = getUniformTranslationStatuses(props.content);


async function fetch_delete_content(content) {
  try {
    const response = await auth_fetch(`/api/update_content/${content.id}/`, {method: 'DELETE'});

    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    const removed_content = await response.json();
    const index = contents.value.findIndex(c => c.id === removed_content.id);
    if (index !== -1)
      contents.value.splice(index, 1);
    toast.add({severity: 'success', summary: 'Confirmed', detail: "Translation removed", life: 3000});
  } catch (err) {
    toast.add({severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000});
  }
}

async function fetch_gsheet_export(content) {
  store.loading = true;
  try {
    let body_data = {
      "content_id": content.id,
    }
    const response = await auth_fetch('/api/gsheet_export/', {method: 'POST', body: JSON.stringify(body_data)});
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    toast.add({severity: 'success', summary: 'Confirmed', detail: "Exported successfully", life: 3000});
    content.status = "pubblicata"
  } catch (err) {
    toast.add({severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000});
  }
  store.loading = false;
}

</script>

<template>
  <div class="d-flex flex-fill justify-content-between">

    <button type="button" class="btn btn-warning text-uppercase fw-bold " data-bs-dismiss="modal">
      <IconFa6SolidCircleXmark class="me-1"/>
      Close
    </button>

    <template v-if="store.role === 'approvatore' && content.status ==='validata'">
      <ApprovatorePublishButton :content_id="content.id"/>
      <ApprovatoreContentRejectButton :content_id="content.id"/>
    </template>

    <template v-if="store.role === 'publisher' && content.status ==='pubblicata'">
      <CopyNEWSLETTERClipboard
          v-if="content.content_type === 'NEWSLETTER'"
          :content="content"
          :show-download="true"
      />

      <CopyALLClipboard
          :content="content"
          :show-download="true"
      />

      <button
          class="btn btn-success  text-uppercase fw-bold"
          @click="fetch_gsheet_export(content)">
        <IconFasFileExport class="me-2"/>
        Export to GSheet
      </button>

    </template>

    <template
        v-if="store.role === 'copywriter' && content.status === 'review_traduzioni' && ( ['validata', 'rifiutata'].includes(uniformTranslationStatus) || ['bozza_validata'].includes(content.status))">
      <CopywriterSendInReviewButton :content_id="content.id"/>
      <button class="btn btn-danger text-uppercase fw-bold"
              @click="confirmDelete(fetch_delete_content(content))">
        <IconFasTrash class="me-1"/>
        Delete
      </button>
    </template>

  </div>
</template>

<style scoped>

</style>
