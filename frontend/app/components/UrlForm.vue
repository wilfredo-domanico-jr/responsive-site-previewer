<script setup lang="ts">
const props = defineProps<{
  busy: boolean
}>()

const emit = defineEmits<{
  submit: [url: string]
}>()

const url = ref('')
const localError = ref<string | null>(null)

function looksLikeUrl(value: string): boolean {
  // Only catch input that is clearly not an address. Scheme and host rules are
  // enforced by the backend, whose messages are more specific.
  if (/\s/.test(value)) return false
  const candidate = /^[a-z][a-z0-9+.-]*:/i.test(value) ? value : `https://${value}`
  try {
    return new URL(candidate).hostname.length > 0 || /^[a-z][a-z0-9+.-]*:/i.test(value)
  } catch {
    return false
  }
}

function onSubmit() {
  const value = url.value.trim()
  if (!value) {
    localError.value = 'Enter a website address to preview.'
    return
  }
  if (!looksLikeUrl(value)) {
    localError.value = 'That does not look like a website address. Try something like https://example.com.'
    return
  }
  localError.value = null
  emit('submit', value)
}

watch(url, () => {
  if (localError.value) localError.value = null
})

defineExpose({ setUrl: (value: string) => (url.value = value) })
</script>

<template>
  <form class="w-full" novalidate @submit.prevent="onSubmit">
    <label for="site-url" class="block text-sm font-medium text-ink-2 mb-2">Website address</label>

    <div
      class="flex items-stretch rounded-2xl bg-surface shadow-card ring-1 transition-shadow"
      :class="localError ? 'ring-danger' : 'ring-line focus-within:ring-2 focus-within:ring-accent'"
    >
      <span class="hidden sm:flex items-center pl-4 text-ink-3" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" class="size-5">
          <circle cx="12" cy="12" r="9" />
          <path d="M3.5 12h17M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
        </svg>
      </span>
      <input
        id="site-url"
        v-model="url"
        type="url"
        inputmode="url"
        autocomplete="url"
        spellcheck="false"
        placeholder="https://example.com"
        :disabled="props.busy"
        :aria-invalid="localError ? 'true' : undefined"
        :aria-describedby="localError ? 'site-url-error' : undefined"
        class="min-w-0 flex-1 bg-transparent px-4 py-4 text-base sm:text-lg text-ink placeholder:text-ink-3 outline-none disabled:opacity-60"
      >
      <div class="flex items-center p-2">
        <button
          type="submit"
          :disabled="props.busy"
          class="inline-flex h-full items-center gap-2 rounded-xl bg-accent px-4 sm:px-5 text-sm sm:text-base font-semibold text-accent-ink transition-colors hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <svg
            v-if="props.busy"
            class="size-4 animate-spin"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            aria-hidden="true"
          >
            <path d="M12 3a9 9 0 1 0 9 9" stroke-linecap="round" />
          </svg>
          <span>{{ props.busy ? 'Generating' : 'Generate preview' }}</span>
        </button>
      </div>
    </div>

    <p v-if="localError" id="site-url-error" class="mt-2 text-sm text-danger" role="alert">
      {{ localError }}
    </p>
    <p v-else class="mt-2 text-sm text-ink-3">
      Any public website works. Previews are captured at four sizes, from 1920 px wide down to 390 px.
    </p>
  </form>
</template>
