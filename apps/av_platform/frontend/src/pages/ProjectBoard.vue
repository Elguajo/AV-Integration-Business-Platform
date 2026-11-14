<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import {
  Button,
  Checkbox,
  DesktopShell,
  ErrorMessage,
  PageHeader,
  ScrollArea,
  Select,
  Sidebar,
  SidebarHeader,
  SidebarItem,
  Skeleton,
  TextInput,
  toast,
  useCall,
} from 'frappe-ui'
import { PM_API, type Board, type BoardTask, type MoveResult } from '../pmApi'
import { ruPm } from '../i18n/pm'
import BoardCard from '../components/BoardCard.vue'

const NO_STAGE = '__no_stage__'
const ANY = '__any__'
const UNASSIGNED = '__unassigned__'

const board = useCall<Board>({ url: PM_API.board })
const move = useCall<MoveResult, { task: string; stage: string; expected_modified: string }>({
  url: PM_API.move,
  method: 'POST',
  immediate: false,
})

// Local copy so a confirmed move updates one card without reloading the board.
const tasks = ref<BoardTask[]>([])
watch(() => board.data, (data) => { tasks.value = data ? [...data.tasks] : [] }, { immediate: true })

const saving = reactive(new Set<string>())
const dropTarget = ref<string | null>(null)

const filters = reactive({
  project: ANY,
  assignee: ANY,
  place: '',
  due: ANY,
  blockedOnly: false,
})

const projectNames = computed(
  () => new Map((board.data?.projects ?? []).map((p) => [p.name, p.project_name])),
)
const stageNames = computed(() => new Set((board.data?.stages ?? []).map((s) => s.name)))

const projectOptions = computed(() => [
  { label: ruPm.filter.allProjects, value: ANY },
  ...(board.data?.projects ?? []).map((p) => ({ label: p.project_name, value: p.name })),
])

const assigneeOptions = computed(() => {
  const people = new Map<string, string>()
  for (const task of tasks.value) {
    for (const a of task.assignees) people.set(a.name, a.full_name || a.name)
  }
  const me = board.data?.user.name
  return [
    { label: ruPm.filter.anyone, value: ANY },
    ...(me ? [{ label: ruPm.filter.me, value: me }] : []),
    { label: ruPm.filter.unassigned, value: UNASSIGNED },
    ...[...people]
      .filter(([name]) => name !== me)
      .sort((a, b) => a[1].localeCompare(b[1], 'ru'))
      .map(([value, label]) => ({ label, value })),
  ]
})

const dueOptions = [
  { label: ruPm.filter.anyDue, value: ANY },
  { label: ruPm.filter.overdue, value: 'overdue' },
  { label: ruPm.filter.week, value: 'week' },
  { label: ruPm.filter.noDate, value: 'none' },
]

function dayStart(offset = 0) {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  d.setDate(d.getDate() + offset)
  return d
}

function matches(task: BoardTask) {
  if (filters.project !== ANY && task.project !== filters.project) return false
  if (filters.assignee === UNASSIGNED && task.assignees.length) return false
  if (
    filters.assignee !== ANY &&
    filters.assignee !== UNASSIGNED &&
    !task.assignees.some((a) => a.name === filters.assignee)
  ) return false
  const place = filters.place.trim().toLowerCase()
  if (place && ![task.room, task.system].some((v) => v?.toLowerCase().includes(place))) return false
  if (filters.blockedOnly && !task.block_reason) return false
  if (filters.due === 'overdue' && !task.is_overdue) return false
  if (filters.due === 'none' && task.end) return false
  if (filters.due === 'week') {
    if (!task.end) return false
    const end = new Date(`${task.end.slice(0, 10)}T00:00:00`)
    if (end >= dayStart(8)) return false
  }
  return true
}

function byDue(a: BoardTask, b: BoardTask) {
  if (a.end && b.end) return a.end.localeCompare(b.end)
  if (a.end) return -1
  if (b.end) return 1
  return a.subject.localeCompare(b.subject, 'ru')
}

const visible = computed(() => tasks.value.filter(matches).sort(byDue))
const filtersActive = computed(
  () =>
    filters.project !== ANY ||
    filters.assignee !== ANY ||
    !!filters.place.trim() ||
    filters.due !== ANY ||
    filters.blockedOnly,
)

