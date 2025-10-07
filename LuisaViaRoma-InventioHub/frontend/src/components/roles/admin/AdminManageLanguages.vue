<script setup>

import {onMounted, ref} from "vue";
import {auth_fetch, error_message} from "@/utils.js";
import {useToast} from "primevue/usetoast";

const toast = useToast();

const languages = ref([]);

onMounted(async () => {
  await fetchLanguageActive();
})

async function fetchLanguageActive() {
  try {
    const response = await auth_fetch(`/api/language_active/`, {method: 'GET'});
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    languages.value = await response.json();
  } catch (err) {
    toast.add({severity: 'error', summary: 'Fetch Error', detail: err.message || "Fatal error", life: 3000});
  }
}

async function toggleLanguageActive(lang) {
  try {
    const response = await auth_fetch('/api/language_active/', {
      method: 'PATCH',
      body: JSON.stringify({
        id: lang.id,
        active: lang.active,
      }),
    });
    if (!response.ok) {
      // revert change if request fails
      lang.active = !lang.active;
      const err = await error_message(response);
      throw new Error(err);
    }
    toast.add({severity: 'success', summary: 'Confirmed', detail: `Language ${lang.name} status updated`, life: 3000});
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Rejected',
      detail: err.message || 'Failed to update language status',
      life: 3000
    });
  }
}

</script>

<template>

  <div class="fs-4 mb-3">Manage Languages</div>
  <div class="lvr-content-table table-responsive border border-1 rounded m-auto shadow-sm">
    <table class="table table-striped table-hover cursor-pointer m-0">
      <thead>
      <tr>
        <th scope="col">#</th>
        <th scope="col">Name</th>
        <th scope="col">Language</th>
        <th scope="col">Country</th>
        <th scope="col" class="text-center align-middle">Active</th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="(lang,idx) in languages" :key="lang.id">
        <th scope="row">{{ idx }}</th>
        <td>{{ lang.name }} ({{ lang.lang_alpha2 }}-{{ lang.country_alpha2 }})</td>
        <td>{{ lang.lang_alpha2 }}</td>
        <td>{{ lang.country_alpha2 }}</td>
        <td class="text-center align-middle">
          <input class="form-check-input" type="checkbox" v-model="lang.active" @change="toggleLanguageActive(lang)"/>
        </td>
      </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.lvr-content-table table td, .lvr-content-table table tr {
  vertical-align: middle;
}
</style>