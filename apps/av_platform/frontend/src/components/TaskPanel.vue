<script setup lang="ts">
// Side panel of one work (BRD-2), opened over the board and "My tasks" by `?task=<name>`.
// The host page must be `position: relative`, read `?task` from the address and close the panel
// by removing it; the panel covers the host's right edge (full width on a phone). Every change
// goes through the same server calls as the card; the panel only renders the server's answer and
// hands the fresh card to the host (`updated`).
import { computed, nextTick, onBeforeUnmount, onMounted, ref, useTemplateRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Button, Dropdown, ErrorMessage, Skeleton, toast, useCall } from 'frappe-ui'
import type { DropdownOptions } from 'frappe-ui'
import {
  PM_API,
  TASK_QUERY,
  deskTaskUrl,
  stageSteps,
  taskShellUrl,
  type BoardTask,
  type MoveResult,
  type TaskDetail,
} from '../pmApi'
import { ruPm } from '../i18n/pm'
import { boot } from '../boot'
import { UNKNOWN, date } from '../format'
import OverlayScroll from './OverlayScroll.vue'

const props = defineProps<{
  name: string
  /** Version of the host's copy of this work: a change made on the card reloads the panel. */
  cardModified?: string | null
}>()
const emit = defineEmits<{ close: []; updated: [task: BoardTask] }>()

const t = ruPm.panel
const c = ruPm.card

// A subtask opens in the same panel on the same screen.
const route = useRoute()
function panelLink(name: string) {
  return { query: { ...route.query, [TASK_QUERY]: name } }
}

// The panel is keyed by the work's name, so params are fixed for its lifetime.
const detail = useCall<TaskDetail, { task: string }>({
  url: PM_API.taskDetail,
  params: { task: props.name },
})
const move = useCall<MoveResult, { task: string; stage: string; expected_modified: string }>({
  url: PM_API.move, method: 'POST', immediate: false,
})
const rename = useCall<MoveResult, { task: string; subject: string; expected_modified: string }>({
  url: PM_API.rename, method: 'POST', immediate: false,
})
const assign = useCall<MoveResult, { task: string; user: string }>({
  url: PM_API.assign, method: 'POST', immediate: false,
})
const unassign = useCall<MoveResult, { task: string; user: string }>({
  url: PM_API.unassign, method: 'POST', immediate: false,
})

const d = computed(() => detail.data)
const task = computed(() => d.value?.task ?? null)
const busy = ref(false)
const forbidden = computed(() => (detail.error as { type?: string } | null)?.type === 'PermissionError')

watch(() => props.cardModified, (value, old) => {
  if (value && old && value !== task.value?.modified && !busy.value) detail.reload()
})

const steps = computed(() => stageSteps(d.value?.stages ?? [], task.value?.stage ?? null))
const stageLabel = computed(() => steps.value.current?.label ?? ruPm.column.noStage)
const canChange = computed(() => !!d.value?.can_move && !steps.value.isClosed)
const place = computed(() => [task.value?.room, task.value?.system].filter(Boolean).join(' · '))
const isMine = computed(() => !!task.value?.assignees.some((a) => a.name === d.value?.user.name))
const isMember = computed(() => !!d.value?.members.some((m) => m.name === d.value?.user.name))
const closedStages = computed(() => new Set((d.value?.stages ?? []).filter((s) => s.is_closed).map((s) => s.name)))
const projectHref = computed(() =>
  d.value?.project_readable && task.value?.project && boot.views.includes('projects')
    ? `/projects/${encodeURIComponent(task.value.project)}`
    : null,
)
const projectLabel = computed(() => d.value?.project_name || task.value?.project || UNKNOWN)

const stageMenu = computed<DropdownOptions>(() =>
  (d.value?.stages ?? [])
    .filter((s) => s.name !== task.value?.stage)
    .map((s) => ({ label: s.label, onClick: () => moveTo(s.name) })),
)

