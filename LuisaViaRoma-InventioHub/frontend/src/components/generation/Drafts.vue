<script setup>

import {ref, onMounted, watch, nextTick, onUnmounted} from 'vue'
import {
  auth_fetch,
  error_message,
  useStore,
  getContentStatusClassColor,
  getContentStatusLabel,
  getAIStateClassColor, formatDate, getAIStateLabel, hideAndCleanup,
  openContentModal
} from '@/utils.js';
import {useRouter} from 'vue-router'
import ContentViewer from '../ContentViewer.vue';
import History from '../History.vue';
import Filter from '@/components/utils/Filter.vue'
import { useToast } from "primevue/usetoast";
import {useDeleteConfirm} from "@/composables/useDeleteConfirm.js";

import { useConfirm } from "primevue/useconfirm";

let contentsRefreshInterval;

const confirm = useConfirm();

const { confirmDelete } = useDeleteConfirm()
const toast = useToast();
const store = useStore()
const router = useRouter()
const contents = ref([]);
const next = ref(null);
const next_num = ref(0);
const filters = ref("");

watch(filters, (newVal, oldVal) => {
  fetch_get_contents();
}, {deep: true});


async function sendForReview(contentId, modalId){
  try{
    const response = await auth_fetch(`/api/send_to_content_review/${contentId}/`,
        {
          method: 'GET'
        }, false);

    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    await hideAndCleanup(modalId);
    toast.add({ severity: 'success', summary: 'Confirmed', detail: "Draft sent for review", life: 3000 });
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
  }
}

async function refreshContents(){

  try{
    let temp_contents = [];
    let response = await auth_fetch(`/api/get_contents/?${filters.value}`, {method: 'GET'});
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }

    const data = await response.json();
    let next = data.next;
    temp_contents.push(...data.results);

    for(let i = 0; i<next_num.value; i++){
      response = await auth_fetch(next, {method: 'GET'});

      if (!response.ok) {
        const err = await error_message(response);
        throw new Error(err);
      }

      const data = await response.json();
      next = data.next;
      temp_contents.push(...data.results);
    }

    //Check for open modals that are not in temp_contents
    let content_ids = new Set(temp_contents.map(item => item.id));
    let open_modals = document.getElementsByClassName("content-modal modal fade show");
    for(const open_modal of open_modals){
      if(!content_ids.has(Number(open_modal.id.split("-").slice(-1)[0])))
        await hideAndCleanup(open_modal.id);
    }
    contents.value = temp_contents;
  }catch(error){
    console.error("Failed to refresh contents: ", error);
  }

}

async function onNext(){
  try {
    next_num.value++;
    let response = await auth_fetch(next.value, {method: 'GET'});

    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }

    const data = await response.json();
    next.value = data.next;
    contents.value.push(...data.results);

  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
  }
}

async function fetch_get_contents() {
  store.loading = true;
  try {
    let response = await auth_fetch(`/api/get_contents/?${filters.value}`, {method: 'GET'});
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }

    const data = await response.json();
    next.value = data.next;
    contents.value = data.results;
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
  }
  store.loading = false;
}


function onSendForReview(contentId, modalId){
  const baseOptions = {
    group: 'firstConfirmDialog',
    header: 'Send for review?',
    rejectProps: {
      icon: 'pi pi-times',
      label: 'Cancel',
      severity: 'secondary',
      outlined: true
    },
    acceptProps: {
      label: 'Send',
      severity: 'success',
      icon:'pi pi-send'
    },
  };

  confirm.require({
    ...baseOptions,

    message: 'Do you want to send to review this content?',
    icon: 'pi pi-question-circle',
    accept: () => sendForReview(contentId, modalId),
    reject: () => {}
  })
}



async function fetch_delete_content(content, modalId) {
  try {
    const response = await auth_fetch(`/api/update_content/${content.id}/`, {method: 'DELETE'});

    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    const removed_content = await response.json();
    const index = contents.value.findIndex(c => c.id === removed_content.id);
    if (index !== -1){
      await hideAndCleanup(modalId)
      contents.value.splice(index, 1);
    }
    toast.add({ severity: 'success', summary: 'Confirmed', detail: "Draft removed", life: 3000 });
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
  }
}

function edit_content(content_id) {
  router.push({name: 'edit_content', params: {content_id: content_id}})
}

const showHistory = ref(false)
const history_content_id = ref(null)

async function openHistoryModal(content_id) {
  history_content_id.value = content_id;
  showHistory.value = true;
  nextTick(() => {
    document.getElementById('button-modal-history').click();
  });
}

function handleContentRestored(restored_content) {
  // update the corresponding content
  for (let i = 0; i < contents.value.length; i++) {
    if (contents.value[i].id === restored_content.id) {
      contents.value.splice(i, 1, restored_content);
      break;
    }
  }
  showHistory.value = false;
  document.getElementById('close-modal-history').click();
  toast.add({ severity: 'success', summary: 'Confirmed', detail: `Content ${restored_content.title} restored`, life: 3000 });
}

onMounted(async () => {
	await fetch_get_contents();
	await openContentModal();
  contentsRefreshInterval = setInterval(refreshContents, 5000);
})

onUnmounted(() => {
	if (contentsRefreshInterval) clearInterval(contentsRefreshInterval);
});

</script>

