<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { navigate_to, useStore } from '../utils';

const token = ref(null);
const router = useRouter();
const store = useStore();
const username = ref('')
const password = ref('')
const error = ref(null)

const GOOGLE_OAUTH_CALLBACK = import.meta.env.VITE_GOOGLE_OAUTH_CALLBACK;
const GOOGLE_OAUTH_CLIENT_ID = import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID

function handleCredentialResponse(response) {
	store.loading = true;
	fetch(GOOGLE_OAUTH_CALLBACK, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ access_token: response.credential }),
		credentials: "include"
	})
	.then(res => res.json())
	.then(data => {
		store.loading = false;
		localStorage.setItem('user_id', data.id);
		localStorage.setItem('username', data.username);
		localStorage.setItem('first_name', data.first_name);
		localStorage.setItem('last_name', data.last_name);
		localStorage.setItem('token', data.access);
		localStorage.setItem('role', data.role);
		localStorage.setItem('roles', JSON.stringify(data.roles));
		store.username = data.username;
		store.first_name = data.first_name;
		store.last_name = data.last_name;
		store.role = data.role;
		store.roles = data.roles;
		// Redirect in base al ruolo
		navigate_to(data.role, router, error);
	});
	store.loading = false;
}

onMounted(() => {
	const script = document.createElement('script');
	script.src = 'https://accounts.google.com/gsi/client';
	script.async = true;
	script.defer = true;
	script.onload = () => {
		window.google.accounts.id.initialize({
			client_id: GOOGLE_OAUTH_CLIENT_ID,
			callback: handleCredentialResponse,
		})
		window.google.accounts.id.renderButton(
			document.getElementById('google-button'),
			{ theme: 'filled_white', size: 'large', text: 'signin_with' }
		)
	}
	document.head.appendChild(script);	

	token.value = localStorage.getItem("token");
})

const handleLogin = async () => {
	store.loading = true;
	error.value = null
	try {
		const response = await fetch('/api/login/', {
			method: 'POST',
			headers: {'Content-Type': 'application/json'},
			body: JSON.stringify({
				username: username.value,
				password: password.value
			})
		})

		if (!response.ok)
			throw new Error('Login fallito');

		store.loading = false;
		const data = await response.json();
		const { access, user} = data;
		localStorage.setItem('user_id', user.id);
		localStorage.setItem('username', user.username);
		localStorage.setItem('first_name', user.first_name);
		localStorage.setItem('last_name', user.last_name);
		localStorage.setItem('token', access);
		localStorage.setItem('role', user.role);
		localStorage.setItem('roles', JSON.stringify(user.roles));
		store.username = user.username;
		store.first_name = user.first_name;
		store.last_name = user.last_name;
		store.role = user.role;
		store.roles = user.roles;
		// Redirect in base al ruolo
		navigate_to(user.role, router, error);
	} 
	catch (err) {
		console.error(err);
		error.value = 'Invalid user or password';
	}
	store.loading = false;
}

</script>

<template>

<div v-if="store.role != null && store.role == 'guest'" class="login-container">
	<p>Wait for an admin to assign you a role.</p>
</div>

<div v-else-if="token == null" class="login-container">
	<h2>Login</h2>
	<form @submit.prevent="handleLogin">
	<div>
		<label for="username">Username:</label>
		<input class="form-control" v-model="username" type="text" id="username" required />
	</div>

	<div>
		<label for="password">Password:</label>
		<input class="form-control" v-model="password" type="password" id="password" required />
	</div>

	<div class="btn-center">
		<button class="btn btn-dark" type="submit">Login</button>
	</div>
	<div class="btn-center mt-4">
		<div id="google-button"></div>
	</div>

	<p v-if="error" class="error">{{ error }}</p>
	</form>
</div>
</template>

<style scoped>
.login-container {
	width: 350px;
	margin: auto;
	padding: 2rem;
	border: 1px solid #ccc;
	border-radius: 8px;
	margin-top: 10%;
}

input {
	display: block;
	width: 100%;
	margin-top: 0.5rem;
	margin-bottom: 1rem;
}

button {
	width: 100px;
	padding: 5px;
}

.btn-center {
	width: 100%;
	height: auto;
	text-align: center;
}

.error {
	color: #ffc107;
	margin-top: 1rem;
	text-align: center;
}
</style>