const assignMenu = computed<DropdownOptions>(() => {
  if (!d.value || !task.value || !canChange.value || !d.value.can_assign_others) return []
  const current = task.value.assignees
  const others = d.value.members.filter((m) => !current.some((a) => a.name === m.name))
  const removable = current.filter((a) => a.name !== d.value?.user.name)
  return [
    {
      label: c.assign,
      icon: 'lucide-user-plus',
      submenu: others.length
        ? others.map((m) => ({ label: m.full_name || m.name, onClick: () => runAction(() => assignTo(m.name)) }))
        : [{ label: c.noMembers, disabled: true }],
    },
    ...(removable.length
      ? [{
          label: c.unassign,
          icon: 'lucide-user-x',
          submenu: removable.map((a) => ({
            label: a.full_name || a.name,
            onClick: () => runAction(() => unassignFrom(a.name)),
          })),
        }]
      : []),
  ] as DropdownOptions
})

function errorMessage(error: unknown) {
  return (error as { messages?: string[] }).messages?.[0] ?? (error as Error).message
}

// One flow for every action: wait for the server, show its answer, hand the fresh card over.
async function runAction(call: () => Promise<MoveResult | null | undefined>, success = ruPm.saved) {
  if (busy.value || !task.value) return
  busy.value = true
  try {
    const result = await call()
    if (!result) return
    if (result.task) emit('updated', result.task)
    if (result.ok) toast.success(success, { description: result.task.subject })
    else toast.error(ruPm.notSaved, { description: ruPm.reject[result.code] })
    await detail.reload()
  } catch (error) {
    toast.error(ruPm.notSaved, { description: errorMessage(error) })
  } finally {
    busy.value = false
  }
}

function moveTo(stage: string) {
  const current = task.value
  if (!current || current.stage === stage) return
  runAction(async () => {
    await move.submit({ task: current.name, stage, expected_modified: current.modified })
    return move.data
  }, ruPm.moved)
}

async function assignTo(user: string) {
  await assign.submit({ task: props.name, user })
  return assign.data
}

async function unassignFrom(user: string) {
  await unassign.submit({ task: props.name, user })
  return unassign.data
}

// Inline rename, as on the card.
const editing = ref(false)
const draft = ref('')
const input = useTemplateRef<HTMLInputElement>('input')

async function startRename() {
  if (!task.value) return
  draft.value = task.value.subject
  editing.value = true
  await nextTick()
  input.value?.focus()
  input.value?.select()
}

function finishRename(save: boolean) {
  if (!editing.value || !task.value) return
  editing.value = false
  const current = task.value
  const subject = draft.value.trim()
  if (save && subject && subject !== current.subject) {
    runAction(async () => {
      await rename.submit({ task: current.name, subject, expected_modified: current.modified })
      return rename.data
    })
  }
  nextTick(() => heading.value?.focus())
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(taskShellUrl(props.name))
    toast.success(c.linkCopied, { description: props.name })
  } catch {
    toast.error(c.linkNotCopied)
  }
}

const created = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
})
function dateTime(value: string) {
  const parsed = new Date(value.replace(' ', 'T'))
  return Number.isNaN(parsed.getTime()) ? value : created.format(parsed)
}

// Focus: the panel takes focus when it opens and gives it back to the opener when it closes.
// Esc closes it unless a menu, a list box or the rename field owns the key.
const root = useTemplateRef<HTMLElement>('root')
const heading = useTemplateRef<HTMLElement>('heading')
let opener: HTMLElement | null = null

function onKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape' || event.defaultPrevented || editing.value) return
  const target = event.target as HTMLElement | null
  if (target?.closest('[role="menu"], [role="listbox"], [role="combobox"], [aria-modal="true"]')) return
  emit('close')
}

onMounted(() => {
  opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
  root.value?.focus()
  window.addEventListener('keydown', onKeydown)
})

