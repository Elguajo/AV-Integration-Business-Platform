<script setup lang="ts">
// Five direction marks of a project row (UI-03, OVW-01/02). Only works are tracked today; the other
// directions are grey with the text «ещё не ведётся» — unknown is never shown as zero or as green.
import { computed } from 'vue'
import type { ProjectStatus } from '../overviewApi'
import { ruOverview as t } from '../i18n/overview'

const props = defineProps<{ works: ProjectStatus }>()

const COLOR: Record<ProjectStatus, string> = {
  problem: 'bg-surface-red-5',
  risk: 'bg-surface-amber-5',
  unknown: 'bg-surface-gray-4',
  on_plan: 'bg-surface-green-3',
}

const marks = computed(() => [
  { label: t.directions.works, value: t.status[props.works], color: COLOR[props.works] },
  ...(['procurement', 'install', 'tests', 'money'] as const).map((key) => ({
    label: t.directions[key],
    value: t.directions.notTracked,
    color: 'bg-surface-gray-3',
  })),
])
</script>

<template>
  <span class="inline-flex gap-[3px]" role="img" :aria-label="marks.map((m) => `${m.label}: ${m.value}`).join('; ')">
    <i
      v-for="mark in marks"
      :key="mark.label"
      class="block size-2.5 rounded-[3px]"
      :class="mark.color"
      :title="`${mark.label}: ${mark.value}`"
    />
  </span>
</template>
