<script setup lang="ts">
// Register of projects (UI-03): list or Kanban by state, «Все / Мои», filter pills and counters.
// Only open projects the user may read come from the server; filters work on that list.
import { computed, ref } from 'vue'
import { Button, ErrorMessage, Select, Skeleton, useCall } from 'frappe-ui'
import { OVERVIEW_API, STATUSES, openShell, shellUrl, type ProjectRegister, type ProjectStatus } from '../overviewApi'
import { ruOverview as t } from '../i18n/overview'
import { date, money } from '../format'
import RegisterHeader, { type RegisterView } from '../components/RegisterHeader.vue'
import ProjectTable from '../components/ProjectTable.vue'
import StatusPill from '../components/StatusPill.vue'
import PeopleStack from '../components/PeopleStack.vue'
import DirectionMarks from '../components/DirectionMarks.vue'
import OverlayScroll from '../components/OverlayScroll.vue'

const ANY = '__any__'
const COUNT_STYLE: Record<ProjectStatus, string> = {
  problem: 'text-ink-red-6',
  risk: 'text-ink-amber-7',
  unknown: 'text-ink-gray-8',
  on_plan: 'text-ink-green-6',
}
const COLUMN_STYLE: Record<ProjectStatus, string> = {
  problem: 'bg-surface-red-2 text-ink-red-6',
  risk: 'bg-surface-amber-2 text-ink-amber-8',
  unknown: 'bg-surface-gray-3 text-ink-gray-7',
  on_plan: 'bg-surface-green-2 text-ink-green-6',
}

const data = useCall<ProjectRegister>({ url: OVERVIEW_API.projects })
const view = ref<RegisterView>('list')
const search = ref('')
const mine = ref(false)
const status = ref<ProjectStatus | null>(null)
const pm = ref(ANY)
const customer = ref(ANY)

const forbidden = computed(() => (data.error as { type?: string } | null)?.type === 'PermissionError')
const allRows = computed(() => data.data?.projects.rows ?? [])
const options = (values: (string | null | undefined)[]) => [
  { label: t.register.any, value: ANY },
  ...[...new Set(values.filter((v): v is string => !!v))].sort((a, b) => a.localeCompare(b, 'ru')).map((v) => ({ label: v, value: v })),
]
const pmOptions = computed(() => options(allRows.value.map((r) => r.pm?.full_name || r.pm?.name)))
const customerOptions = computed(() => options(allRows.value.map((r) => r.customer)))

// Status counters follow every filter except the status itself, so a chip shows what it would select.
const scoped = computed(() => {
  const q = search.value.trim().toLocaleLowerCase('ru')
  return allRows.value.filter((r) => {
    if (mine.value && !r.mine) return false
    if (pm.value !== ANY && (r.pm?.full_name || r.pm?.name) !== pm.value) return false
    if (customer.value !== ANY && r.customer !== customer.value) return false
    if (!q) return true
    return [r.project_name, r.name, r.customer].some((v) => v?.toLocaleLowerCase('ru').includes(q))
  })
})
const rows = computed(() => scoped.value.filter((r) => !status.value || r.status === status.value))
const counts = computed(() =>
  Object.fromEntries(STATUSES.map((s) => [s, scoped.value.filter((r) => r.status === s).length])) as Record<ProjectStatus, number>,
)
const filtered = computed(() => mine.value || status.value || pm.value !== ANY || customer.value !== ANY || !!search.value.trim())

function reset() {
  search.value = ''
  mine.value = false
  status.value = null
  pm.value = ANY
  customer.value = ANY
}

function toggleStatus(value: ProjectStatus) {
  status.value = status.value === value ? null : value
}
</script>

