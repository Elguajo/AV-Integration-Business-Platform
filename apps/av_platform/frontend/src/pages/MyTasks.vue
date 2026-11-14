<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import {
  Button,
  DesktopShell,
  ErrorMessage,
  PageHeader,
  Select,
  Sidebar,
  SidebarHeader,
  SidebarItem,
  Skeleton,
  TextInput,
  toast,
  useCall,
} from 'frappe-ui'
import {
  PM_API,
  type BoardTask,
  type DueBucket,
  type MoveResult,
  type MyTask,
  type MyTaskView,
  type MyTasks,
} from '../pmApi'
import { ruPm } from '../i18n/pm'
import { date } from '../format'
import MyTaskRow from '../components/MyTaskRow.vue'

const ANY = '__any__'
const BUCKETS: DueBucket[] = ['overdue', 'today', 'week', 'later', 'no_date']
const VIEWS: MyTaskView[] = ['mine', 'delegated']

const view = ref<MyTaskView>('mine')
const list = useCall<MyTasks, { view: MyTaskView }>({
  url: PM_API.myTasks,
  params: () => ({ view: view.value }),
  refetch: true,
})
const move = useCall<MoveResult, { task: string; stage: string; expected_modified: string }>({
  url: PM_API.move,
  method: 'POST',
  immediate: false,
})

// Local copy so a confirmed move updates one row without reloading the list.
const tasks = ref<MyTask[]>([])
watch(() => list.data, (data) => { tasks.value = data ? [...data.tasks] : [] }, { immediate: true })

const saving = reactive(new Set<string>())
const collapsed = reactive(new Set<DueBucket>())
const filters = reactive({ project: ANY, search: '' })

const projectNames = computed(
  () => new Map((list.data?.projects ?? []).map((p) => [p.name, p.project_name])),
)
const projectOptions = computed(() => [
  { label: ruPm.my.allProjects, value: ANY },
  ...(list.data?.projects ?? []).map((p) => ({ label: p.project_name, value: p.name })),
])

// A work completed or cancelled from this page leaves the list, as the server would omit it.
function isOpen(task: MyTask) {
  return task.status !== 'Completed' && task.status !== 'Cancelled'
}

function matches(task: MyTask) {
  if (!isOpen(task)) return false
  if (filters.project !== ANY && task.project !== filters.project) return false
  const search = filters.search.trim().toLowerCase()
  if (search && ![task.subject, task.room, task.system].some((v) => v?.toLowerCase().includes(search))) {
    return false
  }
  return true
}

const visible = computed(() => tasks.value.filter(matches))
const filtersActive = computed(() => filters.project !== ANY || !!filters.search.trim())
const groups = computed(() =>
  BUCKETS.map((bucket) => ({
    bucket,
    label: ruPm.my.buckets[bucket],
    tasks: visible.value.filter((t) => t.bucket === bucket),
  })).filter((g) => g.tasks.length),
)
const forbidden = computed(() => (list.error as { type?: string } | null)?.type === 'PermissionError')
const isEmpty = computed(() => list.data && !tasks.value.some(isOpen))

watch(view, () => {
  filters.project = ANY
  collapsed.clear()
})

function toggle(bucket: DueBucket) {
  if (collapsed.has(bucket)) collapsed.delete(bucket)
  else collapsed.add(bucket)
}

function replaceTask(task: BoardTask) {
  // A move never changes the due date, so the row keeps its group until the next reload.
  tasks.value = tasks.value.map((t) => (t.name === task.name ? { ...task, bucket: t.bucket } : t))
}

