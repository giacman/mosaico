<script setup lang="js">
import {onMounted, onUnmounted, ref} from "vue";
import {auth_fetch, error_message} from "@/utils.js";

const notifications = ref([]);
let intervalId;

onMounted(async () => {
  await fetchGetNotifications();
  intervalId = setInterval(fetchGetNotifications, 5000);
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId);
});

async function fetchGetNotifications(){
  try {
    const response = await auth_fetch('/api/get_notifications/', {method: 'GET'});
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    notifications.value = await response.json();
  }
  catch (err) {
    console.error(err);
  }
}

function removeNotification(id) {
  const index = notifications.value.findIndex(n => n.id === id);
  if (index !== -1) {
    notifications.value.splice(index, 1);
  }
}

</script>

<template>
  <div class="notification-list d-flex flex-column fs-5 fw-bold pb-2">Latest updates:</div>
  <div class="list-group overflow-auto">
    <Notification v-for="notification in notifications"
                  :key="notification.id"
                  :notification="notification"
                  @close="removeNotification(notification.id)"
    />
  </div>
</template>

<style scoped>
/* Hide scrollbar for Chrome, Safari and Opera */
.list-group::-webkit-scrollbar {
  display: none;
}

/* Hide scrollbar for IE, Edge and Firefox */
.list-group{
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}
</style>