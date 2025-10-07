<script setup>
import { ref, onMounted } from 'vue'
import {auth_fetch, error_message, useStore} from '@/utils.js';

const emit = defineEmits(['update:filters']);

const store = useStore()

let CONTENT_TYPES = ref([]);
const CONTENT_STATUSES = ref([]);
const CONTENT_STATES = ref([]);

const filters = ref({
  start_date: '',
  end_date: '',
  name: '',
  content_type: '',
  data_type: '',
  status: '',
  state: ''
})

async function fetch_get_content_types() {
  try {

    let url = '/api/get_content_types/';
    const response = await auth_fetch(url, {method: 'GET'});
    const data = await response.json();
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    CONTENT_TYPES.value = (data['content_types'] || []).map(type => type.name);
    CONTENT_STATUSES.value = (data['content_statuses'] || []);
    CONTENT_STATES.value = (data['content_states'] || []);

  }
  catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
    CONTENT_TYPES.value = [];
  }
}

onMounted(() => {
  fetch_get_content_types();
})

function applyFilters() {
  const query = new URLSearchParams();
  for (const key in filters.value) {
    const val = filters.value[key];
    if (val && val !== "") {
      query.set(key, val);
    }
  }
  emit('filters-query', query.toString());
}


function getAIStateLabel(state) {
  switch (state) {
    case 'success':
      return 'GENERATED';
    case 'failed':
      return 'FAILED';
    case 'received':
      return 'RECEIVED';
    case 'sent':
      return 'SENT';
    case 'pending':
      return 'PENDING';
    default:
      return 'UNPROCESSED';
  }
}

function getStatusLabel(status) {
  switch (status) {
    case 'bozza':
      return "DRAFT";
    case "review":
      return "REVIEW";
    case 'bozza_rifiutata':
      return 'REJECTED DRAFT';
    case 'bozza_validata':
      return 'VALID DRAFT';
    case 'review_traduzioni':
      return 'TRANSLATING';
    case 'validata':
      return 'VALIDATED';
    case 'pubblicata':
      return 'PUBLISHED';
    default:
      return status;
  }
}


</script>


<template>
  <div class="d-flex flex-wrap align-items-end gap-2 mb-3">

    <!-- Name -->
    <div>
      <label class="form-label small mb-1">Name</label>
      <input type="text" v-model="filters.name" class="form-control form-control-sm" />
    </div>

    <!-- Content Type -->
    <div>
      <label class="form-label small mb-1">Content</label>
      <select v-model="filters.content_type" class="form-select form-select-sm">
        <option value="">All</option>
        <option v-for="type in CONTENT_TYPES" :key="type" :value="type">{{ type }}</option>
      </select>
    </div>

    <!-- Type -->
    <div>
      <label class="form-label small mb-1">Type</label>
      <input type="text" v-model="filters.data_type" class="form-control form-control-sm"/>
    </div>

    <!-- Status -->
    <div v-if="store.role === 'copywriter'">
      <label class="form-label small mb-1">Status</label>
      <select v-model="filters.status" class="form-select form-select-sm" >
        <option value="">All</option>
        <option v-for="type in CONTENT_STATUSES" :key="type" :value="type">{{ getStatusLabel(type) }}</option>
      </select>
    </div>

    <!-- State -->
    <div v-if="store.role !== 'approvatore'">
      <label class="form-label small mb-1">AI State</label>
      <select v-model="filters.state" class="form-select form-select-sm">
        <option value="">All</option>
        <option v-for="type in CONTENT_STATES" :key="type" :value="type">{{ getAIStateLabel(type) }}</option>
      </select>
    </div>

    <!-- Start date -->
    <div>
      <label class="form-label small mb-1">From Date</label>
      <input type="date" v-model="filters.start_date" class="form-control form-control-sm"/>
    </div>
    <!-- End date -->
    <div>
      <label class="form-label small mb-1">To Date</label>
      <input type="date" v-model="filters.end_date" class="form-control form-control-sm"/>
    </div>

    <!-- Apply Button -->
    <div>
      <button @click="applyFilters" class="btn btn-sm btn-primary mt-3">
        Apply Filters
      </button>
    </div>
  </div>
</template>


