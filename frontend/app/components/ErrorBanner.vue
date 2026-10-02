<script setup lang="ts">
defineProps<{ message: string }>()
defineEmits<{ dismiss: [] }>()
</script>

<template>
  <div
    role="alert"
    class="fade-in flex items-start gap-3 rounded-2xl bg-danger-soft px-4 py-3 text-sm text-ink ring-1 ring-danger/30"
  >
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="mt-0.5 size-5 shrink-0 text-danger" aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v5M12 16.5v.5" stroke-linecap="round" />
    </svg>
    <div class="flex-1">
      <p class="font-medium">Preview could not be generated</p>
      <p class="mt-0.5 text-ink-2">{{ message }}</p>
    </div>
    <button
      type="button"
      class="rounded-lg px-2 py-1 text-ink-2 hover:bg-surface hover:text-ink"
      aria-label="Dismiss"
      @click="$emit('dismiss')"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="size-4" aria-hidden="true">
        <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" />
      </svg>
    </button>
  </div>
</template>
