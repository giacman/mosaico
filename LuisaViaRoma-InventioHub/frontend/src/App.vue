<script setup>
import {ref, watch, onMounted, reactive, provide} from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {auth_fetch, navigate_to, useStore, error_message, getRoleLabel} from '@/utils.js';
import { useToast } from "primevue/usetoast";
const toast = useToast();
import Navbar from "@/components/navigation/Navbar.vue";
import Sidebar from "@/components/navigation/Sidebar.vue";

const router = useRouter();
const route = useRoute();
const store = useStore();
const error = ref(null);

watch(route, () => {
	window.scrollTo(0, 0)
})

onMounted(async () => {
	if (localStorage.getItem('token') !== null){
		await fetch_get_role();
		store.username = localStorage.getItem('username');
		store.first_name = localStorage.getItem('first_name');
		store.last_name = localStorage.getItem('last_name');
	}
})


const autoRefreshControl = reactive({
  paused: false,
  pause() {
    this.paused = true
  },
  resume() {
    this.paused = false
  }
})

provide('autoRefreshControl', autoRefreshControl)

async function fetch_get_role(){
	store.loading = true;
	const response = await auth_fetch('/api/get_role/', {method: 'GET'});
	if (!response.ok){
		store.loading = false;
		const err = await error_message(response);
    toast.add({ severity: 'error', summary: 'Fetch Error', detail: err.message || "Fatal error", life: 3000 });
		return;
	}
	const json = await response.json();
	localStorage.setItem('role', json['role']);
	store.role = localStorage.getItem('role');
	localStorage.setItem('roles', JSON.stringify(json['roles']));
	store.roles = JSON.parse(localStorage.getItem('roles'));
	store.loading = false;
	
	const link = localStorage.getItem("link");
	if(link && link !== "/") {
		localStorage.removeItem("link");
		router.push(link);
	}
	else {
		if(link && link === "/") {
			localStorage.removeItem("link");
		}
		navigate_to(store.role, router, error);
	}
}

</script>

<template>
  <div v-if="store.loading" class="overlay">
    <div class="spinner"></div>
  </div>

  <Navbar></Navbar>

	<div class="d-flex flex-grow-1 overflow-hidden">

      <Sidebar v-if="store.role != null"></Sidebar>

      <div class="main-content container-fluid px-4 py-3 bg-body-tertiary overflow-y-scroll">
          <router-view />
      </div>

	</div>


  <ConfirmDialog group="firstConfirmDialog" />
  <ConfirmDialog group="secondConfirmDialog" />
  <Toast />

</template>




<style scoped>

.main-content {

  transition: all 0.3s ease;
  overflow-y: scroll;
}

</style>
