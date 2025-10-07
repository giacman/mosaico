<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import {
  auth_fetch,
  error_message,
  useStore,
  download_s3_file
} from '../utils';
import { useToast } from "primevue/usetoast";
const toast = useToast();
import { useRouter } from 'vue-router'
import JSONEditor from "@/components/json/JSONEditor.vue";
import Multiselect from "vue-multiselect";
import { useConfirm } from "primevue/useconfirm";


// TODO migliorare la gestione NEW CONTENT e EDIT CONTENT, ora ho fatto 2 file identici a cui si arriva con il router in modo diverso
const confirm = useConfirm();
const store = useStore()
const router = useRouter()

let schema = ref(null);
const formJSON = ref({});

const isValid = ref(false)

const canSave = computed(() => {
  return isValid.value
      && Boolean(
          validSchema.value,
          content.value.title,
          selected_language.value,
          selected_llm.value,
          selected_content_type.value
      )
})
const props = defineProps({
	content_id: Number,
});

const content = ref({
	id: '',
	title: '',
	llm: '',
	custom_prompt: ''
});

const content_types = ref([]);
const selected_content_type = ref({});
const llms = ref([]);
const selected_llm = ref({});
const languages = ref([]);
const selected_language = ref({});
const imageRef = ref(null);
const selectedFiles = ref([]);

const validSchema = ref(false);

let isMultimodal = ref(false);

const inputValueHasChanged = ref(false)
const outputValueHasChanged = ref(false)
let isNewContent = ref(false);

onMounted(() => {
	const fetchData = async () => {
		if(!props.content_id){
      await fetchGetContentTypes();
      isNewContent.value = true;
    }
    else
      await fetchGetContent(props.content_id)
		await fetchActiveLanguages();
		await fetchGetLLMs();
	};
	fetchData();
})

watch(selected_content_type, (newVal, oldVal) => {
  if(isNewContent.value)
    formJSON.value = {};
  fetchGetInputSchema(newVal.name)
});

// watch(() => props.content_id, (newId, oldId) => {
// 	if(newId == null){
//     formJSON.value = {};
// 		content.value = {
// 			id: '',
// 			title: '',
// 			llm: '',
// 			custom_prompt: '',
// 		}
// 		content_types.value = [];
// 		selected_content_type.value = '';
// 		llms.value = '';
// 		selected_llm.value = '';
// 		languages.value = '';
// 		selected_language.value = '';
// 		imageRef.value = null;
// 		selectedFiles.value = [];
// 		isMultimodal.value = true;
//
// 		fetchGetContentTypes();
// 		fetchActiveLanguages();
// 		fetchGetLLMs();
// 	}
// })

// Watcher su selected_llm
watch(
    selected_llm,
    (newVal, oldVal) => {
      for (const service of llms.value) {
        for (const model of service.models) {
          if (model.id === newVal.id) {
            if (service.multimodal) {
              isMultimodal.value = true
            }
            else{
              isMultimodal.value = false
              selectedFiles.value = []
              if (imageRef.value){
                imageRef.value.value = ''
              }
            }
            return
          }
        }
      }
    }
)

const handleFileChange = () => {
	const allowedTypes = [
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/webp',
    'text/plain',
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
    'text/markdown'
	];
	const maxSizeMB = 20;
	const maxSizeBytes = maxSizeMB * 1024 * 1024;
	const files = Array.from(imageRef.value.files);
	const validFiles = [];
	const invalidFiles = [];
	for (const file of files) {
		if (!allowedTypes.includes(file.type) || file.size > maxSizeBytes) {
			invalidFiles.push(file.name);
		} else {
			validFiles.push(file);
		}
	}
	if (invalidFiles.length) {
    toast.add({ severity: 'warn', summary: 'Upload', detail: `Some files are invalid or exceed 20MB: ${invalidFiles.join(', ')}`, life: 3000 });
		imageRef.value.value = ''; // Clear the input
		return;
	}

	const MAX_FILES = 5;

	const fileList = imageRef.value.files;
	const filesArray = Array.from(fileList);
	if (filesArray.length > MAX_FILES) {
    toast.add({ severity: 'warn', summary: 'Upload', detail: `You can only select up to ${MAX_FILES} files.`, life: 3000 });
		imageRef.value.value = ""; // Reset the file input
		selectedFiles.value = [];  // Clear selected files
		return;
	}
	selectedFiles.value = filesArray;
}

