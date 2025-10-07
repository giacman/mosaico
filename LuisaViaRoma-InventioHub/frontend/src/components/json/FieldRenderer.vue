<template>
  <div class="mb-2" :class="['field-renderer-field-'+schema.type] ">
    <!-- Label -->
    <div class="d-flex my-2 me-3 align-items-center ">
      <label v-if="level>0" class="field-renderer-label form-label me-5 mb-0" :class="{'fs-3': level===0, 'text-danger': schema.trans_editable}">
        {{ convertToTitleCase(schema.title)}}<span v-if="schema.trans_editable">(Output Field)</span>:<span v-if="required && !translationMode"> *</span>
      </label>
      <template v-if="schema.type==='array' && !translationMode">
        <template v-if="schema.items && schema.items.anyOf">
          <button class="btn btn-sm btn-primary" type="button" @click="addPolymorphic" :disabled="newItemType===null">
            <span class=" text-uppercase fw-bold me-1">Add</span>
            <IconFasPlus/>
          </button>
          <select class="form-select ms-3 w-auto flex-fill shadow-sm"
                  v-model.number="newItemType"
          >
            <option disabled :value="null">Choose element to add</option>
            <option
                v-for="(sub, i) in schema.items.anyOf"
                :key="i"
                :value="i"
            >{{ sub.title || `Tipo ${i}` }}</option>
          </select>
        </template>
      </template>
    </div>

    <div class="mx-3">
      <!-- enum -->
      <select class="form-select shadow-sm"
              v-if="schema.enum"
              v-model="localValue"
              :required="required"
              :disabled="translationMode"
      >
        <option
            v-for="opt in schema.enum"
            :key="opt"
            :value="opt"
        >{{ opt }}</option>
      </select>

      <!-- string -->
      <textarea class="form-control shadow-sm"
                v-else-if="schema.type==='string'"
                v-model="localValue"
                :required="required"
                :disabled="translationMode && !schema.trans_editable"
      ></textarea>

      <!-- number / integer -->
      <input class="form-control shadow-sm"
             v-else-if="schema.type==='number' || schema.type==='integer'"
             type="number"
             v-model.number="localValue"
             :required="required"
             :disabled="translationMode"
      />

      <!-- boolean -->
      <input class="form-check-input"
             v-else-if="schema.type==='boolean'"
             type="checkbox"
             v-model="localValue"
             :disabled="translationMode"
      />

      <!-- array -->
      <div v-else-if="schema.type==='array'" class="field-renderer-array-list ">

        <div v-if="schema.items && (schema.items.anyOf || schema.items.type==='object')">
          <div  class="list-group">
            <div v-for="(item, idx) in localValue" :key="idx" class="array-item list-group-item position-relative py-3 shadow-sm">
              <button v-if="!translationMode" class="btn btn-sm btn-danger position-absolute top-0 end-0 m-3" type="button" @click="remove(idx)">
                <IconFasTrash/>
              </button>
              <!-- oggetto monotipo -->
              <FieldRenderer
                  v-if="schema.items.type==='object'"
                  v-model="localValue[idx]"
                  :schema="schema.items"
                  :translation-mode="translationMode"
                  :required="false"
                  :level="level+1"
                  class="flex-fill"
              />
              <!-- oggetto polimorfo -->
              <FieldRenderer
                  v-else
                  v-model="localValue[idx]"
                  :schema="getSchema(item)"
                  :translation-mode="translationMode"
                  :required="false"
                  :level="level+1"
                  :parent="'polymorph'"
              />
            </div>
          </div>
          <template v-if="!translationMode">
            <template v-if="schema.items.type==='object'">
              <button v-if="!translationMode"
                      class="btn btn-sm btn-primary align-self-start mt-2"
                      type="button"
                      @click="addMono"
                      :disabled="translationMode"
              >
                <span class=" text-uppercase fw-bold me-1">Add</span>
                <IconFasPlus/>
              </button>
            </template>

            <div v-else-if="localValue && localValue.length>0" class="d-flex my-2 align-items-center">
              <button class="btn btn-sm btn-primary" type="button" @click="addPolymorphic" :disabled="newItemType===null">
                <span class=" text-uppercase fw-bold me-1">Add</span>
                <IconFasPlus/>
              </button>

              <select class="form-select ms-3 w-auto flex-fill shadow-sm"
                      v-model.number="newItemType"
              >
                <option disabled :value="null">Choose element to add</option>
                <option
                    v-for="(sub, i) in schema.items.anyOf"
                    :key="i"
                    :value="i"
                >{{ sub.title || `Tipo ${i}` }}</option>
              </select>

            </div>

          </template>
        </div>
        <!-- monotipo -->
        <div v-else>
            <div v-for="(item, idx) in localValue" :key="idx" class="array-item d-flex align-items-center my-2">
              <div class="flex-fill">
                <input class="form-control shadow-sm"
                       v-if="schema.items.type==='string'"
                       type="text"
                       v-model="localValue[idx]"
                       :disabled="translationMode"
                />
                <input class="form-control shadow-sm"
                       v-else-if="schema.items.type==='number' || schema.items.type==='integer'"
                       type="number"
                       v-model.number="localValue[idx]"
                       :disabled="translationMode"
                />
                <input class="form-control shadow-sm"
                       v-else-if="schema.items.type==='boolean'"
                       type="checkbox"
                       v-model="localValue[idx]"
                       :disabled="translationMode"
                />
              </div>
              <button v-if="!translationMode" class="btn btn-sm btn-danger ms-3" type="button" @click="remove(idx)">
                <IconFasTrash/>
              </button>
            </div>

            <button v-if="!translationMode"
                    class="btn btn-sm btn-primary align-self-center"
                    type="button"
                    @click="addMono"
                    :disabled="translationMode"
            >
              <span class=" text-uppercase fw-bold me-1">Add</span>
              <IconFasPlus/>
            </button>

        </div>
      </div>

      <!-- object -->
      <div v-else-if="schema.type==='object'">
        <div v-for="(subSchema, key) in schema.properties" :key="key">
          <FieldRenderer
              v-model="localValue[key]"
              :schema="subSchema"
              :translation-mode="translationMode"
              :required="schema.required?.includes(key)"
              :level="level+1"
          />
        </div>
      </div>

      <!-- fallback -->
      <span v-else>
        Tipo non supportato: {{ schema }}
      </span>
    </div>



  </div>
