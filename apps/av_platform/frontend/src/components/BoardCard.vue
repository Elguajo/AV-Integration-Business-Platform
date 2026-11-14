<script setup lang="ts">
import { computed, nextTick, ref, useTemplateRef } from 'vue'
import { Button, Dropdown, toast, useCall } from 'frappe-ui'
import type { DropdownOptions } from 'frappe-ui'
import { PM_API, deskTaskUrl, type BoardStage, type BoardTask, type Person, type Subtasks } from '../pmApi'
import { ruPm } from '../i18n/pm'
import { date } from '../format'

const props = defineProps<{
  task: BoardTask
  stages: BoardStage[]
  projectName: string | null
  canMove: boolean
  saving: boolean
  currentUser: string
  members: Person[]
  canAssignOthers: boolean
}>()
const emit = defineEmits<{
  move: [stage: string]
  rename: [subject: string]
  assign: [user: string]
  unassign: [user: string]
}>()

const t = ruPm.card
const busy = computed(() => props.saving)
const place = computed(() => [props.task.room, props.task.system].filter(Boolean).join(' · '))
const assigneeNames = computed(() => props.task.assignees.map((a) => a.full_name || a.name).join(', '))
const isMine = computed(() => props.task.assignees.some((a) => a.name === props.currentUser))
const isMember = computed(() => props.members.some((m) => m.name === props.currentUser))

// Stages are ordered by the server (AV Work Stage.sequence). Completing means moving to the first
// closed stage; the server still refuses blocked works and open dependencies.
const stageIndex = computed(() => props.stages.findIndex((s) => s.name === props.task.stage))
const currentStage = computed(() => props.stages[stageIndex.value] ?? null)
const isClosed = computed(() => !!currentStage.value?.is_closed)
const closedStage = computed(() => props.stages.find((s) => s.is_closed) ?? null)
const nextStage = computed(() => (isClosed.value ? null : props.stages[stageIndex.value + 1] ?? null))

// Inline rename.
const editing = ref(false)
const draft = ref('')
const input = useTemplateRef<HTMLInputElement>('input')

async function startRename() {
  draft.value = props.task.subject
  editing.value = true
  await nextTick()
  input.value?.focus()
  input.value?.select()
}

function finishRename(save: boolean) {
  if (!editing.value) return
  editing.value = false
  const subject = draft.value.trim()
  if (save && subject && subject !== props.task.subject) emit('rename', subject)
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(new URL(deskTaskUrl(props.task.name), location.origin).href)
    toast.success(t.linkCopied, { description: props.task.name })
  } catch {
    toast.error(t.linkNotCopied)
  }
}

const menu = computed<DropdownOptions>(() => {
  const stageItems = props.stages
    .filter((s) => s.name !== props.task.stage)
    .map((s) => ({ label: s.label, onClick: () => emit('move', s.name) }))
  const others = props.members.filter((m) => !props.task.assignees.some((a) => a.name === m.name))
  const work: DropdownOptions = []
  if (props.canMove) {
    if (nextStage.value) {
      const target = nextStage.value
      work.push({ label: `${t.nextStage}: ${target.label}`, icon: 'lucide-arrow-right', onClick: () => emit('move', target.name) })
    }
    if (stageItems.length) work.push({ label: ruPm.card.moveTo, icon: 'lucide-arrow-right-left', submenu: stageItems })
    if (!isClosed.value) work.push({ label: t.rename, icon: 'lucide-pencil', onClick: startRename })
  }
  const people: DropdownOptions = []
  if (props.canMove && !isClosed.value) {
    if (isMine.value) {
      people.push({ label: t.leave, icon: 'lucide-user-minus', onClick: () => emit('unassign', props.currentUser) })
    } else if (isMember.value) {
      people.push({ label: t.take, icon: 'lucide-user-check', onClick: () => emit('assign', props.currentUser) })
    }
    if (props.canAssignOthers) {
      people.push({
        label: t.assign,
        icon: 'lucide-user-plus',
        submenu: others.length
          ? others.map((m) => ({ label: m.full_name || m.name, onClick: () => emit('assign', m.name) }))
          : [{ label: t.noMembers, disabled: true }],
      })
      const removable = props.task.assignees.filter((a) => a.name !== props.currentUser)
      if (removable.length) {
        people.push({
          label: t.unassign,
          icon: 'lucide-user-x',
          submenu: removable.map((a) => ({ label: a.full_name || a.name, onClick: () => emit('unassign', a.name) })),
        })
      }
    }
  }
  return [
    ...(work.length ? [{ group: 'work', hideLabel: true, options: work }] : []),
    ...(people.length ? [{ group: 'people', hideLabel: true, options: people }] : []),
    { group: 'link', hideLabel: true, options: [{ label: t.copyLink, icon: 'lucide-link', onClick: copyLink }] },
  ] as DropdownOptions
})

