<script setup lang="ts">
// The one scroll container of the role screens: the bar floats over the content and fades when
// idle, so content never shifts when a scrollbar appears (native overlay scrollbars are gone from
// Chrome since 114). frappe-ui ScrollArea wraps the slot in its own div, so the layout classes go
// on contentClass, and the wrapper is stretched here:
// - vertical: the content fills at least the full height (sticky footers, side panels);
// - horizontal: the content is as tall as the area (board columns);
// - horizontal and both: the wrapper keeps the area width, so `w-full` tables wrap text before
//   they scroll; rows of fixed-width columns take `w-max` to keep their end padding.
import { computed } from 'vue'
import { ScrollArea } from 'frappe-ui'

const props = withDefaults(
  defineProps<{ orientation?: 'vertical' | 'horizontal' | 'both'; contentClass?: unknown }>(),
  { orientation: 'vertical', contentClass: undefined },
)

const wrapper = computed(() =>
  props.orientation === 'vertical'
    ? '[&>div]:flex [&>div]:min-h-full [&>div]:flex-col'
    : props.orientation === 'horizontal'
      ? '[&>div]:h-full [&>div]:!min-w-0'
      : '[&>div]:!min-w-0',
)
const inner = computed(() =>
  props.orientation === 'vertical' ? 'min-w-0 flex-1' : props.orientation === 'horizontal' ? 'h-full' : '',
)
</script>

<template>
  <ScrollArea :orientation="orientation" :viewport-class="wrapper">
    <div :class="[inner, contentClass]">
      <slot />
    </div>
  </ScrollArea>
</template>
