<script setup>
import {ref, onMounted, watch, onUnmounted, provide} from 'vue'
import {
  auth_fetch,
  error_message,
  getContentStatusClassColor,
  getContentStatusLabel, formatDate, hideAndCleanup, useStore, openContentModal
} from '@/utils';
import ContentViewer from './ContentViewer.vue';
import {useToast} from "primevue/usetoast";

import Filter from "@/components/utils/Filter.vue";
import ApprovatoreContentRejectButton from "@/components/roles/approver/ApprovatoreContentRejectButton.vue";
import ApprovatoreContentApproveButton from "@/components/roles/approver/ApprovatoreContentApproveButton.vue";

let contentsRefreshInterval

provide('refreshContents', () => {refreshContents()})

const toast = useToast();
const store = useStore();

const contents = ref([]);

const filters = ref("");

const next = ref(null);
const next_num = ref(0);



watch(filters, (newVal, oldVal) => {
  fetch_get_contents_to_review();
}, {deep: true});


onMounted(async () => {
  await fetch_get_contents_to_review();
  await openContentModal();
  contentsRefreshInterval = setInterval(refreshContents, 5000);
})

onUnmounted(() => {
  if (contentsRefreshInterval) clearInterval(contentsRefreshInterval);
});


async function refreshContents(){
  try{
    let temp_contents = [];
    let response = await auth_fetch(`/api/get_contents_to_review/?${filters.value}`, {method: 'GET'});
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

async function fetch_get_contents_to_review() {
  store.loading = true;
  try {
    const response = await auth_fetch(`/api/get_contents_to_review/?${filters.value}`, {method: 'GET'});
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    const data = await response.json();
    next.value = data.next;
    contents.value = data.results;
  } catch (err) {
    toast.add({severity: 'error', summary: 'Fetch Error', detail: err.message || "Connection error", life: 3000});
  }
  store.loading = false;
}






</script>

<template>
  <Filter @filters-query="(f) => filters = f"/>

  <div class="table-responsive border border-1 rounded m-auto shadow-sm">
    <table class="table table-striped table-hover cursor-pointer m-auto">
      <thead>
      <tr>
        <th scope="col">#</th>
        <th scope="col">Name</th>
        <th scope="col">Content</th>
        <th scope="col">Type</th>
        <th scope="col">Status</th>
        <th scope="col">Creation Date</th>
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
       data-bs-focus="false"
       tabindex="-1"
       aria-labelledby="staticBackdropLabel"
       aria-hidden="true"
  >
    <div class="modal-dialog modal-fullscreen p-5 modal-dialog-scrollable modal-dialog-centered ">
      <div class="modal-content border border-2 border-secondary rounded">
        <div class="modal-header">
          <h1 class="modal-title fs-5" :id="'staticBackdropLabel-' + content.id">{{ content.title }}</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body bg-body-tertiary">

          <ContentViewer :content="content"/>

        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-warning me-auto text-uppercase fw-bold"
                  :data-bs-target="'staticBackdrop-' + content.id" data-bs-dismiss="modal">
            <IconFa6SolidCircleXmark class="me-1"/>
            Close
          </button>

          <ApprovatoreContentApproveButton :content_id="content.id" @approve="refreshContents"/>

          <ApprovatoreContentRejectButton :content_id="content.id" @reject="refreshContents"/>
        </div>
      </div>
    </div>
  </div>


  <div v-if="next" class="text-center my-3">
    <button class="btn btn-secondary" @click="onNext">Load more</button>
  </div>


</template>