const columns = computed(() => {
  const groups = new Map<string, BoardTask[]>()
  for (const task of visible.value) {
    const key = task.stage && stageNames.value.has(task.stage) ? task.stage : NO_STAGE
    groups.set(key, [...(groups.get(key) ?? []), task])
  }
  const stages = (board.data?.stages ?? []).map((s) => ({
    key: s.name,
    label: s.label,
    tasks: groups.get(s.name) ?? [],
  }))
  // Tasks created before the board existed have no stage; show them instead of hiding them.
  const orphans = groups.get(NO_STAGE)
  return orphans?.length ? [{ key: NO_STAGE, label: ruPm.column.noStage, tasks: orphans }, ...stages] : stages
})

const forbidden = computed(() => (board.error as { type?: string } | null)?.type === 'PermissionError')
const noProjects = computed(() => board.data && !board.data.projects.length && !tasks.value.length)
const projectEmpty = computed(
  () => board.data && filters.project !== ANY && !tasks.value.some((t) => t.project === filters.project),
)

const newTaskHref = computed(() =>
  filters.project !== ANY
    ? `/app/task/new?project=${encodeURIComponent(filters.project)}`
    : '/app/task/new',
)

function replaceTask(task: BoardTask) {
  tasks.value = tasks.value.map((t) => (t.name === task.name ? task : t))
}

async function moveTask(name: string, stage: string) {
  const task = tasks.value.find((t) => t.name === name)
  if (!task || task.stage === stage || saving.has(name) || stage === NO_STAGE) return
  saving.add(name)
  try {
    // The card stays in its column until the server confirms the move (PLAN-06).
    await move.submit({ task: name, stage, expected_modified: task.modified })
    // Read the unwrapped response from `data`, as the Sales handover dialog does.
    const result = move.data
    if (!result) return
    if (result.task) replaceTask(result.task)
    if (result.ok) {
      const label = board.data?.stages.find((s) => s.name === stage)?.label
      toast.success(ruPm.moved, { description: `${task.subject} → ${label ?? stage}` })
    } else {
      toast.error(ruPm.notMoved, { description: ruPm.reject[result.code] })
    }
  } catch (error) {
    const message = (error as { messages?: string[]; message?: string }).messages?.[0]
      ?? (error as Error).message
    toast.error(ruPm.error.save, { description: message })
  } finally {
    saving.delete(name)
  }
}

function onDrop(event: DragEvent, stage: string) {
  dropTarget.value = null
  const name = event.dataTransfer?.getData('text/plain')
  if (name) moveTask(name, stage)
}

function resetFilters() {
  Object.assign(filters, { project: ANY, assignee: ANY, place: '', due: ANY, blockedOnly: false })
}
</script>

