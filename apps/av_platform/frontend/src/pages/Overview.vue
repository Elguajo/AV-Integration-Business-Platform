<script setup lang="ts">
// Home page (DIR-01, UI-03): the user's works, the funnel for the director, projects in execution.
// Layout follows research/12 §6.2: greeting and «Мои / Все» on top, works and funnel side by side,
// then the project table. The server decides every value.
import { computed, ref } from 'vue'
import { Button, ErrorMessage, Skeleton, useCall } from 'frappe-ui'
import { OVERVIEW_API, deskUrl, openShell, shellUrl, type Amount, type Overview } from '../overviewApi'
import type { DueBucket } from '../pmApi'
import { ruOverview as t } from '../i18n/overview'
import { date, money, UNKNOWN } from '../format'
import ProjectTable from '../components/ProjectTable.vue'

const HOME_ROWS = 8
const SHOWN_BUCKETS: DueBucket[] = ['overdue', 'today', 'week']
const BUCKET_STYLE: Record<DueBucket, string> = {
  overdue: 'bg-surface-red-2 text-ink-red-6',
  today: 'bg-surface-amber-2 text-ink-amber-7',
  week: 'bg-surface-gray-2 text-ink-gray-7',
  later: 'bg-surface-gray-2 text-ink-gray-7',
  no_date: 'bg-surface-gray-2 text-ink-gray-7',
}
const DOT: Record<DueBucket, string> = {
  overdue: 'bg-surface-red-5',
  today: 'bg-surface-amber-5',
  week: 'bg-surface-blue-5',
  later: 'bg-surface-gray-4',
  no_date: 'bg-surface-gray-4',
}

const data = useCall<Overview>({ url: OVERVIEW_API.overview })
const mine = ref(false)

const forbidden = computed(() => (data.error as { type?: string } | null)?.type === 'PermissionError')
const allRows = computed(() => data.data?.projects.rows ?? [])
const rows = computed(() => allRows.value.filter((r) => !mine.value || r.mine))
const firstName = computed(() => {
  const user = data.data?.user
  return (user?.full_name || user?.name || '').split(' ')[0]
})
const maxCount = computed(() => Math.max(1, ...(data.data?.funnel?.stages.map((s) => s.count) ?? [1])))

function amounts(totals: Amount[]) {
  return totals.length ? totals.map((a) => money(a.amount, a.currency)).join(' · ') : UNKNOWN
}
</script>

