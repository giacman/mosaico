<!-- JSONEditor.vue -->
<template>
  <form class="">
    <!-- Renderizzo il form solo quando lo schema è stato dereferenziato -->
    <FieldRenderer
        v-if="resolvedSchema"
        v-model="jsonData"
        :schema="resolvedSchema"
        :translation-mode="translationMode"
        :key="schemaVersion"
        :parent="'root'"
    />
  </form>
</template>

<script setup>
import { ref, onMounted, watch, provide } from 'vue'
import FieldRenderer from './FieldRenderer.vue'
import $RefParser from "@apidevtools/json-schema-ref-parser";
import Ajv from 'ajv'

const jsonData = defineModel('jsonData',{ type: Object, default: {} })
const isValid = defineModel('isValid', { type: Boolean, default: false })


const props = defineProps({
  schema: { type: Object, required: true },
  translationMode: { type: Boolean, default: false }
})

const emit = defineEmits([
  'input-value-changed',
  'output-value--changed'
])

provide('notifyInputValueChange', () => {
  emit('input-value-changed',  true)
})

provide('notifyOutputValueChange', () => {
  emit('output-value-changed', true)
})

const schemaVersion = ref(0)
const resolvedSchema = ref(null)
let validateFn = null

async function resolveSchema() {
  resolvedSchema.value = await $RefParser.dereference(props.schema, { mutateInputSchema: false })
  const ajv = new Ajv({ allErrors: true, strict: false })
  validateFn = ajv.compile(resolvedSchema.value)
}

// dereferenzia allo start
onMounted(resolveSchema)

// se cambia schema → reset + rifaccio il FieldRenderer
watch(
    () => props.schema,
    async (newSchema, oldSchema) => {
      if (newSchema !== oldSchema) {
        await resolveSchema()
        jsonData.value = {}
        schemaVersion.value++
      }
    }
)

// **Il watch profondo** che esegue la validazione a ogni modifica
watch(
    jsonData,
    (newVal) => {
      if (!validateFn) return
      isValid.value = validateFn(newVal)
    },
    { deep: true, immediate: true }
)
</script>


<style scoped>

</style>
