<script setup>
import {onMounted, ref, watch} from 'vue';
import {useCarouselController} from '@/stores/useCarouselStore.js';
import {Carousel as BSCarousel} from 'bootstrap';
import {getAIStateClassColor, getAIStateLabel} from "@/utils.js";
import {
  getTranslationStatusClassColor,
  getTranslationStatusLabel
} from "@/components/translations/translation_utils.js";

const props = defineProps({
  translations: {
    type: Array,
    required: true
  },
  options: {
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
let instance = null;

const {currentSlide} = useCarouselController();

onMounted(() => {
  // Inizializza l’istanza Bootstrap
  instance = new BSCarousel(carouselRef.value, props.options);

  // Sincronizza anche al cambiamento esterno (es. se qualcuno chiama to())
  carouselRef.value.addEventListener('slid.bs.carousel', e => {
    currentSlide.value = e.to;
  });

  // Imposta subito la slide iniziale
  instance.to(currentSlide.value);
});

watch(currentSlide, idx => {
  if (instance) {
    instance.to(idx);
  }
});
</script>

<template>
  <div ref="carouselRef" class="carousel carousel-fade ">
    <div class="carousel-inner">
      <div
          v-for="(translation, idx) in translations"
          :key="idx"
          class="carousel-item"
          :class="{ active: idx === currentSlide }"
      >
        <div class="container-fluid p-0 text-nowrap">
          <div class="row">
            <div class="col col-lg-6">
              <div class="text-body-tertiary fw-bold">Translation Status</div>
              <span class="badge text-uppercase" :class="getTranslationStatusClassColor(translation.status)">
                {{ getTranslationStatusLabel(translation.status) }}
              </span>
              <div v-if="translation.rejection_message"
                   class="my-2 text-wrap border border-danger rounded shadow-sm bg-danger py-2 px-3"
                   style="--bs-bg-opacity: .3;">
                {{ translation.rejection_message }}
              </div>
            </div>

            <div class="col col-lg-6">
              <div class="col col-lg-6 text-body-tertiary fw-bold">AI Request Status</div>
              <span class="badge text-uppercase" :class="getAIStateClassColor(translation.state)">
              {{ getAIStateLabel(translation.state) }}
          </span>
              <div v-if="translation.state_message"
                   class="my-2 text-wrap border border-danger rounded shadow-sm bg-danger py-2 px-3"
                   style="--bs-bg-opacity: .3;">
                {{ translation.state_message }}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>


<style scoped>

</style>