// remove selected file but not saved, just if we selected the wrong file and we want to remove it
async function removeFile(index) {
	selectedFiles.value.splice(index, 1);
	const dt = new DataTransfer();
	selectedFiles.value.forEach(file => dt.items.add(file));
	imageRef.value.files = dt.files;
}

async function fetch_delete_s3file(file_key, index) {
	store.loading = true;
	try {
		const response = await auth_fetch(`/api/delete_s3file/${file_key}/`, {method: 'DELETE'});
		const data = await response.json();
		if (!response.ok) {
			const err = await error_message(response);
			throw new Error(err);
		}
		content.value.s3files.splice(index, 1);

    toast.add({ severity: 'warning', summary: 'Confirmed', detail: "File deleted...", life: 3000 });
	} 
	catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
		store.loading = false;
	}
	store.loading = false;
}

function onDeleteS3File(file_name, file_key, index){
  confirm.require({
    group: 'firstConfirmDialog',
    message:`Are you sure you want to delete ${file_name}?`,
    header: 'Delete file',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Delete',
    rejectLabel: 'Cancel',
    acceptProps: {
      label: 'Delete',
      severity: 'danger'
    },
    rejectProps: {
      label: 'Cancel',
      severity: 'secondary',
      outlined: true
    },
    accept: fetch_delete_s3file(file_key, index),
    reject: () => {}
  })
}


async function fetchGetInputSchema(content_type_name) {

  if(!isNewContent.value){
    schema.value = content.value.schema;
    validSchema.value = true;
    return
  }

  validSchema.value = false;

  try {
    let url = `/api/get_content_types/?content_type=${content_type_name}`;

    const response = await auth_fetch(url, {method: 'GET'});
    const data = await response.json();
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    if(data['schema']){
      schema.value = JSON.parse(data['schema']);
      validSchema.value = true;
    }

    else
      throw new Error("Error in retrieving input json schema.");
  }
  catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
  }
}

async function fetchGetContentTypes() {
	try {
		let url = '/api/get_content_types/';

		const response = await auth_fetch(url, {method: 'GET'});
		const data = await response.json();
		if (!response.ok) {
			const err = await error_message(response);
			throw new Error(err);
		}
		content_types.value = data['content_types'];
	} 
	catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
  }
}



async function fetchActiveLanguages() {
	try {
    const response = await auth_fetch('/api/get_languages/', {method: 'GET'}, false)
    if (!response.ok) {
      console.error(await error_message(response))
      return []
    }
    const langs = await response.json()
    languages.value = langs.map(l => ({complete_name: `${l.name} (${l.lang_alpha2}-${l.country_alpha2})`, ...l}))
  }
	catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
	}
}

async function fetchGetLLMs() {
	try {
		const response = await auth_fetch('/api/get_llms/', {method: 'GET'});
		if (!response.ok) {
			const err = await error_message(response);
			throw new Error(err);
		}
		const data = await response.json();
		llms.value = data['llms'];
	} 
	catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
	}
}

async function fetchGetContent(content_id) {
	try {
		const response = await auth_fetch(`/api/get_content/${content_id}/`, {method: 'GET'});
		if (!response.ok) {
			const err = await error_message(response);
			throw new Error(err);
		}
		const data = await response.json();
    data.language["complete_name"] = `${data.language.name} (${data.language.lang_alpha2}-${data.language.country_alpha2})`
		selected_language.value = data.language;
		selected_llm.value = data.selected_llmmodel;
		selected_content_type.value = data.content_type;
		formJSON.value = data.data;
    content.value = data;
    isValid.value = true
    validSchema.value = true;
	} 
	catch (err) {
    toast.add({ severity: 'error', summary: 'Fetch Error', detail: err.message || "Fatal error", life: 3000 });
	}
}




function validateRequiredFields() {
  if (!canSave.value) {
    toast.add({
      severity: 'warn',
      summary: 'Error',
      detail: 'Please fill in all required fields.',
      life: 3000
    });
    return false;
  }
  return true;
}


