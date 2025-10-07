<script setup>
import {onMounted, onUnmounted, ref, watch} from 'vue'
import {auth_fetch, error_message, hideAndCleanup, openContentModal, useStore,} from '@/utils.js';
import {useToast} from "primevue/usetoast";
import Filter from "@/components/utils/Filter.vue";
import TranslationsTable from "@/components/translations/TranslationsTable.vue";

const toast = useToast();

let contentsRefreshInterval;

const store = useStore();
const next = ref(null);
const next_num = ref(0);

const contents = ref([]);

const filters = ref("");
watch(filters, (newVal, oldVal) => {
  fetch_get_translations_validated();
}, {deep: true});


onMounted(async () => {
  await fetch_get_translations_validated();
  await openContentModal();
  contentsRefreshInterval = setInterval(refreshContents, 5000);
})

onUnmounted(() => {
  if (contentsRefreshInterval) clearInterval(contentsRefreshInterval);
});


async function refreshContents() {
  try {
    let temp_contents = [];
    let response = await auth_fetch(`/api/get_translations_validated/?${filters.value}`, {method: 'GET'});
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }

    const data = await response.json();
    let next = data.next;
    temp_contents.push(...data.results);

    for (let i = 0; i < next_num.value; i++) {
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
    for (const open_modal of open_modals) {
      if (!content_ids.has(Number(open_modal.id.split("-").slice(-1)[0])))
        await hideAndCleanup(open_modal.id);
    }
    contents.value = temp_contents;
  } catch (error) {
    console.error("Failed to refresh contents: ", error);
  }

}


async function onNext() {
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
    toast.add({severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000});
  }
}

async function fetch_get_translations_validated() {
  store.loading = true;
  try {
    const response = await auth_fetch(`/api/get_translations_validated/?${filters.value}`, {method: 'GET'});
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    const data = await response.json();
    contents.value = data.results;
    next.value = data.next;

  } catch (err) {
    toast.add({severity: 'error', summary: 'Error', detail: err.message || "Connection error", life: 3000});
  }
  store.loading = false;
}
</script>


<template>
  <Filter @filters-query="(f) => filters = f"/>

  <TranslationsTable :contents="contents"></TranslationsTable>

  <div v-if="next" class="text-center my-3">
    <button class="btn btn-secondary" @click="onNext">Load more</button>
  </div>
</template>

