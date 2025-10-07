<script setup lang="js">
import {auth_fetch, error_message, getRoleLabel, useStore} from "@/utils.js";
import Dialog from "primevue/dialog";
import {ref, watch} from "vue";
const store = useStore();

const isChanging = ref(false)
const selectedRole = ref(null)

const props = defineProps({
  context: {required:true}
})

async function fetchChangeRole(){
  if(!selectedRole.value) return;
  store.loading = true;
  const response = await auth_fetch(`/api/change_role/?new_role=${selectedRole.value}`, {method: 'GET'});
  if (!response.ok){
    store.loading = false;
    const err = await error_message(response);
    toast.add({ severity: 'error', summary: 'Fetch Error', detail: err.message || "Fatal error", life: 3000 });

    return;
  }
  store.loading = false;
  selectedRole.value = null
  window.location.href = "/";
}

</script>

<template>

  <Dialog v-model:visible="isChanging" modal header="Change Role" :style="{ width: '25rem' }" appendTo="body" :baseZIndex="1500" tabindex="-1">
    <div v-for="role in store.roles" :key="role" class="form-check">
      <input class="form-check-input" type="radio" :id="`role-${role}`" :value="role"
             v-model="selectedRole" name="roleOptions"/>
      <label class="form-check-label" :for="`role-${role}`">{{ getRoleLabel(role) }}</label>
    </div>
    <div class="d-flex justify-content-end gap-2">
      <button
          type="button"
          class="btn btn-outline-secondary rounded"
          @click="isChanging = false"
      >Cancel</button>
      <button type="button" class="btn btn-primary" @click="fetchChangeRole"
              :disabled="!selectedRole">
        Change
      </button>
    </div>
  </Dialog>

  <button v-if="store.role != null && store.roles && store.roles.length > 0"
          class="btn btn-primary text-uppercase d-flex align-items-center"
          @click="isChanging=true"
  >
    <IconFasPeopleArrows class="me-1 pb-1"/>
    <div :class="{'multi-collapse collapse-horizontal collapse show text-nowrap':context==='sidebar'}">
      Change Role
    </div>
  </button>
</template>

<style scoped>

</style>