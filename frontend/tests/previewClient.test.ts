import { describe, expect, it, vi } from 'vitest'
import { ApiError, createPreviewClient, isTerminal } from '../app/utils/previewClient'
import type { JobResponse } from '../app/types/preview'

function job(overrides: Partial<JobResponse> = {}): JobResponse {
  return {
    job_id: 'abc123def456',
    url: 'https://example.com',
    status: 'queued',
    step: 'Queued...',
    error: null,
    previews: {},
    created_at: '2026-10-02T00:00:00Z',
    ...overrides,
  }
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

describe('createPreviewClient', () => {
  it('posts the url to /api/preview and returns the job', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(job(), 202))
    const client = createPreviewClient('http://api.test', fetchImpl)

    const result = await client.start('https://example.com')

    expect(fetchImpl).toHaveBeenCalledWith('http://api.test/api/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: 'https://example.com' }),
    })
    expect(result.job_id).toBe('abc123def456')
  })

  it('throws an ApiError carrying the backend detail on 400', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({ detail: 'Only http:// and https:// URLs are supported.' }, 400))
    const client = createPreviewClient('http://api.test', fetchImpl)

    await expect(client.start('ftp://x')).rejects.toMatchObject({
      name: 'ApiError',
      status: 400,
      message: 'Only http:// and https:// URLs are supported.',
    })
  })

  it('falls back to a generic message when the error body is not JSON', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response('<html>502</html>', { status: 502 }))
    const client = createPreviewClient('http://api.test', fetchImpl)

    await expect(client.start('https://example.com')).rejects.toBeInstanceOf(ApiError)
    await expect(client.start('https://example.com')).rejects.toMatchObject({
      message: 'The preview service is unavailable right now. Please try again.',
    })
  })

  it('fetches a job by id', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(job({ status: 'running', step: 'Capturing tablet...' })))
    const client = createPreviewClient('http://api.test/', fetchImpl)

    const result = await client.getJob('abc123def456')

    expect(fetchImpl).toHaveBeenCalledWith('http://api.test/api/preview/abc123def456', undefined)
    expect(result.step).toBe('Capturing tablet...')
  })

  it('builds absolute image and download urls', () => {
    const client = createPreviewClient('http://api.test/', vi.fn())
    expect(client.imageUrl('/screenshots/abc/desktop.png')).toBe('http://api.test/screenshots/abc/desktop.png')
    expect(client.downloadUrl('abc123def456', 'mobile')).toBe('http://api.test/api/preview/abc123def456/download/mobile')
  })
})

describe('isTerminal', () => {
  it('is true only for completed and failed', () => {
    expect(isTerminal('queued')).toBe(false)
    expect(isTerminal('running')).toBe(false)
    expect(isTerminal('completed')).toBe(true)
    expect(isTerminal('failed')).toBe(true)
  })
})
