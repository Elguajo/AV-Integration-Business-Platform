<script setup lang="ts">
// Dense table of projects (UI-03, OVW-01): one row per project, the whole row opens the card.
import { type ProjectRow, openShell, shellUrl } from '../overviewApi'
import { ruOverview as t } from '../i18n/overview'
import { date, money } from '../format'
import StatusPill from './StatusPill.vue'
import PeopleStack from './PeopleStack.vue'
import DirectionMarks from './DirectionMarks.vue'

withDefaults(defineProps<{ rows: ProjectRow[]; moneyVisible: boolean; compact?: boolean }>(), {
  compact: false,
})

function basis(row: ProjectRow, visible: boolean) {
  if (!visible) return t.hidden
  return row.basis ? money(row.basis.amount, row.basis.currency) : t.noData
}

function obstacleOwner(row: ProjectRow) {
  const people = row.obstacle?.assignees ?? []
  return people.length ? people.map((p) => p.full_name || p.name).join(', ') : t.card.nobody
}
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full min-w-[820px] border-collapse text-p-sm">
      <thead>
        <tr class="bg-surface-gray-2 text-left text-p-xs text-ink-gray-6">
          <th class="px-3 py-2 font-medium">{{ t.table.project }}</th>
          <th class="px-3 py-2 font-medium">{{ t.table.customer }}</th>
          <th class="px-3 py-2 font-medium">{{ t.table.team }}</th>
          <th class="px-3 py-2 font-medium">{{ t.table.status }}</th>
          <th class="px-3 py-2 font-medium">{{ t.table.obstacle }}</th>
          <th class="px-3 py-2 font-medium">{{ t.table.directions }}</th>
          <th v-if="!compact" class="px-3 py-2 font-medium">{{ t.table.works }}</th>
          <th v-if="!compact" class="px-3 py-2 font-medium">{{ t.table.end }}</th>
          <th class="px-3 py-2 text-right font-medium">{{ t.table.basis }}</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in rows"
          :key="row.name"
          class="cursor-pointer border-b border-outline-gray-1 align-middle hover:bg-surface-gray-1"
          @click="openShell($event, 'projects', row.name)"
        >
          <td class="px-3 py-2">
            <a
              :href="shellUrl('projects', row.name)"
              class="font-medium text-ink-gray-9 hover:underline"
              @click.stop="openShell($event, 'projects', row.name)"
            >
              {{ row.project_name || row.name }}
            </a>
            <span class="block text-p-xs text-ink-gray-5">{{ row.name }}</span>
          </td>
          <td class="px-3 py-2 text-ink-gray-7">{{ row.customer || t.noData }}</td>
          <td class="px-3 py-2">
            <span class="block text-ink-gray-8">{{ row.pm?.full_name || row.pm?.name || t.noData }}</span>
            <PeopleStack v-if="row.team.length" :people="row.team" class="mt-1" />
          </td>
          <td class="px-3 py-2"><StatusPill :status="row.status" /></td>
          <td class="max-w-[260px] px-3 py-2">
            <template v-if="row.obstacle">
              <span class="block text-ink-gray-8">{{ row.obstacle.subject }}</span>
              <span class="block text-p-xs text-ink-gray-5">
                {{ row.obstacle.kind === 'blocked' ? t.card.blocked : t.card.overdue }} ·
                {{ obstacleOwner(row) }} · {{ t.card.due }} {{ date(row.obstacle.end) }}
              </span>
            </template>
            <span v-else-if="row.works.total === 0" class="text-ink-gray-5">{{ t.reasons.no_works() }}</span>
            <span v-else class="text-ink-gray-5">—</span>
          </td>
          <td class="px-3 py-2"><DirectionMarks :works="row.status" /></td>
          <td v-if="!compact" class="whitespace-nowrap px-3 py-2 tabular-nums text-ink-gray-7">
            {{ row.works.total ? t.card.worksDone(row.works.done, row.works.total) : t.noData }}
          </td>
          <td v-if="!compact" class="whitespace-nowrap px-3 py-2 text-ink-gray-7">
            {{ row.expected_end ? date(row.expected_end) : t.noData }}
          </td>
          <td class="whitespace-nowrap px-3 py-2 text-right tabular-nums text-ink-gray-8">{{ basis(row, moneyVisible) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
