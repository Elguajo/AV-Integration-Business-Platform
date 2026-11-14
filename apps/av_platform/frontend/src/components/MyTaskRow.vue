<script setup lang="ts">
import { computed } from 'vue'
import { Button, Dropdown } from 'frappe-ui'
import type { BoardStage, MyTask } from '../pmApi'
import { ruPm } from '../i18n/pm'
import { date } from '../format'

const props = defineProps<{
  task: MyTask
  stages: BoardStage[]
  projectName: string | null
  canMove: boolean
  saving: boolean
  showAssignees: boolean
}>()
const emit = defineEmits<{ move: [stage: string] }>()

const place = computed(() => [props.task.room, props.task.system].filter(Boolean).join(' · '))
const assignees = computed(() =>
  props.task.assignees.map((a) => a.full_name || a.name).join(', '),
)
const currentIndex = computed(() => props.stages.findIndex((s) => s.name === props.task.stage))
const stageLabel = computed(() => props.stages[currentIndex.value]?.label ?? ruPm.column.noStage)
// Stages are ordered by the server (AV Work Stage.sequence); a work without a stage starts at the first.
const nextStage = computed(() => props.stages[currentIndex.value + 1] ?? null)
const otherStages = computed(() =>
  props.stages
    .filter((s) => s.name !== props.task.stage && s.name !== nextStage.value?.name)
    .map((s) => ({ label: s.label, onClick: () => emit('move', s.name) })),
)
</script>

<template>
  <li
    class="flex flex-wrap items-start gap-x-4 gap-y-2 border-b border-outline-gray-1 px-3 py-2.5 last:border-b-0"
    :class="saving ? 'opacity-60' : 'hover:bg-surface-gray-1'"
    :aria-busy="saving"
  >
    <div class="min-w-0 flex-1 basis-64">
      <a
        :href="`/app/task/${encodeURIComponent(task.name)}`"
        target="_blank"
        rel="noopener"
        class="text-base-medium text-ink-gray-9 hover:underline"
        :title="ruPm.card.open"
      >
        <span v-if="task.is_milestone" class="lucide-flag mr-1 inline-block size-3.5 align-[-2px] text-ink-gray-5" :aria-label="ruPm.card.milestone" />
        {{ task.subject }}
      </a>
      <div class="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-sm text-ink-gray-5">
        <span v-if="projectName" class="truncate">{{ projectName }}</span>
        <span v-if="place" class="flex items-center gap-1">
          <span class="lucide-map-pin size-3.5 shrink-0" aria-hidden="true" />{{ place }}
        </span>
        <span v-if="showAssignees" class="flex items-center gap-1">
          <span class="lucide-user size-3.5 shrink-0" aria-hidden="true" />
          <span class="sr-only">{{ ruPm.my.assignedTo }}:</span>{{ assignees || ruPm.card.noAssignee }}
        </span>
      </div>
      <div
        v-if="task.block_reason"
        class="mt-1.5 inline-block rounded-4 bg-surface-amber-2 px-2 py-0.5 text-p-xs text-ink-amber-7"
      >
        <span class="font-medium">{{ ruPm.card.blocked }}:</span> {{ task.block_reason }}
      </div>
    </div>

    <div class="flex max-w-full flex-wrap items-center gap-2 text-sm">
      <span class="rounded-full bg-surface-gray-2 px-2 py-0.5 text-ink-gray-7">{{ stageLabel }}</span>
      <span
        class="whitespace-nowrap tabular-nums"
        :class="task.is_overdue ? 'font-medium text-ink-red-4' : 'text-ink-gray-5'"
        :title="task.is_overdue ? ruPm.card.overdue : undefined"
      >
        {{ task.end ? date(task.end) : ruPm.card.noDate }}
      </span>
      <template v-if="canMove">
        <Button
          v-if="nextStage"
          size="sm"
          icon-right="lucide-arrow-right"
          :label="nextStage.label"
          :tooltip="`${ruPm.my.nextStageTo} «${nextStage.label}»`"
          :aria-label="`${ruPm.my.nextStageTo} «${nextStage.label}»: ${task.subject}`"
          :disabled="saving"
          @click="emit('move', nextStage.name)"
        />
        <Dropdown
          v-if="otherStages.length"
          :options="otherStages"
          align="end"
          :button="{
            icon: 'lucide-ellipsis',
            variant: 'ghost',
            size: 'sm',
            tooltip: ruPm.my.otherStage,
            disabled: saving,
          }"
          :aria-label="`${ruPm.my.otherStage}: ${task.subject}`"
        />
      </template>
    </div>
  </li>
</template>
