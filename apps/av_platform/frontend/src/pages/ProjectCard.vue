<script setup lang="ts">
// Project card (UI-03, UI-04): record header, rail of sections, main area and side panel.
// Works are filtered by stage with a row of chips; the grouping tree returns with rooms and systems.
// Sections of modules that do not exist yet are not shown; directions without data say so.
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, ErrorMessage, Skeleton, useCall } from 'frappe-ui'
import {
  OVERVIEW_API,
  deskUrl,
  openShell,
  shellUrl,
  type ProjectCardData,
  type Work,
} from '../overviewApi'
import { ruOverview as t } from '../i18n/overview'
import { date, money } from '../format'
import RecordShell, { type RecordSection } from '../components/RecordShell.vue'
import OverlayScroll from '../components/OverlayScroll.vue'
import StatusPill from '../components/StatusPill.vue'
import PeopleStack from '../components/PeopleStack.vue'
import TaskPanel from '../components/TaskPanel.vue'
import { TASK_QUERY } from '../pmApi'

const props = defineProps<{ project?: string }>()

const NO_STAGE = '__none__'
// Directions that have no data in the card yet; they are listed in one line, never as zero.
const UNTRACKED = ['procurement', 'install', 'tests', 'money'] as const
const data = useCall<ProjectCardData, { project: string }>({
  url: OVERVIEW_API.project,
  params: () => ({ project: props.project ?? '' }),
  refetch: true,
})
const section = ref('overview')
// A work opens in the side panel on this page: /av/projects/<id>?task=<name>. The panel reads
// through the server's own permission check, so it also serves users without the board screen.
const route = useRoute()
const router = useRouter()
const openTask = computed(() => {
  const value = route.query[TASK_QUERY]
  return typeof value === 'string' && value ? value : null
})

function taskLink(name: string) {
  return { query: { ...route.query, [TASK_QUERY]: name } }
}

function closePanel() {
  const { [TASK_QUERY]: _closed, ...query } = route.query
  router.push({ query })
}
const stage = ref<string | null>(null)

watch(
  () => props.project,
  () => {
    section.value = 'overview'
    stage.value = null
  },
)

const card = computed(() => data.data)
const p = computed(() => card.value?.project)
const forbidden = computed(
  () => !props.project || (data.error as { type?: string } | null)?.type === 'PermissionError',
)
const openWorks = computed(() => (card.value?.works ?? []).filter((w) => !['Completed', 'Cancelled'].includes(w.status)))
const stageLabel = computed(() => new Map((card.value?.stages ?? []).map((s) => [s.name, s.label])))
const stageCounts = computed(() => {
  const counts = new Map<string, number>()
  for (const work of card.value?.works ?? []) {
    const key = work.stage ?? NO_STAGE
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }
  return counts
})
const stageRows = computed(() => [
  ...(card.value?.stages ?? []).map((s) => ({ key: s.name, label: s.label })),
  ...(stageCounts.value.has(NO_STAGE) ? [{ key: NO_STAGE, label: t.card.noStage }] : []),
])
const shownWorks = computed(() =>
  (card.value?.works ?? []).filter((w) => !stage.value || (w.stage ?? NO_STAGE) === stage.value),
)
const sections = computed<RecordSection[]>(() => [
  { key: 'overview', label: t.card.sections.overview, icon: 'lucide-layout-dashboard' },
  { key: 'works', label: t.card.sections.works, icon: 'lucide-square-kanban', count: card.value?.works.length },
  { key: 'details', label: t.card.sections.details, icon: 'lucide-info' },
  { key: 'files', label: t.card.sections.files, icon: 'lucide-paperclip', count: card.value?.files.length },
])
const blockedCount = computed(() => (card.value?.obstacles ?? []).filter((o) => o.kind === 'blocked').length)
const overdueCount = computed(() => (card.value?.obstacles ?? []).filter((o) => o.kind === 'overdue').length)

function people(work: Work) {
  return work.assignees.length ? work.assignees.map((a) => a.full_name || a.name).join(', ') : t.card.nobody
}

function dueClass(work: Work) {
  if (work.due === 'overdue') return 'font-medium text-ink-red-6'
  if (work.due === 'today' || work.due === 'soon') return 'text-ink-amber-7'
  return 'text-ink-gray-5'
}

