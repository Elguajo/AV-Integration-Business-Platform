<script setup lang="ts">
import { computed } from 'vue'
import { quotationHeadline, type QuotationRow } from '../api'
import { date, money } from '../format'

const props = defineProps<{ row: QuotationRow; selected: boolean }>()
defineEmits<{ select: [] }>()

const headline = computed(() => quotationHeadline(props.row))
</script>

<template>
  <button
    type="button"
    class="w-full rounded-6 border bg-surface-elevation-1 p-3 text-left transition-colors hover:border-outline-gray-3"
    :class="selected ? 'border-outline-gray-4 shadow-sm' : 'border-outline-gray-1'"
    :aria-pressed="selected"
    @click="$emit('select')"
  >
    <div class="truncate text-base-medium text-ink-gray-9" :title="headline.main">
      {{ headline.main }}
    </div>
    <div v-if="headline.sub" class="mt-0.5 truncate text-sm text-ink-gray-6" :title="headline.sub">
      {{ headline.sub }}
    </div>
    <div class="mt-1.5 flex items-center gap-1.5 text-sm font-medium text-ink-gray-7">
      <span class="lucide-file-text size-3.5 shrink-0" aria-hidden="true" />
      <span class="truncate tabular-nums">{{ row.name }}</span>
    </div>
    <div class="mt-2 flex items-center justify-between gap-2">
      <span class="text-base-semibold tabular-nums text-ink-gray-8">
        {{ money(row.grand_total, row.currency) }}
      </span>
      <span class="text-sm text-ink-gray-5">{{ date(row.transaction_date) }}</span>
    </div>
    <div
      v-if="row.handover?.review_status === 'Returned' && row.handover.review_note"
      class="mt-2 line-clamp-2 rounded-4 bg-surface-amber-2 px-2 py-1 text-p-xs text-ink-amber-7"
    >
      {{ row.handover.review_note }}
    </div>
  </button>
</template>
