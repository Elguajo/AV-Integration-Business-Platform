<script setup lang="ts">
// Project dashboard (UI-06): the overview section of the project card, composed after the D-Tools
// project dashboard (research/12 §6.2, DT5). Tiles exist only for directions that have data; the
// rest are named in one line as not tracked, never drawn as zero. Counts, no overall percentage
// (OVW-02). Every number comes from the server summary over all works (QUALITY-01).
import { computed } from 'vue'
import type { RouteLocationRaw } from 'vue-router'
import type { ProjectCardData, Work } from '../overviewApi'
import { deskUrl } from '../overviewApi'
import { ruOverview as t } from '../i18n/overview'
import { date, money } from '../format'
import ProgressRing from './ProgressRing.vue'
import StatusPill from './StatusPill.vue'

const props = defineProps<{ card: ProjectCardData; taskLink: (name: string) => RouteLocationRaw }>()
const emit = defineEmits<{ open: [section: string, stage?: string | null] }>()

const NO_STAGE = '__none__'
const UNTRACKED = ['procurement', 'install', 'tests', 'money'] as const
const OBSTACLES_SHOWN = 5
const UPCOMING_SHOWN = 5

const p = computed(() => props.card.project)
const dash = computed(() => props.card.dashboard)

// Stage colours follow the stage, not its count: the first stage is neutral, the working stages
// step through one blue ramp, a closing stage is green, works without a stage are light gray.
const stageColor = computed(() => {
  const stages = props.card.stages
  const working = stages.filter((s, i) => i > 0 && !s.is_closed)
  const ramp = ['--ink-blue-3', '--ink-blue-5', '--ink-blue-7']
  const colors = new Map<string, string>()
  stages.forEach((s, i) => {
    if (s.is_closed) colors.set(s.name, 'var(--ink-green-5)')
    else if (i === 0) colors.set(s.name, 'var(--ink-gray-4)')
    else {
      const step = working.length > 1 ? working.indexOf(s) / (working.length - 1) : 0.5
      colors.set(s.name, `var(${ramp[Math.round(step * (ramp.length - 1))]})`)
    }
  })
  return colors
})
const stageLabel = computed(() => new Map(props.card.stages.map((s) => [s.name, s.label])))
const worksTotal = computed(() => dash.value.by_stage.reduce((sum, row) => sum + row.count, 0))
const stageRows = computed(() =>
  dash.value.by_stage.map((row) => ({
    key: row.stage ?? NO_STAGE,
    label: row.stage ? (stageLabel.value.get(row.stage) ?? row.stage) : t.card.noStage,
    count: row.count,
    color: (row.stage && stageColor.value.get(row.stage)) || 'var(--surface-gray-4)',
  })),
)

const busy = computed(() => dash.value.people.filter((person) => person.open > 0).length)

// Timeline from the project dates and the dated milestones; today is marked when it falls inside.
function day(value: string) {
  return new Date(`${value.slice(0, 10)}T00:00:00`).getTime()
}
const timeline = computed(() => {
  const points = [p.value.expected_start, p.value.expected_end, ...dash.value.key_dates.map((w) => w.end)]
    .filter((v): v is string => !!v)
    .map(day)
  if (!points.length) return null
  const min = Math.min(...points)
  const max = Math.max(...points)
  const span = max - min
  const at = (value: string) => (span ? ((day(value) - min) / span) * 100 : 50)
  const today = day(props.card.today)
  return {
    from: p.value.expected_start ?? null,
    to: p.value.expected_end ?? null,
    today: span && today >= min && today <= max ? at(props.card.today) : null,
    marks: dash.value.key_dates.map((work) => ({ work, at: at(work.end as string), done: work.status === 'Completed' })),
  }
})
const upcoming = computed(() => dash.value.key_dates.filter((w) => w.status !== 'Completed').slice(0, UPCOMING_SHOWN))

function dueClass(work: Work) {
  if (work.due === 'overdue') return 'font-medium text-ink-red-6'
  if (work.due === 'today' || work.due === 'soon') return 'text-ink-amber-7'
  return 'text-ink-gray-5'
}

function people(work: Work) {
  return work.assignees.length ? work.assignees.map((a) => a.full_name || a.name).join(', ') : t.card.nobody
}