function workStatus(work: Work) {
  return (work.stage && stageLabel.value.get(work.stage)) || work.status
}
</script>

<template>
  <div class="relative h-full text-ink-gray-8">
    <OverlayScroll v-if="data.error || forbidden || !card" class="h-full" content-class="px-3 pb-10 pt-4 sm:px-5">
      <div v-if="data.error || forbidden" class="mx-auto max-w-xl pt-6">
        <p class="text-lg-semibold text-ink-gray-8">{{ t.card.error }}</p>
        <p v-if="forbidden" class="mt-2 text-p-base text-ink-gray-6">{{ t.card.forbidden }}</p>
        <ErrorMessage v-else class="mt-2" :message="data.error" />
        <a :href="shellUrl('projects')" class="mt-4 inline-block text-p-sm text-ink-blue-link hover:underline" @click="openShell($event, 'projects')">
          {{ t.card.back }}
        </a>
      </div>

      <div v-else class="space-y-3">
        <Skeleton class="h-14 w-full rounded-6" />
        <Skeleton class="h-96 w-full rounded-6" />
      </div>
    </OverlayScroll>

    <RecordShell v-else-if="p" v-model:active="section" :sections="sections" :sections-label="t.card.sectionsLabel">
      <template #nav-top>
        <a
          :href="shellUrl('projects')"
          class="flex h-8 shrink-0 items-center gap-2.5 whitespace-nowrap rounded-4 px-2 text-p-sm text-ink-gray-6 hover:bg-surface-gray-2"
          :title="t.card.back"
          @click="openShell($event, 'projects')"
        >
          <span class="lucide-arrow-left size-4 shrink-0" aria-hidden="true" />
          <span class="max-lg:sr-only">{{ t.card.back }}</span>
        </a>
        <!-- Whose sections these are: the column reads as the project's menu, not a second app menu. -->
        <div class="mb-2 mt-1 space-y-1 border-b border-outline-gray-2 px-2 pb-3 max-lg:hidden">
          <span class="block text-p-xs tabular-nums text-ink-gray-5">{{ p.name }}</span>
          <span class="line-clamp-2 block text-p-sm font-semibold text-ink-gray-9" :title="p.project_name || p.name">{{ p.project_name || p.name }}</span>
          <StatusPill :status="p.status" />
        </div>
      </template>
      <template #header>
        <h1 class="min-w-0 break-words text-lg font-semibold text-ink-gray-9">{{ p.project_name || p.name }}</h1>
        <span class="text-p-sm text-ink-gray-5 lg:hidden">{{ p.name }}</span>
        <StatusPill :status="p.status" />
        <span class="text-p-sm text-ink-gray-6">
          {{ p.customer || t.noData }} ·
          <template v-if="p.pm">{{ t.projects.pm }} {{ p.pm.full_name || p.pm.name }}</template>
          <template v-else>{{ card.money_visible ? t.card.pmNone : t.card.pmHidden }}</template>
        </span>
        <span class="grow" />
        <PeopleStack :people="p.team" />
        <span
          v-if="card.money_visible"
          class="rounded-4 border border-outline-gray-3 px-2.5 py-1 text-p-sm font-medium tabular-nums text-ink-gray-8"
        >
          {{ t.table.basis }}: {{ p.basis ? money(p.basis.amount, p.basis.currency) : t.noData }}
        </span>
        <Button icon="lucide-refresh-cw" :tooltip="t.refresh" :aria-label="t.refresh" :loading="data.loading" @click="data.reload()" />
      </template>

      <!-- Overview -->
      <template v-if="section === 'overview'">
        <p class="text-p-sm text-ink-gray-6">{{ t.card.statusScope }}</p>
        <div class="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-2">
          <div class="rounded-4 border border-outline-gray-2 bg-surface-gray-1 px-3 py-2">
            <span class="text-p-xs text-ink-gray-6">{{ t.directions.works }}</span>
            <span class="block text-lg font-semibold tabular-nums text-ink-gray-9">
              {{ p.works.total ? t.card.worksDone(p.works.done, p.works.total) : t.noData }}
            </span>
            <span v-if="blockedCount || overdueCount" class="text-p-xs text-ink-red-6">
              {{ t.card.blocked }}: {{ blockedCount }} · {{ t.card.overdue }}: {{ overdueCount }}
            </span>
          </div>
        </div>
        <!-- Directions without a registry yet: one muted line. A direction that gets data leaves UNTRACKED and gets a tile above. -->
        <p class="text-p-sm text-ink-gray-5">{{ t.card.untracked(UNTRACKED.map((key) => t.directions[key])) }}</p>

        <div class="grid grid-cols-[repeat(auto-fit,minmax(min(100%,280px),1fr))] gap-3">
          <section class="rounded-6 border border-outline-gray-2 p-3">
            <h2 class="mb-2 text-p-base font-semibold text-ink-gray-9">{{ t.card.basis }}</h2>
            <template v-if="!card.money_visible">
              <p class="text-p-sm text-ink-gray-5">{{ t.hidden }}</p>
            </template>
            <template v-else-if="p.basis">
              <p class="text-2xl font-semibold tabular-nums text-ink-gray-9">{{ money(p.basis.amount, p.basis.currency) }}</p>
              <p class="mt-1 text-p-sm text-ink-gray-6">
                <a :href="deskUrl('Quotation', p.basis.quotation)" class="hover:underline">{{ t.card.basisFrom(p.basis.quotation) }}</a>
                <template v-if="p.handover?.reviewed_on"> · {{ t.card.acceptedOn }} {{ date(p.handover.reviewed_on) }}</template>
              </p>
            </template>
            <p v-else class="text-p-sm text-ink-gray-5">{{ t.card.noBasis }}</p>
          </section>

          <section class="rounded-6 border border-outline-gray-2 p-3">
            <h2 class="mb-2 flex items-center gap-2 text-p-base font-semibold text-ink-gray-9">
              {{ t.card.obstacles }}
              <span v-if="card.obstacles.length" class="rounded-3 bg-surface-red-2 px-1.5 text-p-xs text-ink-red-6">{{ card.obstacles.length }}</span>
            </h2>
            <p v-if="!card.obstacles.length" class="text-p-sm text-ink-gray-5">{{ t.card.noObstacles }}</p>
            <ul v-else class="divide-y divide-outline-gray-1">
              <li v-for="work in card.obstacles.slice(0, 6)" :key="work.name" class="flex gap-2 py-1.5">
                <span class="mt-1.5 size-2 shrink-0 rounded-full" :class="work.kind === 'blocked' ? 'bg-surface-red-5' : 'bg-surface-amber-5'" aria-hidden="true" />
                <div class="min-w-0 text-p-sm">
                  <RouterLink :to="taskLink(work.name)" class="font-medium text-ink-gray-8 hover:underline">{{ work.subject }}</RouterLink>
                  <p v-if="work.block_reason" class="text-ink-amber-7">{{ work.block_reason }}</p>
                  <p class="text-p-xs text-ink-gray-5">
                    {{ work.kind === 'blocked' ? t.card.blocked : t.card.overdue }} · {{ people(work) }} ·
                    <span :class="dueClass(work)">{{ t.card.due }} {{ date(work.end) }}</span>
                  </p>
                </div>
              </li>
            </ul>
          </section>
        </div>

        <section class="rounded-6 border border-outline-gray-2 p-3">
          <h2 class="mb-2 text-p-base font-semibold text-ink-gray-9">{{ t.card.reasons }}</h2>
          <ul class="flex flex-wrap gap-1.5">
            <li v-for="reason in p.reasons" :key="reason.code" class="rounded-3 bg-surface-gray-2 px-2 py-0.5 text-p-xs text-ink-gray-7">
              {{ t.reasons[reason.code](reason.count) }}
            </li>
            <li v-if="p.status === 'on_plan'" class="text-p-xs text-ink-gray-5">{{ t.card.onPlan }}</li>
          </ul>
        </section>

        <section class="rounded-6 border border-outline-gray-2 p-3">
          <h2 class="mb-2 text-p-base font-semibold text-ink-gray-9">{{ t.card.milestones }}</h2>
          <p v-if="!card.milestones.length" class="text-p-sm text-ink-gray-5">{{ t.card.noMilestones }}</p>
          <ul v-else class="divide-y divide-outline-gray-1">
            <li v-for="work in card.milestones" :key="work.name" class="flex flex-wrap items-baseline justify-between gap-2 py-1.5 text-p-sm">
              <RouterLink :to="taskLink(work.name)" class="text-ink-gray-8 hover:underline">{{ work.subject }}</RouterLink>
              <span :class="dueClass(work)">{{ date(work.end) }}</span>
            </li>
          </ul>
        </section>
      </template>

      <!-- Works -->
      <template v-else-if="section === 'works'">
        <div class="flex flex-wrap items-center gap-2">
          <h2 class="text-p-base font-semibold text-ink-gray-9">
            {{ t.card.sections.works }}<template v-if="stage"> · {{ stage === NO_STAGE ? t.card.noStage : stageLabel.get(stage) }}</template>
          </h2>
          <span class="grow" />
          <a :href="shellUrl('board')" @click="openShell($event, 'board')">
            <Button icon-left="lucide-square-kanban" :label="t.card.openBoard" />
          </a>
        </div>
        <div v-if="card.works.length" class="flex flex-wrap gap-1.5" role="group" :aria-label="t.card.stages">
          <button
            v-for="row in [{ key: null, label: t.card.wholeProject }, ...stageRows]"
            :key="row.key ?? 'all'"
            type="button"
            class="rounded-full border px-2.5 py-0.5 text-p-sm"
            :class="stage === row.key ? 'border-outline-blue-1 bg-surface-blue-2 text-ink-blue-6' : 'border-outline-gray-2 text-ink-gray-7 hover:bg-surface-gray-2'"
            :aria-pressed="stage === row.key"
            @click="stage = row.key"
          >
            {{ row.label }} <span class="tabular-nums text-ink-gray-5">{{ row.key ? (stageCounts.get(row.key) ?? 0) : card.works.length }}</span>
          </button>
        </div>
        <p v-if="!card.works.length" class="rounded-6 border border-dashed border-outline-gray-3 p-6 text-center text-p-sm text-ink-gray-6">{{ t.card.noWorks }}</p>
        <OverlayScroll v-else orientation="horizontal" class="rounded-6 border border-outline-gray-2">
          <table class="w-full min-w-[640px] border-collapse text-p-sm">
            <thead>
              <tr class="bg-surface-gray-2 text-left text-p-xs text-ink-gray-6">
                <th class="px-3 py-2 font-medium">{{ t.card.colWork }}</th>
                <th class="px-3 py-2 font-medium">{{ t.card.colStage }}</th>
                <th class="px-3 py-2 font-medium">{{ t.card.colAssignee }}</th>
                <th class="px-3 py-2 font-medium">{{ t.card.end }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="work in shownWorks" :key="work.name" class="border-b border-outline-gray-1">
                <td class="px-3 py-2">
                  <RouterLink :to="taskLink(work.name)" class="font-medium text-ink-gray-8 hover:underline">{{ work.subject }}</RouterLink>
                  <span v-if="work.is_milestone" class="ml-1.5 rounded-3 bg-surface-blue-2 px-1.5 text-p-xs text-ink-blue-6">{{ t.card.milestone }}</span>
                  <span v-if="work.block_reason" class="block text-p-xs text-ink-amber-7">{{ work.block_reason }}</span>
                </td>
                <td class="px-3 py-2 text-ink-gray-7">{{ workStatus(work) }}</td>
                <td class="px-3 py-2 text-ink-gray-7">{{ people(work) }}</td>
                <td class="whitespace-nowrap px-3 py-2" :class="dueClass(work)">{{ date(work.end) }}</td>
              </tr>
            </tbody>
          </table>
        </OverlayScroll>
        <p v-if="card.works_truncated" class="text-p-sm text-ink-amber-7">{{ t.card.worksTruncated }}</p>
      </template>

      <!-- Details -->
      <template v-else-if="section === 'details'">
        <dl class="grid gap-3 sm:grid-cols-2">
          <div class="rounded-6 border border-outline-gray-2 p-3">
            <dt class="text-p-xs text-ink-gray-5">{{ t.card.customer }}</dt>
            <dd class="text-p-sm text-ink-gray-8">{{ p.customer || t.noData }}</dd>
          </div>
          <div class="rounded-6 border border-outline-gray-2 p-3">
            <dt class="text-p-xs text-ink-gray-5">{{ t.card.start }} — {{ t.card.end }}</dt>
            <dd class="text-p-sm text-ink-gray-8">{{ date(p.expected_start) }} — {{ date(p.expected_end) }}</dd>
          </div>
          <div class="rounded-6 border border-outline-gray-2 p-3">
            <dt class="text-p-xs text-ink-gray-5">{{ t.card.team }}</dt>
            <dd class="text-p-sm text-ink-gray-8">
              {{ p.team.length ? p.team.map((m) => m.full_name || m.name).join(', ') : t.card.noTeam }}
            </dd>
          </div>
          <div class="rounded-6 border border-outline-gray-2 p-3">
            <dt class="text-p-xs text-ink-gray-5">{{ t.card.handover }}</dt>
            <dd class="text-p-sm text-ink-gray-8">
              <a v-if="p.handover" :href="deskUrl('AV Handover', p.handover.name)" class="hover:underline">{{ p.handover.name }}</a>
              <template v-else>{{ card.money_visible ? t.noData : t.hidden }}</template>
            </dd>
          </div>
          <div class="rounded-6 border border-outline-gray-2 p-3">
            <dt class="text-p-xs text-ink-gray-5">{{ t.card.projectStatus }}</dt>
            <dd class="text-p-sm text-ink-gray-8">{{ p.project_status }}</dd>
          </div>
        </dl>
        <a :href="deskUrl('Project', p.name)" class="inline-block text-p-sm text-ink-blue-link hover:underline">{{ t.card.openDesk }}</a>
      </template>

      <!-- Files -->
      <template v-else-if="section === 'files'">
        <p v-if="!card.files.length" class="rounded-6 border border-dashed border-outline-gray-3 p-6 text-center text-p-sm text-ink-gray-6">{{ t.card.noFiles }}</p>
        <ul v-else class="divide-y divide-outline-gray-1 rounded-6 border border-outline-gray-2">
          <li v-for="file in card.files" :key="file.name" class="flex flex-wrap items-baseline justify-between gap-2 px-3 py-2 text-p-sm">
            <a :href="file.file_url" target="_blank" rel="noopener" class="text-ink-gray-8 hover:underline">{{ file.file_name || file.file_url }}</a>
            <span class="text-p-xs text-ink-gray-5">
              <template v-if="file.is_private">{{ t.card.private }} · </template>{{ date(file.creation) }}
            </span>
          </li>
        </ul>
      </template>

      <template #aside>
        <section>
          <h2 class="mb-1.5 text-p-sm font-semibold text-ink-gray-9">{{ t.card.myWorks }}</h2>
          <p v-if="!card.my_works.length" class="text-ink-gray-5">{{ t.card.noMyWorks }}</p>
          <ul v-else class="space-y-1.5">
            <li v-for="work in card.my_works.slice(0, 6)" :key="work.name">
              <RouterLink :to="taskLink(work.name)" class="text-ink-gray-8 hover:underline">{{ work.subject }}</RouterLink>
              <span class="block text-p-xs" :class="dueClass(work)">{{ t.card.due }} {{ date(work.end) }}</span>
            </li>
          </ul>
        </section>
        <section>
          <h2 class="mb-1.5 text-p-sm font-semibold text-ink-gray-9">{{ t.card.milestones }}</h2>
          <p v-if="!card.milestones.length" class="text-ink-gray-5">{{ t.projects.noMilestone }}</p>
          <p v-else class="text-ink-gray-8">
            {{ card.milestones[0].subject }}
            <span class="block text-p-xs" :class="dueClass(card.milestones[0])">{{ date(card.milestones[0].end) }}</span>
          </p>
        </section>
        <section>
          <h2 class="mb-1.5 text-p-sm font-semibold text-ink-gray-9">{{ t.card.files }}</h2>
          <p v-if="!card.files.length" class="text-ink-gray-5">{{ t.card.noFiles }}</p>
          <ul v-else class="space-y-1">
            <li v-for="file in card.files.slice(0, 4)" :key="file.name" class="truncate">
              <a :href="file.file_url" target="_blank" rel="noopener" class="text-ink-gray-8 hover:underline">{{ file.file_name || file.file_url }}</a>
            </li>
          </ul>
        </section>
      </template>
    </RecordShell>

    <TaskPanel v-if="openTask" :key="openTask" :name="openTask" @close="closePanel" @updated="data.reload()" />
  </div>
</template>