async function moveTask(name: string, stage: string) {
  const task = tasks.value.find((t) => t.name === name)
  if (!task || task.stage === stage || saving.has(name)) return
  saving.add(name)
  try {
    // The row keeps its stage until the server confirms the move (PLAN-06).
    await move.submit({ task: name, stage, expected_modified: task.modified })
    const result = move.data
    if (!result) return
    if (result.task) replaceTask(result.task)
    if (result.ok) {
      const label = list.data?.stages.find((s) => s.name === stage)?.label
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

function resetFilters() {
  Object.assign(filters, { project: ANY, search: '' })
}
</script>

<template>
  <div class="h-screen w-full bg-surface-base text-ink-gray-8">
    <DesktopShell :scroll="false">
      <template #sidebar>
        <Sidebar width="14rem" class="border-r">
          <SidebarHeader :title="ruPm.nav.myTasks" :subtitle="list.data?.user.full_name ?? ruPm.role" />
          <div class="space-y-0.5 px-2 pt-0.5">
            <SidebarItem :label="ruPm.nav.myTasks" icon="lucide-list-checks" :route="{ name: 'MyTasks' }" active />
            <SidebarItem :label="ruPm.nav.board" icon="lucide-square-kanban" :route="{ name: 'Board' }" />
            <SidebarItem :label="ruPm.nav.quotations" icon="lucide-file-text" :route="{ name: 'Sales' }" />
            <SidebarItem :label="ruPm.nav.desk" icon="lucide-external-link" href="/app" />
          </div>
        </Sidebar>
      </template>

      <PageHeader>
        <div class="flex w-full flex-wrap items-center justify-between gap-2">
          <div class="flex min-w-0 items-baseline gap-3">
            <h1 class="truncate text-lg-semibold text-ink-gray-9">{{ ruPm.my.title }}</h1>
            <span v-if="list.data" class="text-sm text-ink-gray-5">
              {{ ruPm.my.todayIs }}: {{ date(list.data.today) }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <div class="flex rounded-6 bg-surface-gray-2 p-0.5" role="group" :aria-label="ruPm.my.title">
              <Button
                v-for="v in VIEWS"
                :key="v"
                :variant="view === v ? 'outline' : 'ghost'"
                :label="ruPm.my.views[v]"
                :aria-pressed="view === v"
                @click="view = v"
              />
            </div>
            <Button
              icon="lucide-refresh-cw"
              :tooltip="ruPm.page.refresh"
              :aria-label="ruPm.page.refresh"
              :loading="list.loading"
              @click="list.reload()"
            />
          </div>
        </div>
      </PageHeader>

      <div class="h-full min-h-0 overflow-y-auto">
        <div class="mx-auto max-w-5xl px-4 pb-10 pt-4 sm:px-5">
          <div v-if="list.error" class="mx-auto max-w-xl pt-6">
            <p class="text-lg-semibold text-ink-gray-8">{{ ruPm.my.error }}</p>
            <p v-if="forbidden" class="mt-2 text-p-base text-ink-gray-6">{{ ruPm.error.forbidden }}</p>
            <ErrorMessage v-else class="mt-2" :message="list.error" />
          </div>

          <div v-else-if="list.loading && !list.data" class="space-y-2">
            <Skeleton v-for="i in 6" :key="i" class="h-14 w-full rounded-6" />
          </div>

          <div v-else-if="isEmpty" class="flex flex-col items-center gap-3 py-20 text-center">
            <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
              <span class="lucide-list-checks size-6" aria-hidden="true" />
            </div>
            <p class="text-base text-ink-gray-7">{{ view === 'mine' ? ruPm.my.empty.mine : ruPm.my.empty.delegated }}</p>
            <p class="max-w-md text-sm text-ink-gray-5">
              {{ view === 'mine' ? ruPm.my.empty.mineHint : ruPm.my.empty.delegatedHint }}
            </p>
          </div>

          <template v-else-if="list.data">
            <div class="flex flex-wrap items-end gap-2 pb-3" role="search">
              <Select
                v-if="list.data.projects.length > 1"
                v-model="filters.project"
                :options="projectOptions"
                :aria-label="ruPm.filter.project"
                class="w-56"
              />
              <TextInput
                v-model="filters.search"
                :placeholder="ruPm.my.search"
                :aria-label="ruPm.my.search"
                class="w-64"
              />
              <Button v-if="filtersActive" variant="ghost" :label="ruPm.filter.reset" @click="resetFilters" />
            </div>
            <p v-if="list.data.truncated" class="pb-2 text-sm text-ink-amber-7">{{ ruPm.my.truncated }}</p>

            <div v-if="!groups.length" class="flex flex-col items-center gap-3 py-16 text-center">
              <p class="text-base text-ink-gray-7">{{ ruPm.my.empty.filtered }}</p>
              <Button :label="ruPm.filter.reset" @click="resetFilters" />
            </div>

            <section
              v-for="group in groups"
              :key="group.bucket"
              class="mb-4 overflow-hidden rounded-6 border border-outline-gray-1"
              :aria-label="group.label"
            >
              <button
                type="button"
                class="flex w-full items-center gap-2 bg-surface-gray-1 px-3 py-2 text-left"
                :aria-expanded="!collapsed.has(group.bucket)"
                :title="collapsed.has(group.bucket) ? ruPm.my.expand : ruPm.my.collapse"
                @click="toggle(group.bucket)"
              >
                <span
                  class="size-4 text-ink-gray-5"
                  :class="collapsed.has(group.bucket) ? 'lucide-chevron-right' : 'lucide-chevron-down'"
                  aria-hidden="true"
                />
                <h2
                  class="text-base-semibold"
                  :class="group.bucket === 'overdue' ? 'text-ink-red-4' : 'text-ink-gray-8'"
                >
                  {{ group.label }}
                </h2>
                <span class="text-sm tabular-nums text-ink-gray-5">{{ group.tasks.length }}</span>
              </button>
              <ul v-show="!collapsed.has(group.bucket)">
                <MyTaskRow
                  v-for="task in group.tasks"
                  :key="task.name"
                  :task="task"
                  :stages="list.data.stages"
                  :project-name="list.data.projects.length > 1 && task.project ? projectNames.get(task.project) ?? task.project : null"
                  :can-move="list.data.can_move"
                  :saving="saving.has(task.name)"
                  :show-assignees="view === 'delegated'"
                  @move="moveTask(task.name, $event)"
                />
              </ul>
            </section>
          </template>
        </div>
      </div>
    </DesktopShell>
  </div>
</template>