<template>
  <div class="h-screen w-full bg-surface-base text-ink-gray-8">
    <DesktopShell :scroll="false">
      <template #sidebar>
        <Sidebar width="14rem" class="border-r">
          <SidebarHeader :title="ruPm.nav.board" :subtitle="board.data?.user.full_name ?? ruPm.role" />
          <div class="space-y-0.5 px-2 pt-0.5">
            <SidebarItem :label="ruPm.nav.myTasks" icon="lucide-list-checks" :route="{ name: 'MyTasks' }" />
            <SidebarItem :label="ruPm.nav.board" icon="lucide-square-kanban" :route="{ name: 'Board' }" active />
            <SidebarItem :label="ruPm.nav.quotations" icon="lucide-file-text" :route="{ name: 'Sales' }" />
            <SidebarItem :label="ruPm.nav.desk" icon="lucide-external-link" href="/app" />
          </div>
        </Sidebar>
      </template>

      <PageHeader>
        <div class="flex w-full items-center justify-between gap-2">
          <div class="flex min-w-0 items-baseline gap-3">
            <h1 class="truncate text-lg-semibold text-ink-gray-9">{{ ruPm.page.title }}</h1>
            <span class="hidden text-sm text-ink-gray-5 sm:inline">{{ ruPm.page.subtitle }}</span>
          </div>
          <div class="flex items-center gap-2">
            <Button
              v-if="board.data?.can_move"
              icon-left="lucide-plus"
              :label="ruPm.page.newTask"
              :href="newTaskHref"
            />
            <Button
              icon-left="lucide-refresh-cw"
              :label="ruPm.page.refresh"
              :loading="board.loading"
              @click="board.reload()"
            />
          </div>
        </div>
      </PageHeader>

      <div class="flex h-full min-h-0 flex-col">
        <div v-if="board.error" class="mx-auto max-w-xl px-5 pt-10">
          <p class="text-lg-semibold text-ink-gray-8">{{ ruPm.error.title }}</p>
          <p v-if="forbidden" class="mt-2 text-p-base text-ink-gray-6">{{ ruPm.error.forbidden }}</p>
          <ErrorMessage v-else class="mt-2" :message="board.error" />
        </div>

        <div v-else-if="board.loading && !board.data" class="flex gap-3 px-5 pt-5">
          <Skeleton v-for="i in 5" :key="i" class="h-72 w-72 shrink-0 rounded-6" />
        </div>

        <div
          v-else-if="noProjects"
          class="flex flex-col items-center justify-center gap-3 py-24 text-center"
        >
          <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
            <span class="lucide-folder-kanban size-6" aria-hidden="true" />
          </div>
          <p class="text-base text-ink-gray-7">{{ ruPm.empty.noProjects }}</p>
          <p class="max-w-sm text-sm text-ink-gray-5">{{ ruPm.empty.noProjectsHint }}</p>
        </div>

        <template v-else-if="board.data">
          <div class="flex flex-wrap items-end gap-2 px-5 pb-1 pt-4" role="search">
            <Select v-model="filters.project" :options="projectOptions" :aria-label="ruPm.filter.project" class="w-56" />
            <Select v-model="filters.assignee" :options="assigneeOptions" :aria-label="ruPm.filter.assignee" class="w-48" />
            <TextInput
              v-model="filters.place"
              :placeholder="ruPm.filter.place"
              :aria-label="ruPm.filter.place"
              class="w-52"
            />
            <Select v-model="filters.due" :options="dueOptions" :aria-label="ruPm.filter.due" class="w-40" />
            <Checkbox v-model="filters.blockedOnly" :label="ruPm.filter.blocked" class="h-7" />
            <Button v-if="filtersActive" variant="ghost" :label="ruPm.filter.reset" @click="resetFilters" />
          </div>
          <p v-if="board.data.truncated" class="px-5 pt-1 text-sm text-ink-amber-7">{{ ruPm.truncated }}</p>

          <div
            v-if="projectEmpty"
            class="flex flex-col items-center justify-center gap-3 py-20 text-center"
          >
            <p class="text-base text-ink-gray-7">{{ ruPm.empty.noTasks }}</p>
            <p class="text-sm text-ink-gray-5">{{ ruPm.empty.noTasksHint }}</p>
            <Button
              v-if="board.data.can_move"
              variant="solid"
              icon-left="lucide-plus"
              :label="ruPm.page.newTask"
              :href="newTaskHref"
            />
          </div>

          <div v-else-if="filtersActive && !visible.length" class="flex flex-col items-center gap-3 py-20 text-center">
            <p class="text-base text-ink-gray-7">{{ ruPm.empty.filtered }}</p>
            <Button :label="ruPm.filter.reset" @click="resetFilters" />
          </div>

          <div v-else class="flex min-h-0 flex-1 gap-3 overflow-x-auto px-5 pb-5 pt-3">
            <section
              v-for="column in columns"
              :key="column.key"
              class="flex w-72 shrink-0 flex-col rounded-6 bg-surface-gray-1 transition-shadow"
              :class="{ 'ring-2 ring-outline-gray-3': dropTarget === column.key }"
              :aria-label="column.label"
              @dragover.prevent="dropTarget = column.key"
              @dragleave="dropTarget = dropTarget === column.key ? null : dropTarget"
              @drop.prevent="onDrop($event, column.key)"
            >
              <header class="flex items-center justify-between px-3 pb-2 pt-3">
                <h2 class="text-base-semibold text-ink-gray-8">{{ column.label }}</h2>
                <span class="text-sm tabular-nums text-ink-gray-5">{{ column.tasks.length }}</span>
              </header>
              <ScrollArea class="min-h-0 flex-1" viewport-class="space-y-2 px-2 pb-3">
                <BoardCard
                  v-for="task in column.tasks"
                  :key="task.name"
                  :task="task"
                  :stages="board.data.stages"
                  :project-name="filters.project === ANY && task.project ? projectNames.get(task.project) ?? task.project : null"
                  :can-move="board.data.can_move"
                  :saving="saving.has(task.name)"
                  @move="moveTask(task.name, $event)"
                />
                <p v-if="!column.tasks.length" class="px-3 py-6 text-center text-p-sm text-ink-gray-4">
                  {{ ruPm.column.empty }}
                </p>
              </ScrollArea>
            </section>
          </div>
        </template>
      </div>
    </DesktopShell>
  </div>
</template>