</template>

<script setup>
import {computed, ref, getCurrentInstance, inject} from 'vue'
import FieldRenderer from './FieldRenderer.vue'
import {convertToTitleCase} from "@/utils.js";


const props = defineProps({
  modelValue:      { required: false },
  schema:          { type: Object, required: true },
  fieldName:        { required: false, default: null },
  translationMode: { type: Boolean, default: false },
  required:        { type: Boolean, default: false },
  level:           { type: Number,  default: 0 },
  parent:          { type: String,  default: "" },

})

const emit = defineEmits(['update:modelValue'])
const notifyInputValueChange = inject('notifyInputValueChange')
const notifyOutputValueChange = inject('notifyOutputValueChange')


// two‐way binding con default
const localValue = computed({
  get() {
    if (props.modelValue == null) {
      const init = defaultOfSchema(props.schema)
      emit('update:modelValue', init)
      return init
    }
    return props.modelValue
  },
  set(val) {
    emit('update:modelValue', val)
    if(props.schema.trans_editable)
      notifyOutputValueChange()
    else
      notifyInputValueChange()
  }
})

const newItemType = ref(null)

// defaultOfSchema senza $ref
function defaultOfSchema(schema) {
  if (schema.anyOf) {
    return defaultOfSchema(schema.anyOf[0])
  }
  switch (schema.type) {
    case 'string':  return (props.required ? null : "")
    case 'number':  return (props.required ? null : 0)
    case 'integer': return (props.required ? null : 0)
    case 'boolean': return (props.required ? null : false)
    case 'array':   return (props.required ? null : [])
    case 'object': {
      const obj = {}
      for (const [key, subs] of Object.entries(schema.properties || {})) {
        obj[key] = defaultOfSchema(subs)
      }
      return obj
    }
    default:
      return null
  }
}

// array monotipo
function addMono() {
  const items = Array.isArray(localValue.value) ? [...localValue.value] : []
  const itemSchema = props.schema.items
  let newItem
  switch (itemSchema.type) {
    case 'string':  newItem = ''; break
    case 'number':
    case 'integer': newItem = 0; break
    case 'boolean': newItem = false; break
    case 'object':  newItem = defaultOfSchema(itemSchema); break
    case 'array':   newItem = []; break
    default:
      console.warn('Tipo di elemento non supportato:', itemSchema.type)
      newItem = null
  }
  items.push(newItem)
  localValue.value = items
}

// array polimorfo
function addPolymorphic() {
  if (newItemType.value == null) return
  const chosen = props.schema.items.anyOf[newItemType.value]
  const obj = defaultOfSchema(chosen)
  // tag per discriminazione
  if (obj && typeof obj === 'object') {
    obj.__schemaIndex = newItemType.value
  }
  const arr = Array.isArray(localValue.value) ? [...localValue.value] : []
  arr.push(obj)
  localValue.value = arr
  newItemType.value = null
}

// discriminante per anyOf
function getSchema(item) {
  if (item && typeof item === 'object' && item.__schemaIndex != null) {
    return props.schema.items.anyOf[item.__schemaIndex]
  }
  return props.schema.items.anyOf[0]
}

// rimozione
function remove(idx) {
  const arr = [...localValue.value]
  arr.splice(idx, 1)
  localValue.value = arr
}

</script>

<style scoped>
.field-renderer-label {
  font-weight: bold;
  color: var(--bs-tertiary-color);
}


</style>
