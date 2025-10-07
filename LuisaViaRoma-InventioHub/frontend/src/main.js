import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap';

import "../node_modules/flag-icons/css/flag-icons.min.css";
import 'primeicons/primeicons.css'
import 'vue-multiselect/dist/vue-multiselect.css'

import { createApp } from 'vue'
import App from './App.vue'
import { createRouter, createWebHistory } from 'vue-router';
import { createPinia } from 'pinia'
import Login from './components/Login.vue'
import Copywriter from '@/components/generation/Drafts.vue'
import ContentEditor from './components/ContentEditor.vue'
import CopywriterTranslations from './components/roles/copywriter/CopywriterTranslations.vue'
import Validated from './components/Validated.vue';
import Approvatore from './components/Approvatore.vue';
import TraduttoreTranslations from '@/components/roles/translator/TraduttoreTranslations.vue';

import PrimeVue from 'primevue/config';
import Aura from '@primeuix/themes/aura';
import ConfirmationService from 'primevue/confirmationservice';
import ConfirmDialog from 'primevue/confirmdialog';
import Toast from 'primevue/toast';
import ToastService from 'primevue/toastservice';

import NewContentEditor from "@/components/NewContentEditor.vue";
import ApprovatoreTranslations from "@/components/roles/approver/ApprovatoreTranslations.vue";
import TraduttoreValidated from "@/components/roles/translator/TraduttoreValidated.vue";
import Published from "@/components/Published.vue";
import AdminManageLanguages from "@/components/roles/admin/AdminManageLanguages.vue";
import AdminManageRoles from "@/components/roles/admin/AdminManageRoles.vue";
import AdminManageTranslators from "@/components/roles/admin/AdminManageTranslators.vue";
import AdminManageLLMs from "@/components/roles/admin/AdminManageLLMs.vue";

import './assets/main.css'

const routes = [
	{ path: '/', name: 'Login', component: Login},
	{ path: '/guest', name: 'guest', component: Login},
	{ path: '/admin/languages', name: 'admin_languages', component: AdminManageLanguages, props: true},
	{ path: '/admin/roles', name: 'admin_roles', component: AdminManageRoles, props: true},
	{ path: '/admin/translators', name: 'admin_translators', component: AdminManageTranslators, props: true},
	{ path: '/admin/llms', name: 'admin_llms', component: AdminManageLLMs, props: true},

	{ path: '/copywriter', name: 'copywriter', component: Copywriter, props: true},
	{ path: '/new_content', name: 'new_content', component: NewContentEditor, props: true},
	{ path: '/edit_content/:content_id', name: 'edit_content', component: ContentEditor, props: true},
	{ path: '/translations', name: 'translations', component: CopywriterTranslations, props: true },

	{ path: '/validated', name: 'validated', component: Validated, props: true },
	{ path: '/published', name: 'published', component: Published, props: true },
	{ path: '/approvatore/drafts', component: Approvatore, props: true},
	{ path: '/approvatore/translations', component: ApprovatoreTranslations, props: true},
	{ path: '/traduttore/translations', name: 'translator_translations', component: TraduttoreTranslations, props: true },
	{ path: '/traduttore/validated', name: 'translator_validated', component: TraduttoreValidated, props: true },
];

const router = createRouter({
	linkActiveClass: 'active',
	linkExactActiveClass: 'exact-active',
	history: createWebHistory(),
	routes,
});

const pinia = createPinia()
const app = createApp(App);
app.use(pinia);

app.use(ToastService);
app.use(PrimeVue, { theme: { preset: Aura, options: {
			darkModeSelector: '',
			cssLayer: false
		}} });
app.use(ConfirmationService);
app.component('ConfirmDialog', ConfirmDialog);
app.component('Toast', Toast);

app.use(router);
app.mount(('#app'));