function initials(name: string) {
  return name
    .split(/[\s@.]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join('')
}
</script>

<template>
  <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-12">
    <!-- Contract: the accepted basis from the handover, visible only to roles that may read money. -->
    <section class="tile xl:col-span-4">
      <header class="tile-head">
        <h2>{{ t.dash.contract }}</h2>
        <button type="button" class="tile-link" @click="emit('open', 'details')">{{ t.dash.details }}</button>
      </header>
      <template v-if="!card.money_visible">
        <p class="text-p-sm text-ink-gray-5">{{ t.dash.moneyHidden }}</p>
      </template>
      <template v-else-if="p.basis">
        <p class="py-3 text-center text-3xl font-semibold tabular-nums text-ink-gray-9">{{ money(p.basis.amount, p.basis.currency) }}</p>
        <dl class="space-y-1 text-p-sm">
          <div class="flex justify-between gap-3">
            <dt class="text-ink-gray-6">{{ t.dash.basisQuotation }}</dt>
            <dd><a :href="deskUrl('Quotation', p.basis.quotation)" class="text-ink-gray-8 hover:underline">{{ p.basis.quotation }}</a></dd>
          </div>
          <div class="flex justify-between gap-3">
            <dt class="text-ink-gray-6">{{ t.dash.acceptedByPm }}</dt>
            <dd class="text-ink-gray-8">{{ date(p.handover?.reviewed_on) }}</dd>
          </div>
        </dl>
        <p class="mt-3 text-p-xs text-ink-gray-5">{{ t.dash.noChanges }}</p>
      </template>
      <p v-else class="text-p-sm text-ink-gray-5">{{ t.card.noBasis }}</p>
    </section>

    <!-- Progress: counts of works, milestones and people; then the project timeline with key dates. -->
    <section class="tile md:col-span-2 xl:col-span-8">
      <header class="tile-head">
        <h2>{{ t.dash.progress }}</h2>
        <button type="button" class="tile-link" @click="emit('open', 'works')">{{ t.dash.allWorks }}</button>
      </header>
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <ProgressRing :done="p.works.done" :total="p.works.total" :label="t.dash.worksDone" :empty="t.dash.noWorks" />
        <ProgressRing :done="dash.milestones.done" :total="dash.milestones.total" :label="t.dash.milestonesDone" :empty="t.dash.noMilestones" />
        <ProgressRing :done="busy" :total="dash.people.length" :label="t.dash.peopleBusy" :empty="t.card.noTeam" />
      </div>

      <div class="mt-4 border-t border-outline-gray-1 pt-3">
        <p v-if="!timeline" class="text-p-sm text-ink-gray-5">{{ t.dash.noDates }}</p>
        <template v-else>
          <div class="flex justify-between text-p-xs tabular-nums text-ink-gray-5">
            <span>{{ t.card.start }} {{ date(timeline.from) }}</span>
            <span>{{ t.card.end }} {{ date(timeline.to) }}</span>
          </div>
          <div class="relative mx-1.5 mb-1 mt-3 h-1.5 rounded-full bg-surface-gray-3">
            <span
              v-if="timeline.today !== null"
              class="absolute -top-2 h-[22px] w-0.5 -translate-x-1/2 rounded-full"
              :style="{ left: `${timeline.today}%`, background: 'var(--ink-red-5)' }"
              :title="t.dash.today"
            />
            <RouterLink
              v-for="mark in timeline.marks"
              :key="mark.work.name"
              :to="taskLink(mark.work.name)"
              class="absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-surface-white"
              :style="{ left: `${mark.at}%`, background: mark.done ? 'var(--ink-green-5)' : 'var(--ink-blue-5)' }"
              :title="`${mark.work.subject} · ${date(mark.work.end)}${mark.done ? ' · ' + t.dash.passed : ''}`"
              :aria-label="`${mark.work.subject}, ${date(mark.work.end)}`"
            />
          </div>
        </template>
        <ul v-if="upcoming.length" class="mt-3 divide-y divide-outline-gray-1">
          <li v-for="work in upcoming" :key="work.name" class="flex flex-wrap items-baseline justify-between gap-2 py-1.5 text-p-sm">
            <RouterLink :to="taskLink(work.name)" class="text-ink-gray-8 hover:underline">{{ work.subject }}</RouterLink>
            <span :class="dueClass(work)">{{ date(work.end) }}</span>
          </li>
        </ul>
        <p v-else-if="dash.milestones.total" class="mt-3 text-p-sm text-ink-gray-5">{{ t.dash.noUpcoming }}</p>
        <p v-if="dash.undated_milestones" class="mt-2 text-p-xs text-ink-amber-7">{{ t.dash.undated(dash.undated_milestones) }}</p>
        <p v-if="dash.key_dates_truncated" class="mt-2 text-p-xs text-ink-gray-5">{{ t.dash.keyDatesTruncated }}</p>
      </div>
    </section>

    <!-- Works by stage: one segmented bar with a legend; a legend row opens the works of that stage. -->
    <section class="tile xl:col-span-4">
      <header class="tile-head">
        <h2>{{ t.dash.byStage }}</h2>
        <span class="text-p-sm tabular-nums text-ink-gray-5">{{ worksTotal }}</span>
      </header>
      <p v-if="!worksTotal" class="text-p-sm text-ink-gray-5">{{ t.card.noWorks }}</p>
      <template v-else>
        <div class="flex h-3 gap-0.5 overflow-hidden rounded-full" role="img" :aria-label="stageRows.map((r) => `${r.label}: ${r.count}`).join(', ')">
          <span
            v-for="row in stageRows"
            :key="row.key"
            class="h-full first:rounded-l-full last:rounded-r-full"
            :style="{ flexGrow: row.count, background: row.color }"
            :title="`${row.label}: ${row.count}`"
          />
        </div>
        <ul class="mt-3 space-y-0.5">
          <li v-for="row in stageRows" :key="row.key">
            <button
              type="button"
              class="flex w-full items-center gap-2 rounded-4 px-1.5 py-1 text-left text-p-sm hover:bg-surface-gray-2"
              @click="emit('open', 'works', row.key)"
            >
              <span class="size-2.5 shrink-0 rounded-full" :style="{ background: row.color }" aria-hidden="true" />
              <span class="flex-1 text-ink-gray-8">{{ row.label }}</span>
              <span class="tabular-nums text-ink-gray-6">{{ row.count }}</span>
            </button>
          </li>
        </ul>
      </template>
    </section>

    <!-- State: the project status with every reason, then the obstacles. -->
    <section class="tile xl:col-span-4">
      <header class="tile-head">
        <h2>{{ t.card.obstacles }}</h2>
        <StatusPill :status="p.status" />
      </header>
      <ul class="mb-2 flex flex-wrap gap-1.5">
        <li v-for="reason in p.reasons" :key="reason.code" class="rounded-3 bg-surface-gray-2 px-2 py-0.5 text-p-xs text-ink-gray-7">
          {{ t.reasons[reason.code](reason.count) }}
        </li>
      </ul>
      <p v-if="!card.obstacles.length" class="text-p-sm text-ink-gray-5">{{ t.card.noObstacles }}</p>
      <ul v-else class="divide-y divide-outline-gray-1">
        <li v-for="work in card.obstacles.slice(0, OBSTACLES_SHOWN)" :key="work.name" class="flex gap-2 py-1.5">
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
      <p v-if="card.obstacles.length > OBSTACLES_SHOWN" class="mt-1 text-p-xs text-ink-gray-5">
        {{ t.dash.moreObstacles(card.obstacles.length - OBSTACLES_SHOWN) }}
      </p>
    </section>

    <!-- People: who holds how many open works; people without works are visible, as in D-Tools. -->
    <section class="tile xl:col-span-4">
      <header class="tile-head">
        <h2>{{ t.dash.people }}</h2>
        <span class="text-p-sm tabular-nums text-ink-gray-5">{{ dash.people.length }}</span>
      </header>
      <p v-if="!dash.people.length" class="text-p-sm text-ink-gray-5">{{ t.card.noTeam }}</p>
      <ul v-else class="space-y-1.5">
        <li v-for="person in dash.people" :key="person.name" class="flex items-center gap-2 text-p-sm">
          <span class="inline-grid size-6 shrink-0 place-items-center rounded-full bg-surface-blue-2 text-[10px] font-semibold text-ink-blue-6" aria-hidden="true">
            {{ initials(person.full_name || person.name) }}
          </span>
          <span class="min-w-0 flex-1 truncate text-ink-gray-8" :title="person.name">
            {{ person.full_name || person.name }}
            <span v-if="!person.member" class="text-p-xs text-ink-gray-5">· {{ t.dash.notMember }}</span>
          </span>
          <span v-if="person.open" class="tabular-nums text-ink-gray-6">{{ t.dash.openWorks(person.open) }}</span>
          <span v-else class="text-p-xs text-ink-amber-7">{{ t.dash.noOpenWorks }}</span>
        </li>
      </ul>
    </section>

    <p class="text-p-sm text-ink-gray-5 md:col-span-2 xl:col-span-12">{{ t.card.untracked(UNTRACKED.map((key) => t.directions[key])) }}</p>
  </div>
</template>

<style scoped>
.tile {
  @apply min-w-0 rounded-6 border border-outline-gray-2 bg-surface-base p-4;
}
.tile-head {
  @apply mb-3 flex items-center justify-between gap-2;
}
.tile-head h2 {
  @apply text-p-base font-semibold text-ink-gray-9;
}
.tile-link {
  @apply rounded-3 text-p-sm text-ink-blue-link hover:underline;
}
</style>