function buildBaseFormData() {
  const formData = new FormData();

  formData.append("content_type", content.value.content_type_id ? content.value.content_type_id : selected_content_type.value.id);
  formData.append("title", content.value.title);
  formData.append("language", selected_language.value.id);
  formData.append("llmmodel", selected_llm.value.id);
  formData.append("custom_prompt", content.value.custom_prompt);
  formData.append("data", JSON.stringify(formJSON.value));

  for (const file of selectedFiles.value) {
    formData.append('files', file);
  }

  return formData;
}


async function fetchSaveContent(){
  store.loading = true;
  try {
    let formData = buildBaseFormData();

    let url = `/api/update_content/${content.value.id}/`
    let method = 'PUT'

    if(!content.value.id){
      formData.append("creator", localStorage.getItem("user_id"));
      formData.append("status", "bozza");
      url = `/api/create_content/`
      method = 'POST'
    }

    const response = await auth_fetch(
        url,
        { method: method, body: formData }, false
    );
    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    toast.add({ severity: 'success', summary: 'Confirmed', detail: "Draft saved", life: 3000 });
    router.push('/copywriter');
  }
  catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
    store.loading = false;
  }
}

async function fetchSendToAI(){
  if(!validateRequiredFields())
    return

  try{
    store.loading = true
    let formData = buildBaseFormData();
    formData.append("state", "sent");


    let url = `/api/update_content/${content.value.id}/`
    let method = 'PUT'

    if(!content.value.id){
      formData.append("creator", localStorage.getItem("user_id"));
      formData.append("status", "bozza");
      url = `/api/create_content/`
      method = 'POST'
    }

    const response = await auth_fetch(
        url,
        {
          method: method, body: formData
        },
        false
    );

    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    toast.add({ severity: 'success', summary: 'Confirmed', detail: "Draft sent to AI", life: 3000 });
    router.push('/copywriter');
  }
  catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
    store.loading = false;
  }

}

async function fetchSendForReview(){
  if(!validateRequiredFields())
    return

  store.loading = true

  try{

    if(!content.value.id || content.value.state === "local")
      throw new Error("You cannot send for review without text generation")

    let formData = buildBaseFormData();
    formData.append("status", "review");

    const response = await auth_fetch(
        `/api/update_content/${content.value.id}/`,
        {
          method: 'PUT', body: formData
        },
        false
    );

    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    toast.add({ severity: 'success', summary: 'Confirmed', detail: "Draft sent for review", life: 3000 });
    router.push('/copywriter');
  }
  catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || "Fatal error", life: 3000 });
  }

  store.loading = false;

}

function onSendForReview(){

  const baseOptions = {
    header: 'Send for review?',
    rejectProps: {
      icon: 'pi pi-times',
      label: 'Cancel',
      severity: 'secondary',
      outlined: true
    },
    acceptProps: {
      label: 'Send',
      severity: 'success',
      icon:'pi pi-send'
    },
  };

  confirm.require({
    ...baseOptions,
    group: 'firstConfirmDialog',
    message: 'Do you want to send to review this content?',
    icon: 'pi pi-question-circle',
    accept: ()=> {
      if(inputValueHasChanged.value)
        confirm.require({
          ...baseOptions,
          group: 'secondConfirmDialog',
          message: 'Seems that you have changed an input value without regenerate through AI.\nAre you sure to send in review?',
          icon: 'pi pi-exclamation-triangle',
          accept: ()=> {
              fetchSendForReview()
          },
          reject: () => {}
        })
      else
        fetchSendForReview()
    },
    reject: () => {}
  })
}



</script>

<template>
<span class="display-6 text-body-tertiary fw-bold">
      {{ isNewContent ? "New": "Edit"}} Content
