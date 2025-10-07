<script setup>
import {onMounted, reactive, ref} from 'vue'
import {auth_fetch, error_message, getRoleLabel, useStore} from '@/utils';
import {useToast} from "primevue/usetoast";

const toast = useToast();
const store = useStore()

const roleOptions = ['amministratore', 'copywriter', 'approvatore', 'traduttore', 'publisher']

const users = ref({})
const usersCopy = reactive({})


onMounted(async () => {
  await fetch_get_users()
})

function isDirty(username) {
  const original = users.value.find(u => u.username === username);
  if (!original) return false;
  const origRoles = [...original.roles].sort();
  const copyRoles = [...usersCopy[username].roles].sort();
  return JSON.stringify(origRoles) !== JSON.stringify(copyRoles);
}

async function fetch_get_users(role) {
  try {
    let response = null;
    if (role)
      response = await auth_fetch(`/api/get_users/${role}/`, {method: 'GET'});
    else
      response = await auth_fetch(`/api/get_users/`, {method: 'GET'});
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    users.value = await response.json();
    users.value.forEach(user => {
      usersCopy[user.username] = JSON.parse(JSON.stringify(user))
    })
  } catch (err) {
    toast.add({severity: 'error', summary: 'fetch Error', detail: err.message || "Fatal error", life: 3000});
  }
}


// Funzione per salvare i ruoli di un singolo utente
async function saveRoles(username) {
  await fetchAsyncRoles(usersCopy[username])
}

async function fetchAsyncRoles(user) {
  store.loading = true;
  try {
    const payload = {
      method: 'POST',
      body: JSON.stringify({
        'user_id': user.id,
        'roles': user.roles,
      })
    };
    const response = await auth_fetch('/api/sync_roles/', payload);
    if (!response.ok) {
      throw new Error('Failed to update role')
    }
    await fetch_get_users(null);
    toast.add({
      severity: 'success',
      summary: 'Role updated',
      detail: `${user.username}'s role successfully updated`,
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
  <div class="fs-4 mb-3">Manage Users</div>
  <div class="lvr-content-table table-responsive border border-1 rounded m-auto shadow-sm">
    <table class="table table-striped table-hover cursor-pointer m-0">
      <thead>
      <tr>
        <th>#</th>
        <th>Username</th>
        <th>First Name</th>
        <th>Last Name</th>

        <!-- Colonna compatta: visibile solo sotto md -->
        <th class="d-table-cell d-md-none">Ruoli</th>

        <!-- Colonne normali: nascoste sotto md -->
        <th
            v-for="role in roleOptions"
            :key="role"
            class="text-center align-middle d-none d-md-table-cell"
        >
          {{ getRoleLabel(role) }}
        </th>

        <th></th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="(user, idx) in users" :key="user.username">
        <td>{{ idx + 1 }}</td>
        <td>{{ user.username }}</td>
        <td>{{ user.first_name }}</td>
        <td>{{ user.last_name }}</td>

        <!-- Celle COMPATTE per mobile -->
        <td class="d-table-cell d-md-none">
          <div class="d-flex flex-column gap-2">
            <label
                v-for="role in roleOptions"
                :key="role"
                class="form-check"
            >
              <input
                  class="form-check-input"
                  type="checkbox"
                  :id="`chk-c-${user.username}-${role}`"
                  :value="role"
                  v-model="usersCopy[user.username].roles"
              />
              <span class="form-check-label">{{ getRoleLabel(role) }}</span>
            </label>
          </div>
        </td>

        <!-- Celle singole per desktop -->
        <td
            v-for="role in roleOptions"
            :key="role"
            class="text-center align-middle d-none d-md-table-cell"
        >
          <input
              class="form-check-input"
              type="checkbox"
              :id="`chk-${user.username}-${role}`"
              :value="role"
              v-model="usersCopy[user.username].roles"
          />
        </td>

        <td class="text-center align-middle">
          <button
              class="btn btn-primary btn-sm"
              @click="saveRoles(user.username)"
              :disabled="!isDirty(user.username)"
          >
            Save
          </button>
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
