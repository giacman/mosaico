<script setup>
import {inject, onMounted, onUnmounted, ref, watch} from 'vue';
import {useCarouselController} from '@/stores/useCarouselStore.js';
import {Carousel as BSCarousel} from 'bootstrap';

import JSONEditor from "@/components/json/JSONEditor.vue";
import JSONViewer from "@/components/json/JSONViewer.vue";

import {auth_fetch, error_message, useStore} from "@/utils.js";
import {useConfirm} from "primevue/useconfirm";
import {useToast} from "primevue/usetoast";
import {useDeleteConfirm} from "@/composables/useDeleteConfirm.js";
import ApprovatoreTranslationRejectButton from "@/components/roles/approver/ApprovatoreTranslationRejectButton.vue";

import {useRouter} from 'vue-router'
import CopyCSVClipboard from "@/components/utils/CopyCSVClipboard.vue";
import CopyClipboard from "@/components/utils/CopyClipboard.vue";

const router = useRouter();
const confirm = useConfirm();
const toast = useToast();
const store = useStore()

const {confirmDelete} = useDeleteConfirm()

const autoRefreshControl = inject('autoRefreshControl')


const translations = defineModel('translations', {type: Array, required: true});

const props = defineProps({
  schema: {required: true},
  viewMode: {required: false, default: false},
  carouselOptions: {
    type: Object,
    default: () => ({
      interval: 0,
      touch: false,
      pause: false,
      keyboard: false,
      ride: false
    })
  }

});

const carouselRef = ref(null);
const editMode = ref(false);
let instance = null;

const {currentSlide} = useCarouselController();


onMounted(() => {

  // Inizializza l’istanza Bootstrap
  instance = new BSCarousel(carouselRef.value, props.carouselOptions);

  // Sincronizza anche al cambiamento esterno (es. se qualcuno chiama to())
  carouselRef.value.addEventListener('slid.bs.carousel', onSlide);

  // Imposta subito la slide iniziale
  instance.to(currentSlide.value);
});

onUnmounted(() => {
  carouselRef.value?.removeEventListener('slid.bs.carousel', onSlide);
});

watch(editMode, () => {
  if (props.viewMode.value) {
    editMode.value = false;
  }
}, {deep: true, immediate: true});


watch(currentSlide, idx => {
  if (instance) {
    instance.to(idx);
  }
});

watch(
    () => translations,
    (newTranslations) => {
      // se l’indice corrente è fuori range, lo riporto all’ultimo valido
      if (currentSlide.value >= newTranslations.length) {
        currentSlide.value = Math.max(0, newTranslations.length - 1)
        instance?.to(currentSlide.value)
      }
    },
    {deep: true}
)


function onSlide(e) {
  currentSlide.value = e.to;
}

let translationDataBackup = ref({});

function activateEditMode() {
  autoRefreshControl.pause()
  translationDataBackup.value = JSON.parse(JSON.stringify(translations.value[currentSlide.value].data));
  editMode.value = true;
}

function resetToOriginalTranslation() {
  translationDataBackup.value = {};
  editMode.value = false;
  autoRefreshControl.resume()
}

// COPYWRITER METHODS
async function deleteTranslation() {
  if (store.role !== "copywriter")
    return

  try {
    const response = await auth_fetch(
        `/api/remove_translation/${translations.value[currentSlide.value].id}/`,
        {
          method: 'DELETE',
        });

    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }

    translations.value.splice(currentSlide.value, 1);// 2nd parameter means remove one item only
    toast.add({severity: 'info', summary: 'Confirmed', detail: 'Translation deleted!', life: 3000});
  } catch (err) {
    toast.add({severity: 'error', summary: 'Error', detail: `Translation NOT deleted: ${err}`, life: 3000});
  }
}

// TRANSLATOR METHODS
async function saveTranslation() {
  if (!["traduttore", 'copywriter'].includes(store.role))
    return

  try {
    const payload = {
      id: translations.value[currentSlide.value].id,
      data: translationDataBackup.value
    }
    const response = await auth_fetch(
        `/api/update_translation_data/`,
        {
          method: 'PUT',
          body: JSON.stringify(payload)
        });

    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    toast.add({severity: 'success', summary: 'Confirmed', detail: 'Translation saved!', life: 3000});
    translations.value[currentSlide.value].data = translationDataBackup.value
    translationDataBackup.value = {}
  } catch (err) {
    toast.add({severity: 'error', summary: 'Error', detail: `Translation NOT saved: ${err}`, life: 3000});
  }
  editMode.value = false;
  autoRefreshControl.resume()
}

async function approveTranslation() {
  if (store.role !== "traduttore")
    return

  try {
    const response = await auth_fetch(
        `/api/approve_translation/${translations.value[currentSlide.value].id}/`,
        {
          method: 'PATCH'
        }
    );

    if (!response.ok) {
      const err = await error_message(response);
      throw new Error(err);
    }
    translations.value[currentSlide.value].status = 'validata';
    toast.add({severity: 'success', summary: 'Confirmed', detail: "Approved!", life: 3000});
  } catch (err) {
    toast.add({severity: 'error', summary: 'Error', detail: err.message || "Connection error", life: 3000});
  }
}

