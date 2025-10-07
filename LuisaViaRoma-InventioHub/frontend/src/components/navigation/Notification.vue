<script setup lang="js">
import {auth_fetch, error_message} from "@/utils.js";
import {ref} from "vue";


const props = defineProps({
  notification: {required:true, type: Object}
})

const emit = defineEmits(['close']);
const showDelete = ref(false)

async function fetchConsume(){
  try {
    const change_role_response = await auth_fetch(`/api/change_role/?new_role=${props.notification.role_name}`, {method: 'GET'});
    if (!change_role_response.ok) {
      const err = await error_message(change_role_response);
      throw new Error(err);
    }
    const response = await auth_fetch(`/api/consume_notification/${props.notification.id}/`, {method: 'DELETE'});
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    const data = await response.json();
    localStorage.setItem("link", props.notification.link);
    localStorage.setItem("editorModal_id", props.notification.modal_id);
    window.location.href = "/";
  }
  catch (err) {
    console.error(err);
  }
}

async function fetchClose(){
  try {
    const response = await auth_fetch(`/api/consume_notification/${props.notification.id}/`, {method: 'DELETE'});
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    emit("close", props.notification.id);
  }
  catch (err) {
    console.error(err);
  }
}

</script>

<template>
  <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center p-0 cursor-pointer" @mouseenter="showDelete=true" @mouseleave="showDelete=false">
    <div class="notification-text py-1 ps-3" @click="fetchConsume()">
      {{notification.message}}
    </div>
    <div v-if="showDelete"  class="px-3 py-1 close-notification-button flex-grow-0" @click="fetchClose()">
      <IconFa6SolidTrash class="mb-1"/>
    </div>
  </div>

</template>

<style scoped>

.close-notification-button {
  font-size: 0.65em !important;
}

.notification-text {
  font-size: 0.8em !important;
}
.close-notification-button:hover{
    background: rgba(255, 0, 0, 0.46);
}
</style>