<script setup lang="js">
import logoUrl from '@/assets/logos/luisaviaroma_logo.png'
import inventioLogoUrl from '@/assets/logos/inventiohub_logo.png'
import {getRoleLabel, useStore} from "@/utils.js";
import ChangeRoleButton from "@/components/navigation/ChangeRoleButton.vue";

const store = useStore();

</script>

<template>
  <nav class="navbar navbar-expand-lg bg-body-tertiary px-3" style="border-bottom: 1px solid lightgray">
    <div class="container-fluid">
      <a class="d-flex align-items-center navbar-brand me-auto" href="/">
        <img :src="inventioLogoUrl" alt="LuisaViaRoma logo" width="auto" height="32" class="d-inline-block align-text-top mb-1">
        <span class="fw-bold ms-1 me-2">X</span>
        <img :src="logoUrl" alt="LuisaViaRoma logo" width="auto" height="16" class="d-inline-block align-text-top">
      </a>

      <span v-if="store.role != null" class="pe-3">Logged as: <span class="text-uppercase">{{
          getRoleLabel(store.role)
        }}</span></span>

      <ChangeRoleButton :context="'navbar'"/>


    </div>
  </nav>
</template>

<style scoped>

</style>
