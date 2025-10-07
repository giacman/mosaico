<script setup>
import { ref, onMounted, watch } from 'vue'
import { auth_fetch, error_message, useStore, getContentStatusClassColor } from '../utils';
import { useToast } from "primevue/usetoast";
const toast = useToast();
import { useRouter } from 'vue-router'
import JSONViewer from "@/components/json/JSONViewer.vue";
import { useConfirm } from "primevue/useconfirm";
const confirm = useConfirm();


// TODO Gestione del restore dello schema nella history. Ora come ora lo schema rimane quello settato al momento del restore nel content



const store = useStore();
const router = useRouter()
const contents = ref([]);

const props = defineProps({
	content_id: {
		type: [String, Number],
		required: true
	}
});

const emit = defineEmits(['restored']);

async function fetch_get_content_history() {
	store.loading = true;
	try {
		let url = `/api/get_content_history/${props.content_id}/`;
		const response = await auth_fetch(url, {method: 'GET'});
		if (!response.ok) {
			const err = await error_message(response);
			throw new Error(err);
		}
		const data = await response.json();
		contents.value = data;
	} 
	catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
		store.loading = false;
	}
	store.loading = false;
}


function onRestore(content_id, history_id){
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
    accept: () => fetch_restore_content(content_id, history_id),
    reject: () => {}
  })
}


async function fetch_restore_content(content_id, history_id) {

	store.loading = true;
	try {
		let url = `/api/restore_content/${content_id}/${history_id}`;
		const response = await auth_fetch(url, {method: 'GET'});
		if (!response.ok) {
			const err = await error_message(response);
			throw new Error(err);
		}
		const data = await response.json();
		contents.value = [];
		emit('restored', data);
	} 
	catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
		store.loading = false;
	}
	store.loading = false;
}
  
onMounted(async () => {
	fetch_get_content_history();
})

watch(() => props.content_id, (newId) => {
	contents.value = [];
	if (newId) {
		fetch_get_content_history()
	}
})

</script>

<template>

<div v-for="delta in contents.diffs" :key="delta.history_id" class="p-4 border border-1 rounded shadow-sm">
	<div class="content-header d-flex justify-content-between align-items-center">
		<span class="fs-5"><strong>{{ delta.title }} {{ delta.history_id }}</strong></span>
		<span class="fs-5">{{ delta.to }}</span>
	</div>

	<div class="mt-4">
		<table class="table table-bordered table-sm">
		<thead>
			<tr>
			<th>Field</th>
			<th>Old</th>
			<th>New</th>
			</tr>
		</thead>
		<tbody>
			<tr v-for="(change, index) in delta.changes" :key="index">
			<td>{{ change.field }}</td>
			<td v-if="change.field === 'data'"><JSONViewer :data="change.old"/></td>
			<td v-else> {{ change.old }} </td>
			<td v-if="change.field === 'data'"><JSONViewer :data="change.new"/></td>
			<td v-else>{{ change.new }} </td>
			</tr>
		</tbody>
		</table>

		<div class="mt-4 d-flex justify-content-end">
			<button class="mt-2 btn btn-info text-uppercase fw-bold" @click="fetch_restore_content(delta.id, delta.history_id)">
        <IconFasRecycle class="me-2" />
				Restore
			</button>
		</div>
	</div>
</div>
</template>
