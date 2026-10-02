<script setup lang="ts">
import type { DeviceKey } from '~/types/preview'

defineProps<{ device: DeviceKey }>()
</script>

<template>
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.6"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    class="size-[1em] shrink-0"
  >
    <template v-if="device === 'desktop'">
      <rect x="2.5" y="4" width="19" height="12" rx="1.5" />
      <path d="M9 20h6M12 16v4" />
    </template>
    <template v-else-if="device === 'laptop'">
      <rect x="4" y="5" width="16" height="10.5" rx="1.5" />
      <path d="M2 18.5h20" />
    </template>
    <template v-else-if="device === 'tablet'">
      <rect x="5" y="2.5" width="14" height="19" rx="2" />
      <path d="M11 18.5h2" />
    </template>
    <template v-else>
      <rect x="7" y="2.5" width="10" height="19" rx="2.2" />
      <path d="M10.5 5h3" />
    </template>
  </svg>
</template>
