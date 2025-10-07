<script setup>

import {
  formatDate,
  getAIStateClassColor,
  getAIStateLabel,
  getContentStatusClassColor,
  getContentStatusLabel
} from "@/utils.js";
import {
  getUniformTranslationStates,
  getUniformTranslationStatuses
} from "@/components/translations/translation_utils.js";
import {computed, onMounted, onUnmounted, ref} from "vue";
import {useRoute} from 'vue-router'

const route = useRoute();

const props = defineProps({
  content: {required: true}
})

const uniformTranslationStatus = computed(() => getUniformTranslationStatuses(props.content))

const uniformTranslationState = computed(() => getUniformTranslationStates(props.content))

const contentStatus = computed(() => getContentStatusLabel(props.content))
const contentStatusColor = computed(() => getContentStatusClassColor(props.content))

const aiStateLabel = computed(() => getAIStateLabel(uniformTranslationState.value.state))
const aiStateColor = computed(() => getAIStateClassColor(uniformTranslationState.value.state))

// reactive per la larghezza viewport
const windowWidth = ref(window.innerWidth);

// aggiorno windowWidth al resize
function onResize() {
  windowWidth.value = window.innerWidth;
}

onMounted(() => {
  window.addEventListener('resize', onResize);
});
onUnmounted(() => {
  window.removeEventListener('resize', onResize);
});

// calcola quante bandierine far vedere in base ai breakpoint di Bootstrap 5.3
const visibleCount = computed(() => {
  const w = windowWidth.value;
  if (w >= 1200) {       // xl e xxl
    return 5;
  } else if (w >= 992) { // lg
    return 4;
  } else if (w >= 768) { // md
    return 3;
  } else if (w >= 576) { // sm
    return 2;
  } else {               // xs
    return 0;
  }
});
</script>

<template>
  <tr class="content-header" data-bs-toggle="modal" :data-bs-target="'#staticBackdrop-' + content.id">
    <td class="fw-bold">{{ content.id }}</td>
    <td><span class="d-inline-block text-truncate">{{ content.title }}</span></td>
    <td class="fw-bold">{{ content.content_type }}</td>
    <td class="fw-bold">{{ content.data.type ? content.data.type : "-" }}</td>
    <td>
      <label class="badge text-uppercase" :class="contentStatusColor">
        {{ contentStatus }} <span v-if="contentStatus !== 'published'" class="text-uppercase fw-bold">({{
          uniformTranslationStatus.status_num
        }}/{{ content.translations.length }})</span>
      </label>
    </td>
    <td>
      <div class="d-flex align-items-center">
        <!-- mostro solo le prime visibleCount bandierine -->
        <div
            v-for="(translation, idx) in content.translations.slice(0, visibleCount)"
            :key="idx"
            class="fi fis rounded-circle"
            :class="'fi-' + translation.language.country_alpha2.toLowerCase()"
        ></div>

        <!-- ellissi solo se ci sono bandierine nascoste -->
        <span
            v-if="visibleCount > 0 && content.translations.length > visibleCount"
            class="ms-1"
        >
        &hellip;
      </span>

        <!-- numero totale -->
        <div class="ms-1 mb-1">
          ({{ content.translations.length }})
        </div>
      </div>
    </td>
    <td>{{ formatDate(content.created_at) }}</td>
    <td v-if="!['validated', 'published'].includes(route.name)">
      <label class="badge text-uppercase" :class="aiStateColor">
        {{ aiStateLabel }} ({{ uniformTranslationState.state_num }}/{{
          content.translations.length
        }})
      </label>
    </td>
  </tr>
</template>

<style scoped>

</style>