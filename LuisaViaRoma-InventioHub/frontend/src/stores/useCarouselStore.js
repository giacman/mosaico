import { ref } from 'vue';

const currentSlide = ref(0);

export function useCarouselController() {
    return { currentSlide };
}