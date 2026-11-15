<script setup lang="ts">
import { landingPath } from '../boot'
import { ruShell as t } from '../i18n/shell'
</script>

<template>
  <div class="mx-auto max-w-xl px-5 pt-10">
    <p class="text-lg font-semibold text-ink-gray-8">{{ t.notFound }}</p>
    <RouterLink :to="landingPath()" class="mt-3 inline-block text-p-base text-ink-blue-link hover:underline">
      {{ t.toStart }}
    </RouterLink>
  </div>
</template>