function onApprove() {
  confirm.require({
    group: 'firstConfirmDialog',
    message: 'Do you want to approve this translation?',
    header: 'Approve?',
    icon: 'pi pi-question-circle',
    rejectLabel: 'Cancel',
    rejectProps: {
      label: 'Cancel',
      severity: 'secondary',
      outlined: true
    },
    acceptProps: {
      label: 'Approve',
      severity: 'success'
    },
    accept: () => {
      approveTranslation();
    },
    reject: () => {

    }
  });
}

</script>

<template>
  <div class="d-flex">
    <div class="col d-flex  align-content-center align-items-center">
      <div class=" display-6 text-body-tertiary fw-bold text-nowrap">
        {{ translations[currentSlide]?.language?.name || '–' }} Data
      </div>
      <template v-if="translations[currentSlide]?.state === 'success'">
        <CopyClipboard
            :source="translations[currentSlide]?.data"
            :css_class="'fs-4 ms-3 text-black'"
        />
        <CopyCSVClipboard
            :source="translations[currentSlide]?.data"
            :css_class="'fs-4 ms-3 text-black'"
            :filename="`${translations[currentSlide]?.content}_${translations[currentSlide]?.language?.name}.csv`"
            :show-download="true"
        />
      </template>

    </div>


    <div class="col text-nowrap d-flex justify-content-start justify-content-xl-end">
      <template
          v-if="store.role === 'traduttore' && translations[currentSlide]?.status !== 'validata' && translations[currentSlide]?.state !== 'pending'">
        <button v-if="!editMode" class="btn btn-success ms-2 text-uppercase fw-bold" @click="onApprove"
                aria-label="Approve">
          <IconFasThumbsUp class=" pb-1"/>
          Approve
        </button>

        <button
            v-if="!editMode && !viewMode && translations[currentSlide]?.state !== 'pending'"
            class="btn btn-secondary text-uppercase fw-bold ms-2" @click="activateEditMode" aria-label="Edit">
          <IconFasWrench class="me-1"/>
          Edit
        </button>

        <template v-if="editMode && !viewMode">
          <button class="btn btn-success mx-2 text-uppercase fw-bold" @click="saveTranslation" aria-label="Save">
            <IconFa6SolidFloppyDisk class="me-1"/>
            Save
          </button>
          <button class="btn btn-warning text-uppercase fw-bold" @click="resetToOriginalTranslation"
                  aria-label="Cancel">
            <IconFasBan/>
            Cancel
          </button>
        </template>
      </template>
      <template
          v-else-if="store.role === 'copywriter' && !viewMode && ['validata','rifiutata'].includes(translations[currentSlide]?.status)">
        <button v-if="!editMode" class="btn btn-danger ms-2 text-uppercase fw-bold"
                @click="confirmDelete(deleteTranslation)" aria-label="Delete">
          <IconFasTrash class=""/>
        </button>

        <button
            v-if="!editMode &&  translations[currentSlide]?.state !== 'pending'"
            class="btn btn-secondary text-uppercase fw-bold ms-2" @click="activateEditMode" aria-label="Edit">
          <IconFasWrench class="me-1"/>
          Edit
        </button>

        <template v-if="editMode">
          <button class="btn btn-success mx-2 text-uppercase fw-bold" @click="saveTranslation" aria-label="Save">
            <IconFa6SolidFloppyDisk class="me-1"/>
            Save
          </button>
          <button class="btn btn-warning text-uppercase fw-bold" @click="resetToOriginalTranslation"
                  aria-label="Cancel">
            <IconFasBan/>
            Cancel
          </button>
        </template>
      </template>

      <ApprovatoreTranslationRejectButton
          v-else-if="store.role === 'approvatore' && translations[currentSlide]?.status === 'validata'"
          :trans_id="translations[currentSlide]?.id"
          @reject="router.push('/approvatore/translations')"
      />
    </div>

  </div>
  <div class="px-4 py-3 my-2 border border-1 rounded shadow-sm">
    <div ref="carouselRef" class="carousel carousel-fade ">
      <div class="carousel-inner">
        <div
            v-for="(translation, idx) in translations"
            :key="idx"
            class="carousel-item"
            :class="{ active: idx === currentSlide }"
        >
          <template v-if="store.role === 'copywriter'">
            <div v-if="translation.status === 'pending'"
                 class="d-flex align-items-center justify-content-center align-items-center">
              <div class="me-3">Waiting Translator...</div>
              <div class="spinner-border text-secondary" role="status"></div>
            </div>
            <template v-else>
              <JSONEditor v-if="editMode" v-model:jsonData="translationDataBackup" :schema="schema"
                          :translation-mode="true"/>
              <JSONViewer v-else :data="translation.data" :schema="schema"/>
            </template>
          </template>
          <template v-else-if="store.role === 'traduttore'">
            <template v-if="translation.state !== 'pending'">
              <JSONEditor v-if="editMode" v-model:jsonData="translationDataBackup" :schema="schema"
                          :translation-mode="true"/>
              <JSONViewer v-else :data="translation.data" :schema="schema"/>
            </template>
            <template v-else>
              <div class="d-flex align-items-center justify-content-center align-items-center">
                <div class="me-3">Waiting AI translation...</div>
                <div class="spinner-border text-secondary" role="status"></div>
              </div>
            </template>
          </template>
          <template v-else>
            <JSONViewer :data="translation.data" :schema="schema"/>
          </template>
        </div>
      </div>
    </div>
  </div>


</template>