<template>
  <OverlayScroll class="h-full bg-surface-gray-1 text-ink-gray-8">
    <div class="mx-auto max-w-7xl space-y-4 px-3 pb-10 pt-4 sm:px-5">
      <RegisterHeader
        v-model:view="view"
        v-model:search="search"
        v-model:mine="mine"
        :search-placeholder="t.register.search"
        :mine-label="t.register.scopeMine"
        :all-label="t.register.scopeAll"
        :scope-label="t.scope.label"
        :list-label="t.register.list"
        :kanban-label="t.register.kanban"
      >
        <Select v-model="pm" :options="pmOptions" :aria-label="t.register.pm" class="w-48">
          <template #prefix><span class="text-p-sm text-ink-gray-5">{{ t.register.pm }}:</span></template>
        </Select>
        <Select v-model="customer" :options="customerOptions" :aria-label="t.register.customer" class="w-56">
          <template #prefix><span class="text-p-sm text-ink-gray-5">{{ t.register.customer }}:</span></template>
        </Select>
        <Button v-if="filtered" variant="ghost" :label="t.register.reset" @click="reset" />
      </RegisterHeader>

      <div v-if="data.error" class="mx-auto max-w-xl pt-6">
        <p class="text-lg-semibold text-ink-gray-8">{{ t.register.error }}</p>
        <p v-if="forbidden" class="mt-2 text-p-base text-ink-gray-6">{{ t.card.forbidden }}</p>
        <ErrorMessage v-else class="mt-2" :message="data.error" />
      </div>

      <div v-else-if="data.loading && !data.data" class="space-y-3">
        <Skeleton class="h-16 w-full rounded-6" />
        <Skeleton class="h-72 w-full rounded-6" />
      </div>

      <template v-else-if="data.data">
        <p class="text-p-sm text-ink-gray-6">{{ t.statusScope }}</p>
        <div class="grid grid-cols-2 gap-2 sm:grid-cols-4" role="group" :aria-label="t.register.status" :title="t.register.statusFilterHint">
          <button
            v-for="s in STATUSES"
            :key="s"
            type="button"
            class="rounded-6 border px-3 py-2 text-left hover:border-outline-gray-4 focus-visible:outline focus-visible:outline-2 focus-visible:outline-outline-gray-4"
            :class="status === s ? 'border-outline-gray-5 bg-surface-gray-2 ring-1 ring-outline-gray-3' : 'border-outline-gray-2 bg-surface-base'"
            :aria-pressed="status === s"
            @click="toggleStatus(s)"
          >
            <span class="flex items-center gap-1.5 text-p-sm text-ink-gray-6">
              <span class="grow">{{ t.status[s] }}</span>
              <span v-if="status === s" class="lucide-check size-3.5 shrink-0 text-ink-gray-8" aria-hidden="true" />
            </span>
            <span class="block text-2xl font-semibold tabular-nums" :class="COUNT_STYLE[s]">{{ counts[s] }}</span>
            <span v-if="status === s" class="sr-only">{{ t.register.statusFilterOn }}</span>
          </button>
        </div>

        <p v-if="!allRows.length" class="rounded-6 border border-dashed border-outline-gray-3 bg-surface-base p-8 text-center text-p-base text-ink-gray-6">
          {{ t.register.empty }}
        </p>
        <p v-else-if="!rows.length" class="rounded-6 border border-dashed border-outline-gray-3 bg-surface-base p-8 text-center text-p-base text-ink-gray-6">
          {{ t.register.emptyFilter }}
        </p>

        <section v-else-if="view === 'list'" class="rounded-6 border border-outline-gray-2 bg-surface-base">
          <ProjectTable :rows="rows" :money-visible="data.data.money_visible" />
        </section>

        <OverlayScroll v-else orientation="horizontal" content-class="flex w-max gap-3 pb-2">
          <div v-for="s in STATUSES" :key="s" class="flex w-72 shrink-0 flex-col gap-2">
            <div class="rounded-4 px-3 py-2 text-p-sm font-medium" :class="COLUMN_STYLE[s]">
              {{ t.status[s] }} · {{ rows.filter((r) => r.status === s).length }}
            </div>
            <a
              v-for="row in rows.filter((r) => r.status === s)"
              :key="row.name"
              :href="shellUrl('projects', row.name)"
              class="flex flex-col gap-1.5 rounded-6 border border-outline-gray-2 bg-surface-base p-3 hover:border-outline-gray-4"
              @click="openShell($event, 'projects', row.name)"
            >
              <span class="flex items-start gap-2">
                <span class="grow font-medium text-ink-gray-9">{{ row.project_name || row.name }}</span>
                <StatusPill :status="row.status" />
              </span>
              <span class="text-p-xs text-ink-gray-5">{{ row.name }} · {{ row.customer || t.noData }}</span>
              <span v-if="row.obstacle" class="text-p-sm text-ink-gray-8">{{ row.obstacle.subject }}</span>
              <span class="flex items-center gap-2 text-p-xs text-ink-gray-6">
                <PeopleStack :people="row.team" />
                <span class="grow">{{ row.expected_end ? date(row.expected_end) : '' }}</span>
                <DirectionMarks :works="row.status" />
              </span>
              <span v-if="data.data.money_visible && row.basis" class="text-p-xs tabular-nums text-ink-gray-6">
                {{ t.table.basis }}: {{ money(row.basis.amount, row.basis.currency) }}
              </span>
            </a>
          </div>
        </OverlayScroll>

        <p class="text-p-xs text-ink-gray-5">{{ view === 'kanban' ? t.register.kanbanHint : t.register.directionsHint }}</p>
        <p v-if="data.data.projects.truncated" class="text-p-sm text-ink-amber-7">{{ t.projects.truncated }}</p>
      </template>
    </div>
  </OverlayScroll>
</template>