<template>

  <button id="button-modal-history" type="button" class="d-none" data-bs-toggle="modal"
          data-bs-target="#modal-history"></button>
  <button id="close-modal-history" type="button" class="d-none" data-bs-dismiss="modal"
          data-bs-target="#modal-history"></button>

  <div id="modal-history" class="history-modal modal fade" tabindex="-1">
    <div class="modal-dialog modal-fullscreen p-5 modal-dialog-scrollable modal-dialog-centered" role="document">
      <div class="modal-content rounded">
        <div class="modal-header">
          <h5 class="modal-title">History</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" data-bs-target="modal-history" aria-label="Close"></button>
        </div>

        <div class="modal-body p-5">
          <History v-if="showHistory" :content_id="history_content_id" @restored="handleContentRestored"/>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-warning me-auto text-uppercase fw-bold" data-bs-target="modal-history" data-bs-dismiss="modal">
            <IconFa6SolidCircleXmark class="me-1"/>
            Close
          </button>
        </div>

      </div>
    </div>
  </div>

  <Filter @filters-query="(f) => filters = f"/>

  <div class="lvr-content-table table-responsive border border-1 rounded m-auto shadow-sm">
    <table class="table table-striped table-hover cursor-pointer m-auto">
      <thead>
      <tr>
        <th scope="col">#</th>
        <th scope="col">Name</th>
        <th scope="col">Content</th>
        <th scope="col">Type</th>
        <th scope="col">Status</th>
        <th scope="col">Creation Date</th>
        <th scope="col">AI State</th>
        <th scope="col">AI Sent Date</th>
      </tr>
      </thead>
      <tbody class="table-group-divider">
      <template v-for="content in contents" :key="content.id">
        <!-- Clickable Row -->
        <tr class="content-header" data-bs-toggle="modal" :data-bs-target="'#staticBackdrop-' + content.id">
          <td class="fw-bold">{{ content.id }}</td>
          <td><span class="d-inline-block text-truncate">{{ content.title }}</span></td>
          <td class="fw-bold">{{ content.content_type }}</td>
          <td class="fw-bold">{{ content.data.type ? content.data.type : "-" }}</td>
          <td>
            <label class="badge text-uppercase" :class="getContentStatusClassColor(content)">
              {{ getContentStatusLabel(content) }}
            </label>
          </td>
          <td>{{ formatDate(content.created_at) }}</td>
          <td>
            <label class="badge text-uppercase" :class="getAIStateClassColor(content.state)">
              {{ getAIStateLabel(content.state) }}
            </label>
          </td>
          <td>{{ formatDate(content.sent_at) }}</td>
        </tr>
      </template>
      </tbody>
    </table>
  </div>




  <div v-for="content in contents" :key="content.id"
       class="content-modal modal fade"
       :id="'staticBackdrop-' + content.id"
       data-bs-backdrop="static"
       data-bs-keyboard="false"
       tabindex="-1"
       aria-labelledby="staticBackdropLabel"
       aria-hidden="true"
  >
      <div class="modal-dialog modal-fullscreen p-5 modal-dialog-scrollable modal-dialog-centered">
        <div class="modal-content border border-2 border-secondary rounded">
          <div class="modal-header">
            <h1 class="modal-title fs-5" :id="'staticBackdropLabel-' + content.id">{{ content.title }}</h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body bg-body-tertiary">

            <ContentViewer :content="content"/>

          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-warning me-auto text-uppercase fw-bold" :data-bs-target="'staticBackdrop-' + content.id" data-bs-dismiss="modal">
              <IconFa6SolidCircleXmark class="me-1"/>
              Close
            </button>

            <template v-if="['bozza', 'bozza_validata', 'bozza_rifiutata'].includes(content.status) && ['local', 'success', 'failed'].includes(content.state)">

              <button v-if="content.status === 'bozza' && content.state === 'success'"
                      class="btn btn-success mx-2 px-5 text-uppercase  fw-bold" @click="onSendForReview(content.id, 'staticBackdrop-' + content.id)">
                <IconFasEnvelope class="me-1"/>
                Send to Review
              </button>

              <button v-if="['bozza', 'bozza_rifiutata'].includes(content.status)"
                      class="btn btn-secondary text-uppercase fw-bold" @click="edit_content(content.id)"
                      data-bs-dismiss="modal" aria-label="Edit">
                <IconFasWrench class="me-1"/>
                Edit
              </button>

              <button class="btn btn-danger ms-2 text-uppercase fw-bold" @click="confirmDelete(() =>fetch_delete_content(content, 'staticBackdrop-' + content.id))">
                <IconFasTrash class="me-1"/>
                Delete
              </button>

              <button v-if="['bozza', 'bozza_rifiutata'].includes(content.status)"
                      class="btn btn-info ms-2 text-uppercase fw-bold"
                      @click="openHistoryModal(content.id)"
                      data-bs-dismiss="modal"
                      :data-bs-target="'staticBackdrop-' + content.id"
              >
                <IconFa6SolidClockRotateLeft class="me-2"/>
                History
              </button>
            </template>

          </div>
        </div>
      </div>
    </div>

  <div v-if="next" class="text-center my-3">
    <button class="btn btn-secondary" @click="onNext">Load more</button>
  </div>

</template>


<style scoped>

</style>
