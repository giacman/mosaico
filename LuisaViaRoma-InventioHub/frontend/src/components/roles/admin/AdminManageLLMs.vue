<script setup>
import {computed, onMounted, ref} from "vue";
import {auth_fetch, error_message, useStore} from '@/utils';
import {useToast} from "primevue/usetoast";

const toast = useToast();
const store = useStore();

const llms = ref([]);

// form state
const newProvider = ref("");
const newModel = ref("");
const newActive = ref(true);
const adding = ref(false);

// fetch existing LLMs
onMounted(async () => {
  await fetchGetLLMs();
});

async function fetchGetLLMs() {
  try {
    const response = await auth_fetch('/api/get_llms/', {method: 'GET'});
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    const data = await response.json();
    llms.value = data['llms'];
  } catch (err) {
    toast.add({severity: 'error', summary: 'Fetch Error', detail: err.message || "Fatal error", life: 3000});
  }
}

async function toggleLLMActive(model) {
  try {
    const old = model.active;
    const response = await auth_fetch('/api/set_llm_model_active/', {
      method: 'PUT',
      body: JSON.stringify({
        id: model.id,
        active: model.active,
      }),
    });
    if (!response.ok) {
      // revert change if request fails
      model.active = !model.active;
      const err = await error_message(response);
      throw new Error(err);
    }
    const json = await response.json();
    const update = JSON.parse(json.update);
    toast.add({severity: 'success', summary: 'Confirmed', detail: `${model.name}: ${update.job_id}`, life: 3000});
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Rejected',
      detail: err.message || 'Failed to update model active status', life: 3000
    });
  }
}

async function fetch_add_new_llm(llm_string, active) {
  store.loading = true;
  try {
    const response = await auth_fetch('/api/add_new_llm/', {
      method: 'POST',
      body: JSON.stringify({
        llm_string: llm_string,
        active: active,
      }),
    });

    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }

    const data = await response.json();
    toast.add({
      severity: 'success',
      summary: 'Confirmed',
      detail: `Model ${data.model} added to service ${data.service}`,
      life: 3000
    });
    await fetchGetLLMs();
    // reset form
    newProvider.value = "";
    newModel.value = "";
    newActive.value = true;
  } catch (err) {
    toast.add({severity: 'error', summary: 'Fetch Error', detail: err.message || "Fatal error", life: 3000});
  } finally {
    store.loading = false;
    adding.value = false;
  }
}

function submitNewLLM(e) {
  e.preventDefault();
  if (!newProvider.value.trim() || !newModel.value.trim()) {
    toast.add({severity: 'warn', summary: 'Validation', detail: 'Provider and Model are required', life: 2500});
    return;
  }
  const llm_string = `${newProvider.value.trim()}:${newModel.value.trim()}`; // adjust if backend expects different format
  adding.value = true;
  fetch_add_new_llm(llm_string, newActive.value);
}

// compute row numbering
const flattenedRows = computed(() => {
  const rows = [];
  llms.value.forEach(provider => {
    provider.models.forEach(model => {
      rows.push({
        providerName: provider.name,
        model,
      });
    });
  });
  return rows;
});
</script>

<template>
  <div class="fs-4 mb-3">Add LLM</div>
  <div class="card mb-4">
    <div class="card-body">
      <form @submit="submitNewLLM" class="row g-3">
        <div class="col-md-4">
          <label for="providerInput" class="form-label">Provider</label>
          <input type="text" id="providerInput" class="form-control" v-model="newProvider" placeholder="e.g., openai"
                 required/>
        </div>
        <div class="col-md-4">
          <label for="modelInput" class="form-label">Model</label>
          <input type="text" id="modelInput" class="form-control" v-model="newModel" placeholder="e.g., gpt-4o"
                 required/>
        </div>
        <div class="col-md-2 d-flex align-items-end">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" id="activeCheck" v-model="newActive"/>
            <label class="form-check-label" for="activeCheck">Active</label>
          </div>
        </div>
        <div class="col-md-2 d-flex align-items-end">
          <button type="submit" class="btn btn-primary w-100" :disabled="adding || store.loading">
            <span v-if="adding || store.loading" class="spinner-border spinner-border-sm me-1" role="status"
                  aria-hidden="true"></span>
            Add LLM
          </button>
        </div>
      </form>
      <div class="form-text mt-2 d-flex align-items-center">
        <IconFasExclamationTriangle class="text-warning me-2 "/>
        Names are case SENSITIVE.
      </div>
    </div>
  </div>

  <div class="fs-4 mb-3">Manage LLMs</div>
  <div class="lvr-content-table table-responsive border border-1 rounded m-auto shadow-sm">
    <table class="table table-striped table-hover cursor-pointer m-0">
      <thead>
      <tr>
        <th scope="col">#</th>
        <th scope="col">Provider</th>
        <th scope="col">Model</th>
        <th scope="col" class="text-center align-middle">Active</th>
      </tr>
      </thead>
      <tbody>
      <template v-for="(row, idx) in flattenedRows" :key="row.model.id">
        <tr>
          <th scope="row">{{ idx + 1 }}</th>
          <td>{{ row.providerName }}</td>
          <td>{{ row.model.name }}</td>
          <td class="text-center align-middle">
            <input class="form-check-input" type="checkbox" v-model="row.model.active"
                   @change="toggleLLMActive(row.model)"/>
          </td>
        </tr>
      </template>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.lvr-content-table table td, .lvr-content-table table tr {
  vertical-align: middle;
}
</style>
