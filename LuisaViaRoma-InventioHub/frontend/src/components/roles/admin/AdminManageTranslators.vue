<script setup>
import {onMounted, ref} from 'vue'
import Multiselect from "vue-multiselect";
import {auth_fetch, error_message, useStore} from '@/utils';
import {useToast} from "primevue/usetoast";
import Dialog from "primevue/dialog";

const toast = useToast();
const store = useStore()

const users = ref({})
const selectedLangs = ref([])
const selectedUser = ref({})
const options = ref([])

const isChanging = ref(false)

onMounted(async () => {
  try {
    options.value = await retrieveActiveLanguages()
    await fetchGetTranslators()
  } catch (e) {
    console.error(e)
  }
})

function onRowClick(user) {
  selectedLangs.value = user.complete_langs
  selectedUser.value = user
  isChanging.value = true
}

async function retrieveActiveLanguages() {
  try {
    const response = await auth_fetch('/api/language_active/', {method: 'GET'}, false)
    if (!response.ok) {
      console.error(await error_message(response))
      return []
    }
    const langs = await response.json()
    return langs.map(l => ({complete_name: `${l.name} (${l.lang_alpha2}-${l.country_alpha2})`, ...l}))

  } catch (err) {
    toast.add({severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000});
  }
}


async function fetchGetTranslators() {
  try {
    let response = await auth_fetch(`/api/get_users/traduttore/`, {method: 'GET'});
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    users.value = await response.json();
    for (let i = 0; i < users.value.length; i++) {
      users.value[i].complete_langs = []
      for (const option of options.value) {
        if (users.value[i].langs.includes(Number(option.id)))
          users.value[i].complete_langs.push(option)
      }
    }
  } catch (err) {
    toast.add({severity: 'error', summary: 'fetch Error', detail: err.message || "Fatal error", life: 3000});
  }
}

async function saveLanguages() {
  store.loading = true;
  try {
    const payload = {
      method: 'PUT',
      body: JSON.stringify({
        'langs': selectedLangs.value.map(l => l.id),
      })
    };
    const response = await auth_fetch(`/api/set_user_langs/${selectedUser.value.id}/`, payload);
    if (!response.ok) {
      const err = await error_message(response)
      throw new Error(err)
    }
    await fetchGetTranslators();
    isChanging.value = false
    toast.add({
      severity: 'success',
      summary: 'Languages updated',
      detail: `${selectedUser.value.username}'s languages successfully updated`,
      life: 3000
    });
  } catch (error) {
    toast.add({severity: 'error', summary: 'Fetch Error', detail: error.message || "Fatal error", life: 3000});
    console.error(error);
  }
  store.loading = false;
}
</script>


<template>
  <Dialog v-model:visible="isChanging"
          modal
          header="Selecting languages..."
          :style="{ width: '50rem', maxWidth: '90vw' }"
          :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
          appendTo="body"
          :baseZIndex="1500"
          tabindex="-1"
  >
    <div class="position-relative" style="height: 35vh">
      <label class="form-label text-body-tertiary fw-bold">
        Select languages for {{ selectedUser.username }}
      </label>
      <Multiselect
          v-model="selectedLangs"
          :options="options"
          :multiple="true"
          :close-on-select="false"
          :clear-on-select="false"
          :preserve-search="true"
          :hide-selected="true"
          placeholder="Choose languages"
          label="complete_name"
          track-by="complete_name"
          :preselect-first="false"
          class="w-100"
      >
        <template #option="{ option }">
          <span class="fi me-2 fis rounded-circle" :class="'fi-' + option.country_alpha2?.toLowerCase()"></span>
          <span>{{ option.complete_name }}</span>
        </template>
        <template #tag="{ option, remove }">
      <span class="multiselect__tag py-1 d-inline-flex align-items-center" :key="option.id">
        <span class="fi me-2 fis rounded-circle" :class="'fi-' + option.country_alpha2?.toLowerCase()"></span>
        {{ option.complete_name }}
        <i
            class="multiselect__tag-icon ms-2"
            @mousedown.prevent="remove(option)"
            @keypress.enter.prevent="remove(option)"
            tabindex="-1"
            style="cursor: pointer;"
        ></i>
      </span>
        </template>
      </Multiselect>


    </div>

    <div class="d-flex justify-content-end gap-2">
      <button
          type="button"
          class="btn btn-outline-secondary rounded"
          @click="isChanging = false"
      >Cancel
      </button>
      <button
          type="button"
          class="btn btn-success fw-bold text-uppercase"
          @click="saveLanguages"
      >
        <IconFa6SolidFloppyDisk/>
        Save
      </button>
    </div>
  </Dialog>


  <div class="fs-4 mb-3">Manage Translators Languages</div>
  <div class="lvr-content-table table-responsive border border-1 rounded m-auto shadow-sm">
    <table class="table table-striped table-hover cursor-pointer m-0">
      <thead>
      <tr>
        <th>#</th>
        <th>Username</th>
        <th>First Name</th>
        <th>Last Name</th>
        <th>Languages</th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="(user, idx) in users" :key="user.username" @click="onRowClick(user)">
        <td>{{ idx + 1 }}</td>
        <td>{{ user.username }}</td>
        <td>{{ user.first_name }}</td>
        <td>{{ user.last_name }}</td>
        <td>
          <div
              v-for="(lang, idx) in user.complete_langs"
              :key="idx"
              class="fi fis rounded-circle"
              :class="'fi-' + lang.country_alpha2.toLowerCase()"
          ></div>
        </td>
      </tr>
      </tbody>
    </table>
  </div>
</template>


<style scoped>

.multiselect__content {
  position: absolute !important;
  top: 100%;
  left: 0;
  z-index: 1055; /* sopra il dialogo */
  width: 100%;
  max-height: 12rem; /* limitato con scroll */
  overflow-y: auto;
}

.lvr-content-table table td, .lvr-content-table table tr {
  vertical-align: middle;
}
</style>
