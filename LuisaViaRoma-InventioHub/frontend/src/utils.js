import { defineStore } from 'pinia'
import { ref } from 'vue'
import {getUniformTranslationStatuses} from "@/components/translations/translation_utils.js"
import { Modal as BSModal } from 'bootstrap'

export const useStore = defineStore('store1', () => {
	const loading = ref(false);
	const username = ref(null);
	const first_name = ref(null);
	const last_name = ref(null);
	const role = ref(null);
	const roles = ref([]);
	return { loading, username, first_name, last_name, role, roles }
})

export function navigate_to(role, router, error) {
	if (role === 'amministratore')
		router.push('/admin/languages');
	if (role === 'copywriter')
		router.push({ name: 'copywriter' });
	else if (role === 'approvatore')
		router.push('/approvatore/drafts');
	else if (role === 'traduttore')
		router.push('/traduttore/translations');
	else if (role === 'publisher')
		router.push({ name: 'published'});
	else if (role === 'guest')
		router.push({ name: 'guest'});
	else
		error.value = 'Ruolo sconosciuto';
}

export const dateOptions = {
	year: "numeric",
	month: "2-digit",
	day: "2-digit",
	hour: "2-digit",
	minute: "2-digit",
	second: "2-digit",
};

export function formatDate(UTCDateString, locale = undefined) {
	if (UTCDateString)
		return (new Date(UTCDateString)).toLocaleDateString(locale, dateOptions)
	else
		return "-"
}

export async function auth_fetch(url, options = {}, setContentType = true) {
	let token = localStorage.getItem("token");

	const headers = {
		...(options.headers || {}),
		Authorization: `Bearer ${token}`,
	};

	if (setContentType) {
		headers['Content-Type'] = 'application/json';
	}

	const authOptions = {
		...options,
		headers,
	};
  
	/*const authOptions = {
		...options,
		headers: {
			...(options.headers || {}),
			'ContentViewer-Type': 'application/json',
			Authorization: `Bearer ${token}`,
		},
	};*/
  
	let response = await fetch(url, authOptions);
  
	if (response.status === 401) {
		const refreshResponse = await fetch('/api/login/refresh/', {
			method: 'POST',
			credentials: 'include', // This ensures cookies are sent
		});
  
		if (refreshResponse.ok) {
			const data = await refreshResponse.json();
			localStorage.setItem('token', data.access);
			authOptions.headers.Authorization = `Bearer ${data.access}`;
			response = await fetch(url, authOptions);
		} 
		else {
			logout();
			toast.add({ severity: 'info', summary: 'Logged Out', detail: "Session scaduta", life: 3000 });
			window.location.href = "/";
			return response;
		}
	}
  
	return response;
}

export function logout(){
	localStorage.removeItem('token');
	localStorage.removeItem('user_id');
	localStorage.removeItem('username');
	localStorage.removeItem('first_name');
	localStorage.removeItem('last_name');
	localStorage.removeItem('role');
}

export async function error_message(response) {
	let errorData;

	// Proviamo a fare il parse del JSON; in caso di fallimento, usiamo statusText
	try {
		errorData = await response.json();
	} catch {
		return response.statusText || 'Errore sconosciuto';
	}

	// Se il server ha risposto con un messaggio di errore come stringa pura
	if (typeof errorData === 'string') {
		return errorData;
	}

	// Se ha restituito un array di messaggi direttamente
	if (Array.isArray(errorData)) {
		return errorData.join(', ');
	}

	// Se ha restituito un oggetto con campi => messaggi (array o stringa)
	return Object.entries(errorData)
		.map(([field, errors]) => {
			if (Array.isArray(errors)) {
				return `${field}: ${errors.join(', ')}`;
			} else {
				// qui errors è presumibilmente una stringa
				return `${field}: ${errors}`;
			}
		})
		.join('\n');
}

export function getRoleLabel(role) {
	switch (role.toLowerCase()) {
		case 'amministratore':
			return 'Administrator';
		case "approvatore":
			return 'Approver';
		case 'traduttore':
			return 'Translator';
		case 'publisher':
			return 'Publisher';
		case 'copywriter':
			return 'Copywriter';
		default:
			return role;
	}
}

export function getAIStateLabel(state) {
	switch (state) {
		case 'success':
			return 'generated';
		case 'failed':
			return 'failed';
		case 'sent':
		case 'pending':
			return 'pending';
		default:
			return 'unprocessed';
	}
}

export function getAIStateClassColor(state) {
	switch (state) {
		case 'success':
			return 'text-bg-success';
		case 'failed':
			return 'text-bg-danger';
		case 'sent':
		case 'pending':
			return 'text-bg-warning';
		default:
			return 'text-bg-secondary';
	}
}