// Subtasks are read on demand; the server returns only the ones this user may read.
const showSubtasks = ref(false)
const subtasks = useCall<Subtasks, { task: string }>({
  url: PM_API.subtasks,
  params: () => ({ task: props.task.name }),
  immediate: false,
})

function toggleSubtasks() {
  showSubtasks.value = !showSubtasks.value
  if (showSubtasks.value) subtasks.reload()
}

const closedStages = computed(() => new Set(props.stages.filter((s) => s.is_closed).map((s) => s.name)))
const progress = computed(() => {
  const s = props.task.subtasks
  return s ? Math.round((s.done / s.total) * 100) : 0
})

function onDragStart(event: DragEvent) {
  if (!event.dataTransfer || editing.value) return
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', props.task.name)
}
</script>

<template>
  <article
    class="group relative rounded-6 border bg-surface-elevation-1 p-3 transition-colors"
    :class="[
      task.block_reason ? 'border-outline-amber-2' : 'border-outline-gray-1',
      busy ? 'opacity-60' : 'hover:border-outline-gray-3',
      canMove && !busy && !editing ? 'cursor-grab' : '',
    ]"
    :draggable="canMove && !busy && !editing"
    :aria-busy="busy"
    @dragstart="onDragStart"
  >
    <div class="flex items-start gap-2">
      <span
        v-if="isClosed"
        class="lucide-circle-check mt-0.5 size-4 shrink-0 text-ink-green-3"
        role="img"
        :aria-label="t.completed"
        :title="t.completed"
      />
      <button
        v-else-if="canMove && closedStage"
        type="button"
        class="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full text-ink-gray-4 hover:text-ink-green-3 focus-visible:outline focus-visible:outline-2 focus-visible:outline-outline-gray-4 disabled:opacity-50"
        :disabled="busy"
        :title="`${t.complete}: ${closedStage.label}`"
        :aria-label="`${t.complete}: ${task.subject}`"
        @click="emit('move', closedStage.name)"
      >
        <span class="lucide-circle size-4" aria-hidden="true" />
      </button>

      <div class="min-w-0 flex-1">
        <input
          v-if="editing"
          ref="input"
          v-model="draft"
          maxlength="140"
          class="w-full rounded-4 border border-outline-gray-3 bg-surface-white px-1.5 py-0.5 text-base-medium text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-outline-gray-3"
          :aria-label="t.renameField"
          :title="t.renameHint"
          @keydown.enter.prevent="finishRename(true)"
          @keydown.esc.prevent="finishRename(false)"
          @blur="finishRename(true)"
        />
        <a
          v-else
          :href="deskTaskUrl(task.name)"
          target="_blank"
          rel="noopener"
          class="block hyphens-auto break-words text-base-medium hover:underline"
          lang="ru"
          :class="isClosed ? 'text-ink-gray-5' : 'text-ink-gray-9'"
          :title="ruPm.card.open"
        >
          <span v-if="task.is_milestone" class="lucide-flag mr-1 inline-block size-3.5 align-[-2px] text-ink-gray-5" :aria-label="ruPm.card.milestone" />
          {{ task.subject }}
        </a>
      </div>

      <div class="-mr-1 -mt-0.5 flex shrink-0 items-center">
        <!-- Hover shortcuts overlay the title instead of taking its width. Touch screens have no
             hover: there the same actions stay in the "⋯" menu and the title keeps the full width. -->
        <div
          v-if="canMove && !editing"
          class="absolute right-9 top-2 flex items-center rounded-4 bg-surface-elevation-1 opacity-0 shadow-sm transition-opacity focus-within:opacity-100 group-hover:opacity-100 [@media(hover:none)]:hidden"
        >
          <Button
            v-if="nextStage"
            variant="ghost"
            size="sm"
            icon="lucide-arrow-right"
            :tooltip="`${t.nextStage}: ${nextStage.label}`"
            :aria-label="`${t.nextStage}: ${nextStage.label}`"
            :disabled="busy"
            @click="emit('move', nextStage.name)"
          />
          <Button
            v-if="!isClosed"
            variant="ghost"
            size="sm"
            icon="lucide-pencil"
            :tooltip="t.rename"
            :aria-label="`${t.rename}: ${task.subject}`"
            :disabled="busy"
            @click="startRename"
          />
        </div>
        <Dropdown
          :options="menu"
          align="end"
          :button="{ icon: 'lucide-ellipsis', variant: 'ghost', size: 'sm', tooltip: t.actions, disabled: busy }"
          :aria-label="`${t.actions}: ${task.subject}`"
        />
      </div>
    </div>

    <div class="mt-1.5 flex flex-wrap items-center gap-x-2.5 gap-y-1 text-sm text-ink-gray-5">
      <button
        type="button"
        class="rounded-4 font-mono text-p-xs tabular-nums hover:text-ink-gray-8 focus-visible:outline focus-visible:outline-2 focus-visible:outline-outline-gray-4"
        :title="t.copyLink"
        @click="copyLink"
      >
        {{ task.name }}
      </button>
      <span v-if="task.comments" class="flex items-center gap-1" :title="t.comments">
        <span class="lucide-message-square size-3.5" aria-hidden="true" />
        <span class="tabular-nums"><span class="sr-only">{{ t.comments }}: </span>{{ task.comments }}</span>
      </span>
      <button
        v-if="task.subtasks"
        type="button"
        class="flex items-center gap-1 rounded-4 hover:text-ink-gray-8 focus-visible:outline focus-visible:outline-2 focus-visible:outline-outline-gray-4"
        :aria-expanded="showSubtasks"
        :title="showSubtasks ? t.hideSubtasks : t.showSubtasks"
        @click="toggleSubtasks"
      >
        <span class="lucide-list-tree size-3.5" aria-hidden="true" />
        <span class="tabular-nums"><span class="sr-only">{{ t.subtasks }}: </span>{{ task.subtasks.done }}/{{ task.subtasks.total }}</span>
        <span :class="showSubtasks ? 'lucide-chevron-up' : 'lucide-chevron-down'" class="size-3.5" aria-hidden="true" />
      </button>
    </div>

    <div v-if="projectName" class="mt-1 truncate text-sm text-ink-gray-5">{{ projectName }}</div>
    <div v-if="place" class="mt-1.5 flex items-center gap-1.5 text-sm text-ink-gray-6">
      <span class="lucide-map-pin size-3.5 shrink-0" aria-hidden="true" />
      <span class="truncate">{{ place }}</span>
    </div>

    <div class="mt-2 flex items-center justify-between gap-2 text-sm">
      <span class="flex min-w-0 items-center gap-1.5 text-ink-gray-6">
        <span class="lucide-user size-3.5 shrink-0" aria-hidden="true" />
        <span class="truncate">{{ assigneeNames || ruPm.card.noAssignee }}</span>
      </span>
      <span
        class="shrink-0 rounded-4 tabular-nums"
        :class="{
          'font-medium text-ink-red-4': task.due_state === 'overdue',
          'bg-surface-amber-2 px-1.5 font-medium text-ink-amber-7': task.due_state === 'today',
          'text-ink-amber-7': task.due_state === 'soon',
          'text-ink-gray-5': !task.due_state,
        }"
        :title="task.due_state ? t.due[task.due_state] : undefined"
      >
        <span v-if="task.due_state" class="sr-only">{{ t.due[task.due_state] }}: </span>{{ task.end ? date(task.end) : ruPm.card.noDate }}
      </span>
    </div>

    <div v-if="task.subtasks" class="mt-2 h-1 overflow-hidden rounded-full bg-surface-gray-2" aria-hidden="true">
      <div
        class="h-full rounded-full"
        :class="task.subtasks.done === task.subtasks.total ? 'bg-surface-green-3' : 'bg-surface-gray-5'"
        :style="{ width: `${progress}%` }"
      />
    </div>

    <ul v-if="showSubtasks" class="mt-2 space-y-1 border-t border-outline-gray-1 pt-2" :aria-label="t.subtasks">
      <li v-if="subtasks.loading && !subtasks.data" class="text-p-xs text-ink-gray-5">{{ t.loading }}</li>
      <li v-else-if="subtasks.error" class="text-p-xs text-ink-red-4">{{ t.subtasksError }}</li>
      <li v-else-if="subtasks.data && !subtasks.data.tasks.length" class="text-p-xs text-ink-gray-5">{{ t.noVisibleSubtasks }}</li>
      <li
        v-for="sub in subtasks.data?.tasks ?? []"
        :key="sub.name"
        class="flex items-start gap-1.5 rounded-4 bg-surface-gray-1 px-2 py-1 text-sm"
      >
        <span
          :class="sub.stage && closedStages.has(sub.stage) ? 'lucide-circle-check text-ink-green-3' : 'lucide-circle text-ink-gray-4'"
          class="mt-0.5 size-3.5 shrink-0"
          :aria-label="sub.stage && closedStages.has(sub.stage) ? t.completed : undefined"
        />
        <a
          :href="deskTaskUrl(sub.name)"
          target="_blank"
          rel="noopener"
          class="min-w-0 flex-1 break-words hover:underline"
          :class="sub.stage && closedStages.has(sub.stage) ? 'text-ink-gray-5' : 'text-ink-gray-8'"
        >{{ sub.subject }}</a>
        <span
          v-if="sub.end"
          class="shrink-0 text-p-xs tabular-nums"
          :class="sub.due_state === 'overdue' ? 'text-ink-red-4' : 'text-ink-gray-5'"
        >{{ date(sub.end) }}</span>
      </li>
    </ul>

    <div
      v-if="task.block_reason"
      class="mt-2 rounded-4 bg-surface-amber-2 px-2 py-1 text-p-xs text-ink-amber-7"
    >
      <span class="font-medium">{{ ruPm.card.blocked }}:</span> {{ task.block_reason }}
    </div>
    <div v-if="busy" class="mt-2 text-p-xs text-ink-gray-5">{{ ruPm.card.saving }}</div>
  </article>
</template>