watch(task, async (value, old) => {
  if (!value || old) return
  await nextTick()
  if (root.value?.contains(document.activeElement)) heading.value?.focus()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  const focusInside = root.value?.contains(document.activeElement) || document.activeElement === document.body
  if (focusInside && opener?.isConnected) opener.focus()
})
</script>

<template>
  <aside
    ref="root"
    tabindex="-1"
    role="dialog"
    aria-modal="false"
    :aria-label="task ? `${t.label}: ${task.subject}` : t.label"
    class="absolute inset-y-0 right-0 z-20 flex w-full flex-col border-outline-gray-2 bg-surface-base shadow-2xl outline-none sm:w-[28rem] sm:border-l"
  >
    <div class="flex min-h-12 items-center justify-between gap-2 border-b border-outline-gray-1 px-4">
      <button
        type="button"
        class="truncate rounded-4 font-mono text-p-sm tabular-nums text-ink-gray-5 hover:text-ink-gray-8 focus-visible:outline focus-visible:outline-2 focus-visible:outline-outline-gray-4"
        :title="c.copyLink"
        @click="copyLink"
      >
        {{ props.name }}
      </button>
      <div class="flex items-center gap-1">
        <Button
          v-if="boot.desk"
          variant="ghost"
          icon="lucide-external-link"
          :tooltip="t.openDesk"
          :aria-label="t.openDesk"
          :href="deskTaskUrl(props.name)"
        />
        <Button variant="ghost" icon="lucide-x" :tooltip="t.close" :aria-label="t.close" @click="emit('close')" />
      </div>
    </div>

    <div v-if="detail.loading && !d" class="space-y-3 p-4" role="status" :aria-label="c.loading">
      <Skeleton class="h-6 w-64" />
      <Skeleton class="h-4 w-40" />
      <Skeleton class="h-24 w-full" />
      <Skeleton class="h-16 w-full" />
    </div>

    <div v-else-if="detail.error" class="space-y-3 p-4" role="alert">
      <p class="text-lg-semibold text-ink-gray-8">{{ t.loadError }}</p>
      <p v-if="forbidden" class="text-p-base text-ink-gray-6">{{ t.notAvailable }}</p>
      <ErrorMessage v-else :message="detail.error" />
      <Button v-if="!forbidden" :label="t.retry" @click="detail.reload()" />
    </div>

    <OverlayScroll v-else-if="d && task" class="min-h-0 flex-1" content-class="space-y-6 px-4 pb-10 pt-4">
      <section :aria-busy="busy">
        <div class="flex items-start gap-2">
          <input
            v-if="editing"
            ref="input"
            v-model="draft"
            maxlength="140"
            class="w-full rounded-4 border border-outline-gray-3 bg-surface-base px-2 py-1 text-xl text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-outline-gray-3"
            :aria-label="c.renameField"
            :title="c.renameHint"
            @keydown.enter.prevent="finishRename(true)"
            @keydown.esc.prevent="finishRename(false)"
            @blur="finishRename(true)"
          />
          <h2
            v-else
            ref="heading"
            tabindex="-1"
            lang="ru"
            class="min-w-0 flex-1 hyphens-auto break-words text-xl text-ink-gray-9 outline-none"
          >
            <span
              v-if="task.is_milestone"
              class="lucide-flag mr-1 inline-block size-4 align-[-2px] text-ink-gray-5"
              role="img"
              :aria-label="t.milestone"
              :title="t.milestone"
            />{{ task.subject }}
          </h2>
          <Button
            v-if="canChange && !editing"
            variant="ghost"
            icon="lucide-pencil"
            :tooltip="c.rename"
            :aria-label="`${c.rename}: ${task.subject}`"
            :disabled="busy"
            @click="startRename"
          />
        </div>

        <div
          v-if="task.block_reason"
          class="mt-3 rounded-4 bg-surface-amber-2 px-2.5 py-1.5 text-p-sm text-ink-amber-7"
        >
          <span class="font-medium">{{ c.blocked }}:</span> {{ task.block_reason }}
        </div>

        <div class="mt-4 flex flex-wrap items-center gap-2">
          <span
            class="flex items-center gap-1.5 rounded-full bg-surface-gray-2 px-2.5 py-1 text-sm text-ink-gray-7"
          >
            <span v-if="steps.isClosed" class="lucide-circle-check size-3.5 text-ink-green-3" aria-hidden="true" />
            <span class="sr-only">{{ t.stage }}:</span>{{ stageLabel }}
          </span>
          <template v-if="d.can_move">
            <Button
              v-if="steps.nextStage"
              icon-right="lucide-arrow-right"
              :label="`${c.nextStage}: ${steps.nextStage.label}`"
              :disabled="busy"
              @click="moveTo(steps.nextStage.name)"
            />
            <Dropdown
              v-if="stageMenu.length"
              :options="stageMenu"
              align="end"
              :button="{ label: c.moveTo, iconRight: 'lucide-chevron-down', variant: 'ghost', disabled: busy }"
            />
          </template>
          <span v-if="busy" class="text-p-xs text-ink-gray-5">{{ c.saving }}</span>
        </div>
      </section>

      <dl class="grid grid-cols-[7.5rem_1fr] gap-x-3 gap-y-2.5 text-sm">
        <dt class="text-ink-gray-5">{{ t.project }}</dt>
        <dd class="min-w-0 break-words">
          <RouterLink v-if="projectHref" :to="projectHref" class="text-ink-gray-8 underline-offset-2 hover:underline">
            {{ projectLabel }}
          </RouterLink>
          <span v-else class="text-ink-gray-7">{{ projectLabel }}</span>
        </dd>

        <dt class="text-ink-gray-5">{{ t.assignees }}</dt>
        <dd class="min-w-0">
          <ul v-if="task.assignees.length" class="space-y-0.5">
            <li v-for="a in task.assignees" :key="a.name" class="break-words text-ink-gray-8">
              {{ a.full_name || a.name }}
            </li>
          </ul>
          <span v-else class="text-ink-gray-5">{{ c.noAssignee }}</span>
          <div v-if="canChange" class="mt-1.5 flex flex-wrap items-center gap-1">
            <Button
              v-if="isMine"
              size="sm"
              icon-left="lucide-user-minus"
              :label="c.leave"
              :disabled="busy"
              @click="runAction(() => unassignFrom(d!.user.name))"
            />
            <Button
              v-else-if="isMember"
              size="sm"
              icon-left="lucide-user-check"
              :label="c.take"
              :disabled="busy"
              @click="runAction(() => assignTo(d!.user.name))"
            />
            <Dropdown
              v-if="assignMenu.length"
              :options="assignMenu"
              align="start"
              :button="{ label: c.assign, size: 'sm', iconLeft: 'lucide-user-plus', variant: 'ghost', disabled: busy }"
            />
          </div>
        </dd>

        <dt class="text-ink-gray-5">{{ t.start }}</dt>
        <dd class="tabular-nums text-ink-gray-7">{{ task.start ? date(task.start) : UNKNOWN }}</dd>

        <dt class="text-ink-gray-5">{{ t.end }}</dt>
        <dd>
          <span
            class="tabular-nums"
            :class="{
              'font-medium text-ink-red-6': task.due_state === 'overdue',
              'rounded-4 bg-surface-amber-2 px-1.5 font-medium text-ink-amber-7': task.due_state === 'today',
              'text-ink-amber-7': task.due_state === 'soon',
              'text-ink-gray-7': !task.due_state,
            }"
          >{{ task.end ? date(task.end) : c.noDate }}</span>
          <span v-if="task.due_state" class="ml-2 text-p-xs" :class="task.due_state === 'overdue' ? 'text-ink-red-6' : 'text-ink-amber-7'">
            {{ c.due[task.due_state] }}
          </span>
        </dd>

        <dt class="text-ink-gray-5">{{ t.place }}</dt>
        <dd class="min-w-0 break-words text-ink-gray-7">{{ place || UNKNOWN }}</dd>
      </dl>

      <section v-if="task.subtasks || d.subtasks.length">
        <h3 class="flex items-baseline gap-2 text-base-semibold text-ink-gray-8">
          {{ t.subtasks }}
          <span v-if="task.subtasks" class="text-sm font-normal tabular-nums text-ink-gray-5">
            {{ task.subtasks.done }}/{{ task.subtasks.total }}
          </span>
        </h3>
        <p v-if="!d.subtasks.length" class="mt-2 text-p-sm text-ink-gray-5">{{ c.noVisibleSubtasks }}</p>
        <ul v-else class="mt-2 space-y-1">
          <li
            v-for="sub in d.subtasks"
            :key="sub.name"
            class="flex items-start gap-2 rounded-4 bg-surface-gray-1 px-2.5 py-1.5 text-sm"
          >
            <span
              :class="sub.stage && closedStages.has(sub.stage) ? 'lucide-circle-check text-ink-green-3' : 'lucide-circle text-ink-gray-4'"
              class="mt-0.5 size-3.5 shrink-0"
              role="img"
              :aria-label="sub.stage && closedStages.has(sub.stage) ? c.completed : (d.stages.find((s) => s.name === sub.stage)?.label ?? ruPm.column.noStage)"
            />
            <RouterLink
              :to="panelLink(sub.name)"
              class="min-w-0 flex-1 break-words hover:underline"
              :class="sub.stage && closedStages.has(sub.stage) ? 'text-ink-gray-5' : 'text-ink-gray-8'"
            >{{ sub.subject }}</RouterLink>
            <span
              class="shrink-0 text-p-xs tabular-nums"
              :class="sub.due_state === 'overdue' ? 'font-medium text-ink-red-6' : 'text-ink-gray-5'"
            >{{ sub.end ? date(sub.end) : c.noDate }}</span>
          </li>
        </ul>
      </section>

      <section>
        <h3 class="text-base-semibold text-ink-gray-8">{{ t.description }}</h3>
        <p v-if="d.description" class="mt-2 whitespace-pre-line break-words text-p-base text-ink-gray-8">{{ d.description }}</p>
        <p v-else class="mt-2 text-p-sm text-ink-gray-5">{{ t.unknown }}</p>
      </section>

      <section>
        <h3 class="flex items-baseline gap-2 text-base-semibold text-ink-gray-8">
          {{ t.comments }}
          <span v-if="d.comments.length" class="text-sm font-normal tabular-nums text-ink-gray-5">{{ d.comments.length }}</span>
        </h3>
        <p v-if="d.comments_truncated" class="mt-1 text-p-xs text-ink-gray-5">{{ t.commentsTruncated }}</p>
        <p v-if="!d.comments.length" class="mt-2 text-p-sm text-ink-gray-5">{{ t.noComments }}</p>
        <ol v-else class="mt-2 space-y-3">
          <li v-for="comment in d.comments" :key="comment.name" class="rounded-6 border border-outline-gray-1 px-3 py-2">
            <div class="flex flex-wrap items-baseline justify-between gap-x-2 text-p-xs text-ink-gray-5">
              <span class="font-medium text-ink-gray-7">{{ comment.author.full_name || comment.author.name }}</span>
              <time :datetime="comment.created" class="tabular-nums">{{ dateTime(comment.created) }}</time>
            </div>
            <p class="mt-1 whitespace-pre-line break-words text-p-sm text-ink-gray-8">{{ comment.text || UNKNOWN }}</p>
          </li>
        </ol>
        <p v-if="boot.desk" class="mt-2 text-p-xs text-ink-gray-5">{{ t.commentsReadOnly }}</p>
      </section>
    </OverlayScroll>
  </aside>
</template>
