<script setup>

import {ref, onMounted, watch, provide, onUnmounted, inject} from 'vue'
import {
  auth_fetch,
  error_message,
  useStore,
  hideAndCleanup, openContentModal
} from '../utils';

import Filter from '@/components/utils/Filter.vue'
import TranslationsTable from "@/components/translations/TranslationsTable.vue";

const store = useStore()
const contents = ref([]);
const next = ref(null);
const next_num = ref(0);

const filters = ref("");

let contentsRefreshInterval
const autoRefreshControl = inject('autoRefreshControl')

provide('refreshContents', () => {refreshContents()})


watch(filters, (newVal, oldVal) => {
	fetchGetContents();
}, { deep: true });


onMounted(async () => {
  await fetchGetContents();
  await openContentModal();
  contentsRefreshInterval = setInterval(() => {
    if (!autoRefreshControl.paused) {
      refreshContents()
    }
  }, 5000);
})

onUnmounted(() => {
  if (contentsRefreshInterval) clearInterval(contentsRefreshInterval);
});


async function fetchGetContents(next_url = null) {
	store.loading = true;
	try {
		let response = null;
		if(next_url)
			response = await auth_fetch(next_url, { method: 'GET' });
		else
			response = await auth_fetch(`/api/get_contents_published/?${filters.value}`, { method: 'GET' });
		if (!response.ok) {
			const err = await error_message(response);
			throw new Error(err);
		}

		const data = await response.json();
		next.value = data.next;
		const results = data.results;
		if(next_url){
			for(let i = 0 ; i < results.length; i++)
				contents.value.push(results[i]);
		}
		else
			contents.value = results;
	}
	catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
	}
	store.loading = false;
}


async function refreshContents(){
  try{
    let temp_contents = [];
    let response = await auth_fetch(`/api/get_contents_published/?${filters.value}`, {method: 'GET'});
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


</script>

<template>

  <Filter @filters-query="(f) => filters = f"/>

  <TranslationsTable :contents="contents"></TranslationsTable>

  <div v-if="next" class="text-center my-3">
    <button class="btn btn-secondary" @click="onNext">Load more</button>
  </div>

</template>
