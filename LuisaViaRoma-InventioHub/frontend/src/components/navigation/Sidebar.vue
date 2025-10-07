<script setup lang="js">
import {getRoleLabel, logout, useStore, auth_fetch, error_message} from '@/utils.js';
import {ref} from "vue";
import ChangeRoleButton from "@/components/navigation/ChangeRoleButton.vue";
import NotificationList from "@/components/navigation/NotificationList.vue";

const store = useStore();
const sidebarOpen = ref(true);

function do_logout() {
  logout();
  window.location.href = "/";
}

function toggleSidebar() {
  document.querySelector('.sidebar')?.classList.toggle('collapsed');
  document.querySelector('.collapsible-sidebar-button')?.classList.toggle('collapsed');
  document.querySelector('#toggle-button')?.classList.toggle('collapsed');
  sidebarOpen.value = !sidebarOpen.value;
}




</script>

<template>
  <div class="sidebar d-flex flex-column flex-shrink-0 flex-grow-1 position-relative bg-body-secondary">
    <button class="toggle-btn" role="button" data-bs-toggle="collapse" data-bs-target=".multi-collapse" @click="toggleSidebar">
      <IconFasChevronLeft/>
    </button>


    <router-link v-if="store.role === 'copywriter'" to="/new_content" class="collapsible-sidebar-button btn btn-success  mx-auto mt-5 mb-3 text-white d-flex align-items-center justify-center" :class="{'px-5': sidebarOpen}">
      <IconFasPlus/>
      <span class="multi-collapse collapse-horizontal collapse show text-nowrap fw-bold ps-2">New Content</span>
    </router-link>

    <div class="list-group mx-3 border rounded" :class="{'mt-5': store.role !== 'copywriter'}">

      <template v-if="store.role === 'copywriter'">

        <router-link to="/copywriter" class="list-group-item list-group-item-action d-flex align-items-center">
          <IconFa6SolidFeatherPointed/>
          <div class="multi-collapse collapse-horizontal collapse show text-nowrap">
            <div class="ps-3">Contents Drafts</div>
          </div>
        </router-link>

        <router-link to="/translations" class="list-group-item list-group-item-action  d-flex align-items-center">
          <IconFasLanguage/>
          <div class="multi-collapse collapse-horizontal collapse show text-nowrap">
            <div class="ps-3">Translations</div>
          </div>
        </router-link>

        <router-link :to="{ name: 'validated', params: { filter: 'validated' } }"
                     class="list-group-item list-group-item-action  d-flex align-items-center">
          <IconFa6SolidCircleCheck/>
          <div class="multi-collapse collapse-horizontal collapse show text-nowrap">
            <div class="ps-3">Validated</div>
          </div>
        </router-link>

      </template>

      <template v-else-if="store.role === 'approvatore'">
        <router-link to="/approvatore/drafts" class="list-group-item list-group-item-action  d-flex align-items-center">
          <IconFa6SolidFeatherPointed/>
          <div class="multi-collapse collapse-horizontal collapse show text-nowrap">
            <div class="ps-3">
              Content Drafts
            </div>
          </div>
        </router-link>

        <router-link to="/approvatore/translations" class="list-group-item list-group-item-action  d-flex align-items-center">
          <IconFasLanguage/>
          <div class="multi-collapse collapse-horizontal collapse show text-nowrap">
            <div class="ps-3">
              Translations
            </div>
          </div>
        </router-link>

      </template>

      <template v-else-if="store.role === 'amministratore'">
        <router-link to="/admin/languages" class="list-group-item list-group-item-action  d-flex align-items-center">
          <IconFa6SolidEarthEurope/>
          <div class="multi-collapse collapse-horizontal collapse show text-nowrap">
            <div class="ps-3">
              Languages
            </div>
          </div>
        </router-link>

        <router-link to="/admin/llms" class="list-group-item list-group-item-action  d-flex align-items-center">
          <IconFasBrain/>
          <div class="multi-collapse collapse-horizontal collapse show text-nowrap">
            <div class="ps-3">
              LLMs
            </div>
          </div>
        </router-link>

        <router-link to="/admin/roles" class="list-group-item list-group-item-action  d-flex align-items-center">
          <IconFasUsers/>
          <div class="multi-collapse collapse-horizontal collapse show text-nowrap">
            <div class="ps-3">
              Roles
            </div>
          </div>
        </router-link>

        <router-link to="/admin/translators" class="list-group-item list-group-item-action  d-flex align-items-center">
          <IconFasLanguage/>
          <div class="multi-collapse collapse-horizontal collapse show text-nowrap">
            <div class="ps-3">
              Translators
            </div>
          </div>
        </router-link>

      </template>

      <template v-else-if="store.role === 'traduttore'">
        <router-link to="/traduttore/translations" class="list-group-item list-group-item-action  d-flex align-items-center">
          <IconFasLanguage/>
          <div class="multi-collapse collapse-horizontal collapse show text-nowrap">
            <div class="ps-3">
              Translations
            </div>
          </div>
        </router-link>

        <router-link to="/traduttore/validated"
                     class="list-group-item list-group-item-action  d-flex align-items-center">
          <IconFa6SolidCircleCheck/>
          <div class="multi-collapse collapse-horizontal collapse show text-nowrap">
            <div class="ps-3">Validated</div>
          </div>
        </router-link>
      </template>

      <template v-if="!['guest', 'amministratore'].includes(store.role)">
        <router-link to="/published"
                     class="list-group-item list-group-item-action  d-flex align-items-center">
          <IconFa6SolidFlagCheckered/>
          <div class="multi-collapse collapse-horizontal collapse show text-nowrap">
            <div class="ps-3">Published</div>
          </div>
        </router-link>
      </template>




    </div>

    <div v-if="sidebarOpen && store.role !== 'amministratore'" class="mt-5 p-3 d-flex flex-column position-relative overflow-hidden" style="height: auto; max-height: 50vh;">
      <NotificationList/>
    </div>

    <div class="d-flex flex-column profile-section mt-auto p-3">
      <div class="d-flex flex-grow-1 align-items-center">
        <img src="https://randomuser.me/api/portraits/women/12.jpg" class="profile-picture flex-grow-1 rounded-circle"
             alt="Profile">
        <div class="multi-collapse collapse-horizontal collapse show text-nowrap ms-3 profile-info w-75">
          <h6 class="">{{ store.first_name }} {{ store.last_name }}</h6>
          <small class="text-muted text-uppercase">{{ getRoleLabel(store.role) }}</small>
        </div>
      </div>


        <div class="d-flex flex-column align-items-center">
          <div class="mx-auto my-3">
            <ChangeRoleButton :context="'sidebar'"/>
          </div>
          <a class="btn btn-danger mx-auto text-uppercase d-flex align-items-center" @click="do_logout();">
            <IconFa6SolidArrowRightFromBracket/>
            <div class="multi-collapse collapse-horizontal collapse show text-nowrap">
              <div class="ps-2">
                Logout
              </div>
            </div>
          </a>
        </div>



    </div>
  </div>
</template>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  height: 100%;
  transition: all 0.3s ease;
  border-right: 1px solid lightgray;
}


.sidebar.collapsed {
  width: var(--sidebar-width-collapsed);
}

.collapsible-sidebar-button.collapsed,  .collapsible-sidebar-button.collapsed.active{
  padding: 0.50rem !important;
}

.profile-section {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.profile-picture {
   width: 35%;
 }

.profile-picture {
  width: 35%;
}

.toggle-btn {
  position: absolute;
  right: -15px;
  top: 50%;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  border: none;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  z-index: 100;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.toggle-btn.collapsed {
  transform: rotate(180deg);
}

</style>