</span>
<div class="row justify-content-center mt-3 mx-4 bg-body">
	<div class="border border-1 rounded shadow-sm p-4 mx-5">
	<div class="row d-flex align-items-stretch input-values">

	<div class="col-md-6 p-4">
		<label>Task name *</label>
		<input class="form-control mb-3 shadow-sm" type="text" v-model="content.title" placeholder=""/>

		<label>Language *</label>
    <Multiselect
        class="mb-3 shadow-sm"
        v-model="selected_language"
        :options="languages"
        track-by="complete_name"
        label="complete_name"
        :searchable=false
        :allow-empty=false
        :close-on-select=true
        :hide-selected=true
    >
      <template #singleLabel="{ option }">
        <span :class="['fi fis rounded-circle me-2', 'fi-'+option.country_alpha2?.toLowerCase()]"/>
        <span>{{ option.complete_name }}</span>
      </template>

      <template #option="{ option }">
        <span :class="['fi fis rounded-circle me-2', 'fi-'+option.country_alpha2?.toLowerCase()]"/>
        <span class="option__title me-2">{{ option.complete_name }}</span>
      </template>
    </Multiselect>

		<label>LLM *</label>
    <Multiselect id="option-groups"
                 v-model="selected_llm"
                 :options="llms"
                 :multiple="false"
                 :allow-empty=false
                 :close-on-select=true
                 group-values="models"
                 group-label="name"
                 placeholder="Type to search"
                 track-by="name"
                 label="name"
                 class="mb-3 shadow-sm"

    >
      <template v-slot:noResult>Oops! No elements found. Consider changing the search query.</template>
    </Multiselect>


    <label>Files</label>
    <input class="form-control mb-3 shadow-sm" type="file" ref="imageRef" multiple @change="handleFileChange"
      :accept=" isMultimodal ? '.jpg,.jpeg,.png,.webp,.txt,.pdf,.docx,.md' : '.txt,.pdf,.docx,.md'"/>
    <ul v-if="selectedFiles.length">
      <li class="mt-2" v-for="(file, index) in selectedFiles" :key="file.name + index">
        {{ file.name }}
        <button @click="removeFile(index)" class="btn btn-sm btn-danger ms-2">
          <IconFasTrash/>
        </button>
      </li>
    </ul>
		<ul>
		<li v-for="(file, index) in content.s3files" class="link-info mt-2" 
			style="cursor: pointer" @click="download_s3_file(store, file.name, file.key)">
			<strong class="text-truncate">{{file.name}}</strong>
			<button @click.stop="onDeleteS3File(file.name, file.key, index)" class="btn btn-sm btn-danger ms-2">
        <IconFasTrash/>
			</button>
		</li>
		</ul>
	</div>

	<div class="col-md-6 p-4">
		<label for="tipo">Content *</label>
    <multiselect v-if="isNewContent"
                 v-model="selected_content_type"
                 placeholder="Select a content category"
                 label="name"
                 track-by="name"
                 :options="content_types"
                 :allow-empty=false
                 :close-on-select=true
                 class="shadow-sm mb-3"
    >
      <template #singleLabel="props">
        <span>{{ props.option.name?.replace("_", " ")  }}</span>
      </template>
      <template #option="props">
        <div class="option__desc"><span class="option__title">{{ props.option.name.replace("_", " ") }}</span></div>
      </template>
    </multiselect>
    <div v-else class="border border-1 rounded shadow-sm form-select no-arrow mb-3">
      {{ content.content_type }}
    </div>

		<label>Custom Prompt</label>
		<textarea class="form-control shadow-sm" type="text" v-model="content.custom_prompt" rows="3"></textarea>
	</div>

	<div class="col-md-12 p-4">
		<div class="mt-5">
			<JSONEditor v-if="schema"
                  :schema="schema"
                  v-model:jsonData="formJSON"
                  v-model:isValid="isValid"
                  @input-value-changed="(event) => {inputValueHasChanged = event}"
                  @output-value-changed="outputValueHasChanged = $event"
      />
		</div>	
	</div>

  <div class="text-end">
    <button :disabled="!canSave" class="btn btn-success mx-2 text-uppercase fw-bold" @click="fetchSaveContent">
      <IconFa6SolidFloppyDisk class="me-1"/>
      Save
    </button>
    <button :disabled="!canSave" class="btn btn-info mx-2 text-uppercase fw-bold"
            @click="fetchSendToAI">
      <IconFasRocket/>
      Generate with AI
    </button>
    <button :disabled="!canSave" v-if="!isNewContent && ['bozza', 'bozza_rifiutata'].includes(content.status) && ['success'].includes(content.state)"
            class="btn btn-success mx-2 text-uppercase fw-bold"
            @click="onSendForReview">
      <IconFasEnvelope />
      Send for review
    </button>
  </div>

	</div>

	</div>
</div>


</template>

<style scoped>
  label{
    font-weight: bold;
    color: var(--bs-tertiary-color);
  }

  .form-select.no-arrow {
    background-image: none !important;
  }
</style>