<template>
  <div class="h-full overflow-y-auto bg-surface-gray-1 text-ink-gray-8">
    <div class="mx-auto max-w-7xl space-y-4 px-3 pb-10 pt-4 sm:px-5">
      <div v-if="data.error" class="mx-auto max-w-xl pt-6">
        <p class="text-lg-semibold text-ink-gray-8">{{ t.error }}</p>
        <p v-if="forbidden" class="mt-2 text-p-base text-ink-gray-6">{{ t.forbidden }}</p>
        <ErrorMessage v-else class="mt-2" :message="data.error" />
      </div>

      <div v-else-if="data.loading && !data.data" class="space-y-3">
        <Skeleton class="h-10 w-72 rounded-4" />
        <div class="grid gap-3 lg:grid-cols-2">
          <Skeleton class="h-48 rounded-6" />
          <Skeleton class="h-48 rounded-6" />
        </div>
        <Skeleton class="h-64 w-full rounded-6" />
      </div>

      <template v-else-if="data.data">
        <div class="flex flex-wrap items-center gap-3">
          <h1 class="text-xl font-semibold text-ink-gray-9">{{ t.greeting(firstName) }}</h1>
          <span class="text-p-sm text-ink-gray-5">{{ t.todayIs }} {{ date(data.data.today) }}</span>
          <span class="grow" />
          <div class="inline-flex rounded-4 bg-surface-gray-3 p-0.5 text-p-sm" role="group" :aria-label="t.scope.label">
            <button
              v-for="option in [false, true]"
              :key="String(option)"
              type="button"
              class="rounded-3 px-3 py-1"
              :class="mine === option ? 'bg-surface-base font-medium text-ink-gray-9 shadow-sm' : 'text-ink-gray-6'"
              :aria-pressed="mine === option"
              @click="mine = option"
            >
              {{ option ? t.scope.mine : t.scope.all }}
            </button>
          </div>
          <Button icon="lucide-refresh-cw" :tooltip="t.refresh" :aria-label="t.refresh" :loading="data.loading" @click="data.reload()" />
        </div>

        <div class="grid gap-4" :class="data.data.funnel ? 'xl:grid-cols-[minmax(0,1fr)_minmax(0,1.35fr)]' : ''">
          <section class="rounded-6 border border-outline-gray-2 bg-surface-base p-4" aria-labelledby="av-home-tasks">
            <div class="mb-3 flex items-center gap-2">
              <h2 id="av-home-tasks" class="text-base font-semibold text-ink-gray-9">{{ t.myTasks.title }}</h2>
              <span class="grow" />
              <a :href="shellUrl('my-tasks')" class="text-p-sm text-ink-blue-link hover:underline" @click="openShell($event, 'my-tasks')">
                {{ t.myTasks.all }}
              </a>
            </div>
            <p v-if="!data.data.my_tasks" class="text-p-sm text-ink-gray-5">{{ t.myTasks.none }}</p>
            <template v-else>
              <div class="mb-3 flex flex-wrap gap-1.5">
                <span
                  v-for="bucket in SHOWN_BUCKETS"
                  :key="bucket"
                  class="rounded-3 px-2 py-0.5 text-p-xs font-medium tabular-nums"
                  :class="BUCKET_STYLE[bucket]"
                >
                  {{ t.myTasks.buckets[bucket] }}: {{ data.data.my_tasks.counts[bucket] }}
                </span>
              </div>
              <p v-if="!data.data.my_tasks.items.length" class="text-p-sm text-ink-gray-5">{{ t.myTasks.empty }}</p>
              <ul v-else class="divide-y divide-outline-gray-1">
                <li v-for="task in data.data.my_tasks.items" :key="task.name" class="flex items-start gap-2 py-2">
                  <span class="mt-1.5 size-2 shrink-0 rounded-full" :class="DOT[task.bucket]" aria-hidden="true" />
                  <div class="min-w-0">
                    <a :href="deskUrl('Task', task.name)" class="text-p-sm font-medium text-ink-gray-8 hover:underline">{{ task.subject }}</a>
                    <p class="text-p-xs text-ink-gray-5">
                      <a
                        v-if="task.project"
                        :href="shellUrl('projects', task.project)"
                        class="hover:underline"
                        @click="openShell($event, 'projects', task.project)"
                      >{{ task.project_name || task.project }}</a>
                      · {{ t.myTasks.buckets[task.bucket] }} · {{ date(task.end) }}
                    </p>
                    <p v-if="task.block_reason" class="text-p-xs text-ink-amber-7">{{ task.block_reason }}</p>
                  </div>
                </li>
              </ul>
            </template>
          </section>

          <section v-if="data.data.funnel" class="rounded-6 border border-outline-gray-2 bg-surface-base p-4" aria-labelledby="av-home-funnel">
            <div class="mb-1 flex flex-wrap items-baseline gap-2">
              <h2 id="av-home-funnel" class="text-base font-semibold text-ink-gray-9">{{ t.funnel.title }}</h2>
              <span class="text-p-xs text-ink-gray-5">{{ t.funnel.hint }}</span>
            </div>
            <div class="mt-3 grid h-36 grid-cols-5 items-end gap-2">
              <div v-for="stage in data.data.funnel.stages" :key="stage.stage" class="flex h-full min-w-0 flex-col items-center justify-end gap-1 text-center">
                <span class="text-p-xs font-medium tabular-nums text-ink-gray-8">{{ stage.count }}</span>
                <span
                  class="w-full rounded-t-[5px] bg-surface-blue-5"
                  :style="{ height: `${Math.max(4, (stage.count / maxCount) * 88)}px` }"
                  aria-hidden="true"
                />
                <span class="w-full truncate text-[11px] text-ink-gray-6" :title="t.funnel.stages[stage.stage]">{{ t.funnel.stages[stage.stage] }}</span>
              </div>
            </div>
            <p class="mt-3 text-p-sm text-ink-gray-7">
              <span class="font-medium">{{ t.funnel.open }}:</span>
              <span class="tabular-nums"> {{ amounts(data.data.funnel.open_totals) }}</span>
            </p>
            <ul v-if="data.data.funnel.attention.length" class="mt-2 divide-y divide-outline-gray-1 border-t border-outline-gray-1">
              <li v-for="deal in data.data.funnel.attention.slice(0, 4)" :key="deal.name" class="flex flex-wrap items-baseline justify-between gap-x-3 py-1.5 text-p-sm">
                <a :href="deskUrl('Quotation', deal.name)" class="min-w-0 truncate text-ink-gray-8 hover:underline">{{ deal.customer || deal.name }}</a>
                <span :class="deal.alert === 'expired' ? 'font-medium text-ink-red-6' : 'text-ink-amber-7'">
                  {{ deal.alert ? t.funnel.alerts[deal.alert] : t.funnel.returned }}
                  <template v-if="deal.alert"> · {{ date(deal.valid_till) }}</template>
                </span>
              </li>
            </ul>
            <p v-else class="mt-2 text-p-xs text-ink-gray-5">{{ t.funnel.attentionEmpty }}</p>
          </section>
        </div>

        <section class="rounded-6 border border-outline-gray-2 bg-surface-base" aria-labelledby="av-home-projects">
          <div class="flex flex-wrap items-center gap-2 px-4 pb-2 pt-3">
            <h2 id="av-home-projects" class="text-base font-semibold text-ink-gray-9">{{ t.homeProjects.title }}</h2>
            <span class="text-p-sm text-ink-gray-5">{{ t.homeProjects.count(Math.min(rows.length, HOME_ROWS), rows.length) }}</span>
            <span class="grow" />
            <a :href="shellUrl('projects')" class="text-p-sm text-ink-blue-link hover:underline" @click="openShell($event, 'projects')">
              {{ t.homeProjects.all }}
            </a>
          </div>
          <p v-if="!allRows.length" class="px-4 pb-6 pt-2 text-p-sm text-ink-gray-5">{{ t.projects.empty }}</p>
          <p v-else-if="!rows.length" class="px-4 pb-6 pt-2 text-p-sm text-ink-gray-5">{{ t.homeProjects.emptyMine }}</p>
          <ProjectTable v-else :rows="rows.slice(0, HOME_ROWS)" :money-visible="data.data.money_visible" compact />
          <p class="px-4 py-2 text-p-xs text-ink-gray-5">{{ t.register.directionsHint }}</p>
        </section>
      </template>
    </div>
  </div>
</template>
