import { computed, onScopeDispose, ref, shallowRef } from 'vue'
import type { JobResponse } from '~/types/preview'
import { ApiError, isTerminal } from '~/utils/previewClient'

const POLL_INTERVAL_MS = 750
const NETWORK_ERROR = 'Could not reach the preview service. Make sure the backend is running and try again.'

/**
 * Starts a preview job and polls it until it completes or fails.
 * Progress (`job.step`, `job.previews`) comes straight from the backend.
 */
export function usePreviewJob() {
  const client = usePreviewClient()

  const job = shallowRef<JobResponse | null>(null)
  const error = ref<string | null>(null)
  const isSubmitting = ref(false)

  let timer: ReturnType<typeof setTimeout> | null = null
  let activeJobId: string | null = null

  const isRunning = computed(
    () => isSubmitting.value || (job.value !== null && !isTerminal(job.value.status)),
  )

  function stopPolling() {
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
    activeJobId = null
  }

  async function poll(jobId: string) {
    if (activeJobId !== jobId) return
    try {
      const next = await client.getJob(jobId)
      if (activeJobId !== jobId) return
      job.value = next
      if (next.status === 'failed') {
        error.value = next.error ?? 'Something went wrong while capturing the website. Please try again.'
      }
      if (isTerminal(next.status)) {
        stopPolling()
        return
      }
    } catch (err) {
      if (activeJobId !== jobId) return
      error.value = err instanceof ApiError ? err.message : NETWORK_ERROR
      stopPolling()
      return
    }
    timer = setTimeout(() => poll(jobId), POLL_INTERVAL_MS)
  }

  async function start(url: string) {
    stopPolling()
    error.value = null
    job.value = null
    isSubmitting.value = true
    try {
      const created = await client.start(url)
      job.value = created
      activeJobId = created.job_id
      timer = setTimeout(() => poll(created.job_id), POLL_INTERVAL_MS)
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : NETWORK_ERROR
    } finally {
      isSubmitting.value = false
    }
  }

  function reset() {
    stopPolling()
    job.value = null
    error.value = null
  }

  onScopeDispose(stopPolling)

  return { job, error, isRunning, start, reset, client }
}
