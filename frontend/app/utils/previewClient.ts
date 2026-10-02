import type { DeviceKey, JobResponse, JobStatus } from '~/types/preview'

export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>

const SERVICE_UNAVAILABLE = 'The preview service is unavailable right now. Please try again.'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function isTerminal(status: JobStatus): boolean {
  return status === 'completed' || status === 'failed'
}

async function errorFromResponse(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as { detail?: unknown }
    if (typeof body.detail === 'string' && body.detail) {
      return new ApiError(response.status, body.detail)
    }
  } catch {
    // Body was not JSON; fall through to the generic message.
  }
  return new ApiError(response.status, SERVICE_UNAVAILABLE)
}

export interface PreviewClient {
  start(url: string): Promise<JobResponse>
  getJob(jobId: string): Promise<JobResponse>
  imageUrl(path: string): string
  downloadUrl(jobId: string, device: DeviceKey): string
}

export function createPreviewClient(apiBase: string, fetchImpl: FetchLike): PreviewClient {
  const base = apiBase.replace(/\/+$/, '')

  async function request(path: string, init?: RequestInit): Promise<JobResponse> {
    const response = await fetchImpl(`${base}${path}`, init)
    if (!response.ok) throw await errorFromResponse(response)
    return (await response.json()) as JobResponse
  }

  return {
    start(url) {
      return request('/api/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      })
    },
    getJob(jobId) {
      return request(`/api/preview/${jobId}`)
    },
    imageUrl(path) {
      return `${base}${path.startsWith('/') ? path : `/${path}`}`
    },
    downloadUrl(jobId, device) {
      return `${base}/api/preview/${jobId}/download/${device}`
    },
  }
}
