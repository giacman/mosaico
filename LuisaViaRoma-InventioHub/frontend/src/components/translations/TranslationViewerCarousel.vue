<script setup>
import {onMounted, onUnmounted, ref, watch} from 'vue';
import {useCarouselController} from '@/stores/useCarouselStore.js';
import {Carousel as BSCarousel} from 'bootstrap';
import JSONViewer from "@/components/json/JSONViewer.vue";


import {useStore} from "@/utils.js";
import {useConfirm} from "primevue/useconfirm";
import {useToast} from "primevue/usetoast";

import {useRouter} from 'vue-router'
import CopyCSVClipboard from "@/components/utils/CopyCSVClipboard.vue";
import CopyClipboard from "@/components/utils/CopyClipboard.vue";

const router = useRouter();
const confirm = useConfirm();
const toast = useToast();
const store = useStore()


const translations = defineModel('translations', {type: Array, required: true});

const props = defineProps({
  schema: {required: true},
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

let instance = null;
const carouselRef = ref(null);
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
</script>

<template>
  <div class="row align-items-center">
    <div class="col d-flex  align-content-center align-items-center">
      <div class=" display-6 text-body-tertiary fw-bold text-nowrap">
        {{ translations[currentSlide]?.language?.name || '–' }} Data
      </div>
      <template v-if="translations[currentSlide]?.status === 'validata'">
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
          <JSONViewer :data="translation.data" :schema="schema"/>
        </div>
      </div>
    </div>
  </div>


</template>
