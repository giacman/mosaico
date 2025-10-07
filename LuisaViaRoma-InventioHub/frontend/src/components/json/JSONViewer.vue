<template>
	<div class="container-fluid p-0">
	<ViewRenderer :node="data" :path="[]" :output-fields="getTransEditableFields(props.schema)"
	 @update-node="updateData" />
	</div>
</template>

<script setup>
import ViewRenderer from './ViewRenderer.vue'

const props = defineProps({
	data: { type: [Object, Array], required: true },
	schema: { type: Object, required: false }
})

function updateData({ path, value }) {
	let target = props.data
	for (let i = 0; i < path.length - 1; i++) {
		target = target[path[i]]
	}
	const key = path[path.length - 1]
	target[key] = castValue(value)
}

// Optional: try to preserve types
function castValue(value) {
	if (!isNaN(value) && value.trim() !== '') return Number(value)
	if (value === 'true') return true
	if (value === 'false') return false
	return value
}



function getTransEditableFields(schema, complete_mode = false) {
  const result = [];

  function traverse(obj, path = '') {
    if (obj && typeof obj === 'object') {
      // Se il nodo ha trans_editable=true, aggiungiamo il path
      if (obj.trans_editable === true) {
        const cleaned = path.startsWith('.') ? path.slice(1) : path;
        result.push(cleaned);
      }

      // Scorri definizioni custom ($defs)
      if (obj.$defs && typeof obj.$defs === 'object') {
        for (const [defName, defSchema] of Object.entries(obj.$defs)) {
          const nextPath = path ? `${path}.$defs.${defName}` : `$defs.${defName}`;
          traverse(defSchema, nextPath);
        }
      }

      // Scorri le proprietà (properties)
      if (obj.properties && typeof obj.properties === 'object') {
        for (const [propName, propSchema] of Object.entries(obj.properties)) {
          const nextPath = path ? `${path}.properties.${propName}` : `properties.${propName}`;
          traverse(propSchema, nextPath);
        }
      }

      // Scorri eventuali items (per array)
      if (obj.items) {
        const nextPath = path ? `${path}.items` : 'items';
        traverse(obj.items, nextPath);
      }

      // Scorri altre chiavi ad oggetto
      for (const [key, val] of Object.entries(obj)) {
        if (['$defs', 'properties', 'items'].includes(key)) continue;
        if (val && typeof val === 'object') {
          const nextPath = path ? `${path}.${key}` : key;
          traverse(val, nextPath);
        }
      }
    } else if (Array.isArray(obj)) {
      // Se è un array, scorriamo gli elementi
      obj.forEach((item, idx) => {
        traverse(item, `${path}[${idx}]`);
      });
    }
  }

  traverse(schema, '');

  if(!complete_mode) {
    for(let i =0; i<result.length; i++) {
      result[i] = result[i].split(".").slice(-1)[0];
    }
  }

  return new Set(result.map(s => s.toLowerCase()));
}

</script>

