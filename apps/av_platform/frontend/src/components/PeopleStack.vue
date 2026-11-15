<script setup lang="ts">
// Overlapping initials of the people on a record (UI-03). Names stay readable in the title.
import { computed } from 'vue'
import type { Person } from '../pmApi'

const props = withDefaults(defineProps<{ people: Person[]; max?: number }>(), { max: 4 })

function initials(person: Person) {
  const words = (person.full_name || person.name).split(/[\s@.]+/).filter(Boolean)
  return words.slice(0, 2).map((w) => w[0]?.toUpperCase()).join('')
}

const shown = computed(() => props.people.slice(0, props.max))
const rest = computed(() => props.people.length - shown.value.length)
const names = computed(() => props.people.map((p) => p.full_name || p.name).join(', '))
</script>

<template>
  <span v-if="people.length" class="inline-flex items-center" :title="names">
    <span
      v-for="(person, index) in shown"
      :key="person.name"
      class="inline-grid size-6 place-items-center rounded-full border-2 border-surface-white bg-surface-blue-2 text-[10px] font-semibold text-ink-blue-6"
      :class="index ? '-ml-1.5' : ''"
      aria-hidden="true"
    >
      {{ initials(person) }}
    </span>
    <span v-if="rest > 0" class="-ml-1.5 inline-grid size-6 place-items-center rounded-full border-2 border-surface-white bg-surface-gray-3 text-[10px] text-ink-gray-7" aria-hidden="true">
      +{{ rest }}
    </span>
    <span class="sr-only">{{ names }}</span>
  </span>
</template>