export function getContentStatusClassColor(content) {
	const translationStatus = getUniformTranslationStatuses(content)

	switch (content.status) {
		case 'bozza':
			return 'text-bg-primary';
		case 'bozza_rifiutata':
			return 'text-bg-danger';

		case 'bozza_validata':
			switch(translationStatus.status) {
				case "unprocessed":
					return "text-bg-primary";
				default:
					return 'text-bg-success';
			}
		case "validata":
		case 'pubblicata':
			return 'text-bg-success';

		case 'review_traduzioni':
			switch(translationStatus.status){
				case "unprocessed":
					return "text-bg-primary";
				case "validata":
					return "text-bg-success";
				default:
					return "text-bg-warning";
			}
		default:
			return 'text-bg-warning';
	}
}

export function getContentStatusLabel(content) {
	const translationStatus = getUniformTranslationStatuses(content)

	switch (content.status) {
		case 'bozza':
			return 'draft';

		case "review":
			return "in review";
		case 'bozza_rifiutata':
			return 'rejected draft';

		case 'bozza_validata':
			switch(translationStatus.status) {
				case "unprocessed":
					return "to translate";
				default:
					return 'valid draft';
			}

			case 'validata':
			return 'validated';
		case 'pubblicata':
			return 'published';

		case 'review_traduzioni':
			switch(translationStatus.status){
				case "unprocessed":
					return "to translate";
				case "validata":
					return "to public";
				default:
					return "translating";
			}

		default:
			return content.status;

	}
}

export async function hideAndCleanup(modalId) {
	const el = document.getElementById(modalId);
	// Recupera o crea l'istanza Bootstrap
	const modalInstance = BSModal.getInstance(el) || BSModal.getOrCreateInstance(el);

	if(!el.classList.contains('show'))
		return
	// Attendi l'evento hidden.bs.modal
	await new Promise(resolve => {
		el.addEventListener('hidden.bs.modal', () => {
			resolve();
		}, { once: true });

		modalInstance.hide(); // Avvia la chiusura
	});

	// Rimuovi tutti i backdrop eventualmente residui
	document.querySelectorAll('.modal-backdrop').forEach(b => b.remove());
	// Ricompone lo stato del body
	document.body.classList.remove('modal-open');
	document.body.style.paddingRight = '';

	// Pulisce listener e dati interni
	modalInstance.dispose();
}


function getFilenameFromHeader(headers) {
	const cd = headers.get("Content-Disposition");
	if (!cd) return null;
	// prima prova filename*=UTF-8''
	let match = /filename\*\=UTF-8''([^;]+)/i.exec(cd);
	if (match && match[1]) {
		try {
			return decodeURIComponent(match[1]);
		} catch { /* fallthrough */ }
	}
	// fallback a filename=""
	match = /filename\="?([^\";]+)"?/.exec(cd);
	if (match && match[1]) {
		return match[1];
	}
	return null;
}

export async function download_s3_file(store, file_name, file_key) {
	store.loading = true;
	try {
		const response = await auth_fetch(`/api/download_s3_file/${file_key}/${file_name}/`, {method: 'GET'});
		if (!response.ok) {
			const err = await error_message(response);
			throw new Error(err);
		}
		const blob = await response.blob();
		const filename = getFilenameFromHeader(response.headers) || 'downloaded_file';
		// Create temporary download link
		const link = document.createElement('a');
		link.href = URL.createObjectURL(blob);
		link.download = filename;
		link.style.display = 'none';
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(link.href);
	} 
	catch (err) {
		toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
	}
	store.loading = false;
}

export async function openContentModal(){
	const modal_id = localStorage.getItem("editorModal_id");
	if(modal_id){
		localStorage.removeItem("editorModal_id");
		const el = document.getElementById("staticBackdrop-"+modal_id);
		if(el == null) return;
		const modalInstance = BSModal.getInstance(el) || BSModal.getOrCreateInstance(el);
		await new Promise(resolve => {
			el.addEventListener('hidden.bs.modal', () => {resolve();}, { once: true });
			modalInstance.show();
		});
	}
}


export function convertToTitleCase(str) {
	if (typeof str !== 'string') return str
	if (!str) return ""
	let splits = str.split(" ");
	if(splits.length <= 1)
		splits = str.split("_");
	if(splits[0].toLowerCase().includes("orderid"))
		splits.shift()
	return splits.join(" ").toLowerCase().replace(/\b\w/g, s => s.toUpperCase());
}
