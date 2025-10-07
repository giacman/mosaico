
<script setup>

import {computed} from "vue";
import CopyClipboard from "@/components/utils/CopyClipboard.vue";
import {convertToTitleCase} from "@/utils.js";

const props = defineProps({
  name:     { type: [String, Number], default: null },
  outputFields:   { type: Set, default: new Set},
  node:     { required: true },
  parent:   { type: String, default: "" },
  level:    { type: Number, default: 0 },
  path:     { type: Array, default: () => [] },
})

const isArray     = computed(() => Array.isArray(props.node))
const isObject    = computed(() => !isArray.value && props.node !== null && typeof props.node === 'object')
const isPrimitive = computed(() => !isArray.value && !isObject.value)

const isOutputField = computed(() => props.outputFields.has(props.name.toLowerCase()))

function returnCorrectedNodeList(node){
  if(node.length === 0)
    node.push(false)
  return node
}

</script>



<template>
  <div class="p-0" :class=" {'ms-3': level > 1 && !['list', 'object'].includes(parent), 'ps-3 list-group-item': ['list'].includes(parent), 'me-3':isPrimitive && !['list'].includes(parent)} ">
    <!-- Primitive values -->
    <template v-if="isPrimitive">
      <div v-if="name !== null" class="node-render-title py-2" :class="{'text-danger': isOutputField}">
        {{ convertToTitleCase(name) }}<span v-if="isOutputField">(Output Field)</span>:
      </div>
      <div class="primitive-render position-relative text-black pe-4 pe-md-5 py-2"
           :class="{'border border-1 rounded shadow-sm ms-2 mb-2 ps-3': parent !== 'list'}"
      >
        {{node || '-'}}
        <CopyClipboard v-if="node" :source="node" :css_class="'position-absolute top-0 end-0 m-2 text-black'"></CopyClipboard>
      </div>
    </template>

    <!-- Arrays -->
    <template v-else-if="isArray">
      <div v-if="name !== null" class="node-render-title py-2" :class="{'text-danger': isOutputField}">
        {{ convertToTitleCase(name) }}<span v-if="isOutputField">(Output Field)</span>:
      </div>
      <div class="list-render my-2 ms-2 me-3 border border-1 rounded shadow-sm" :class="{ 'list-group list-group-flush': parent !== 'object'}">
        <ViewRenderer
          v-for="(item, idx) in returnCorrectedNodeList(node)"
          :key="idx"
          :parent="'list'"
          :node="item"
          :level="level + 1"
          :path="[...path, idx]"
          :outputFields="outputFields"
        />
      </div>
    </template>

    <!-- Objects -->
    <template v-else>
      <div class="node-render-title" v-if="name !== null">{{ convertToTitleCase(name) }}:</div>
      <div class="object-render " :class="{'mb-3' : level > 1}">
        <ViewRenderer
          v-for="(value, key) in node"
          :key="key"
          :name="key"
          :parent="level === 0 ? '':'object'"
          :node="value"
          :level="level + 1"
          :path="[...path, key]"
          :outputFields="outputFields"
        />
      </div>
    </template>
  </div>
</template>


<style scoped>
.node-render-title{
  color: var(--bs-tertiary-color);
  font-weight: bold;
}
</style>

