<script setup lang="ts">
import TranslationsRow from "@/components/translations/TranslationsRow.vue";
import TranslationsModalFooter from "@/components/translations/TranslationsModalFooter.vue";
import TranslationModalBody from "@/components/translations/TranslationModalBody.vue";
import Table from "@/components/Table.vue";

import {useRoute} from 'vue-router'

const route = useRoute();

const props = defineProps({
  contents: {
    type: Array,
    default: () => []
  }
})


</script>

<template>

  <Table :contents="contents">
    <template #header>
      <tr>
        <th scope="col">#</th>
        <th scope="col">Name</th>
        <th scope="col">Content</th>
        <th scope="col">Type</th>
        <th scope="col">Status</th>
        <th scope="col"> Languages</th>
        <th scope="col">Creation Date</th>
        <th scope="col" v-if="!['validated', 'published'].includes(route.name)">AI State</th>
      </tr>
    </template>

    <template #row="{ content }">
      <TranslationsRow :content="content"/>
    </template>

    <template #modal-body="{ content }">
      <TranslationModalBody :content="content"/>
    </template>

    <template #modal-footer="{ content }">
      <TranslationsModalFooter :content="content"/>
    </template>
  </Table>

</template>

<style scoped>

</style>