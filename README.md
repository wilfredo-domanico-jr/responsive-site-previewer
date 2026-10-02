# Responsive Site Previewer

Enter a public website address and get full-page screenshots of it at four device sizes: desktop, laptop, tablet and mobile. The previews appear in a dashboard as they are captured, can be viewed as a size-proportional grid or one large image at a time, and each one can be downloaded as a PNG.

## Features

- Captures any publicly reachable `http://` or `https://` URL at exactly 1920×1080, 1440×900, 768×1024 and 390×844.
- Full-page screenshots, with JavaScript executed and network activity allowed to settle.
- Real progress reporting: the UI shows the backend's actual step ("Opening website…", "Capturing tablet…", "Finishing…") and shows each screenshot as soon as it exists.
- Grid view with device frames sized in proportion to their viewports, plus a large single-device view.
- Download button per device, served with a descriptive filename.
- Friendly error messages for empty or invalid URLs, unsupported schemes, DNS failures, connection failures, timeouts, SSL problems, HTTP error responses and browser errors. No stack traces reach the client.
- First-layer SSRF protection: only `http`/`https`, no credentials in the URL, and `localhost`, loopback, private, link-local and other internal addresses are refused, including hostnames that resolve to them and redirects that land on them.
- No database, auth or cloud storage. Screenshots are stored on local disk under `backend/screenshots/<job-id>/`.

## Tech stack

| Layer    | Choice                                                      |
|----------|-------------------------------------------------------------|
| Frontend | Nuxt 4, Vue 3, TypeScript, Tailwind CSS v4                  |
| Backend  | Python 3.12+, FastAPI, Playwright (Chromium), pydantic-settings |
| Tests    | pytest (backend), Vitest (frontend client logic)            |
| Dev ops  | Docker + docker compose                                     |

## Requirements

- Node.js 20 or newer and npm
- Python 3.12 or newer (developed on 3.13)
- Docker with Compose (optional, for the containerised setup)

## Local development

Clone the repository, then set up the two halves. They run on different ports and the browser talks to the backend directly.

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Install the Playwright browser (one-time; downloads Chromium into Playwright's cache):

```bash
python -m playwright install chromium
# On Linux you may also need OS libraries:
# python -m playwright install --with-deps chromium
```

Optional configuration lives in environment variables or a `backend/.env` file (see `backend/.env.example`):

| Variable                  | Default                      | Purpose                                              |
|---------------------------|------------------------------|------------------------------------------------------|
| `SCREENSHOT_DIR`          | `./screenshots`              | Where PNGs are written                               |
| `CORS_ORIGINS`            | `http://localhost:3000`      | Comma-separated allowed browser origins              |
| `NAVIGATION_TIMEOUT_MS`   | `30000`                      | Max time for the page to load                        |
| `NETWORK_IDLE_TIMEOUT_MS` | `5000`                       | Best-effort wait for network activity to settle      |
| `SETTLE_DELAY_MS`         | `500`                        | Extra pause after load for animations and lazy JS    |
| `MAX_CONCURRENT_JOBS`     | `2`                          | How many preview jobs capture at the same time       |
| `MAX_FULL_PAGE_HEIGHT`    | `10000`                      | Taller pages are clipped to this height in pixels    |
| `BLOCKED_HOSTNAMES`       | `metadata.google.internal`   | Extra hostnames to refuse, comma-separated           |

Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive API docs are then at <http://localhost:8000/docs>.

Run the backend tests (no browser needed; the screenshot step is faked):

```bash
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app is served at <http://localhost:3000>. It calls the backend at `http://localhost:8000` by default; override with `NUXT_PUBLIC_API_BASE` (see `frontend/.env.example`).

Other commands:

```bash
npm run test        # Vitest unit tests for the API client
npm run typecheck   # vue-tsc via nuxt typecheck
npm run build       # production build into .output/
```

## Docker

Build and start both services:

```bash
docker compose up --build
```

- Frontend: <http://localhost:3000>
- Backend: <http://localhost:8000> (API docs at `/docs`)

The backend image is based on `mcr.microsoft.com/playwright/python`, which ships Chromium and its system libraries, so no browser install step runs in the container. Screenshots are written to `./backend/screenshots` on the host through a bind mount. `shm_size` is raised because Chromium needs more shared memory than Docker's default.

## API

All endpoints are JSON. Errors use FastAPI's shape: `{"detail": "<user-friendly message>"}`.

### `GET /api/health`

```json
{ "status": "ok" }
```

### `POST /api/preview`

Starts a preview job. Validation errors return `400` immediately; otherwise the job is accepted and capture runs in the background.

Request:

```json
{ "url": "https://example.com" }
```

Response `202 Accepted`:

```json
{
  "job_id": "0d4f7ec88cc3",
  "url": "https://example.com",
  "status": "queued",
  "step": "Queued...",
  "error": null,
  "previews": {},
  "created_at": "2026-10-02T09:08:06.659235Z"
}
```

### `GET /api/preview/{job_id}`

Returns the current state of a job. Poll it until `status` is `completed` or `failed`. `previews` fills in one device at a time while the job runs.

| `status`    | Meaning                                                     |
|-------------|-------------------------------------------------------------|
| `queued`    | Waiting for a capture slot                                  |
| `running`   | Capturing; `step` holds the current human-readable step     |
| `completed` | All four previews are present                               |
| `failed`    | `error` holds a user-friendly explanation                   |

Completed example:

```json
{
  "job_id": "0d4f7ec88cc3",
  "url": "https://example.com",
  "status": "completed",
  "step": "Finishing...",
  "error": null,
  "previews": {
    "desktop": { "width": 1920, "height": 1080, "image": "/screenshots/0d4f7ec88cc3/desktop.png" },
    "laptop":  { "width": 1440, "height": 900,  "image": "/screenshots/0d4f7ec88cc3/laptop.png" },
    "tablet":  { "width": 768,  "height": 1024, "image": "/screenshots/0d4f7ec88cc3/tablet.png" },
    "mobile":  { "width": 390,  "height": 844,  "image": "/screenshots/0d4f7ec88cc3/mobile.png" }
  },
  "created_at": "2026-10-02T09:08:06.659235Z"
}
```

`image` paths are relative to the backend host, e.g. `http://localhost:8000/screenshots/0d4f7ec88cc3/desktop.png`.

Unknown or malformed job ids return `404 {"detail": "Preview job not found."}`.

### `GET /api/preview/{job_id}/download/{device}`

Returns the PNG for `device` (`desktop`, `laptop`, `tablet` or `mobile`) as an attachment named like `example.com-tablet-768x1024.png`. Available once the job is `completed`; otherwise `404`.

### `GET /screenshots/{job_id}/{device}.png`

Static file serving for the generated images.

### Error messages you can expect

| Situation                              | HTTP / job state         | Message                                                            |
|----------------------------------------|--------------------------|--------------------------------------------------------------------|
| Empty URL                              | `400`                    | Please enter a website URL.                                        |
| `ftp://`, `file://`, `javascript:` …   | `400`                    | Only http:// and https:// URLs are supported.                      |
| `localhost`, `127.0.0.1`, `10.x`, …    | `400`                    | Local and internal addresses cannot be previewed.                  |
| Hostname does not resolve              | `400`                    | We couldn't find that website. Check the address and try again.    |
| Connection refused / reset             | job `failed`             | We couldn't connect to the website.                                |
| Page took longer than the timeout      | job `failed`             | The website took too long to respond.                              |
| Certificate or TLS error               | job `failed`             | The website has an SSL/certificate problem, so it couldn't be loaded securely. |
| Server answered 4xx/5xx                | job `failed`             | The website responded with HTTP 404.                               |
| Redirect to an internal address        | job `failed`             | The website redirected to a blocked address.                       |
| Anything else inside the browser       | job `failed`             | Something went wrong while capturing the website. Please try again. |

## Project structure

```
responsive-site-previewer/
├── frontend/                 Nuxt 4 app
│   └── app/
│       ├── pages/index.vue           page layout and view state
│       ├── components/               UrlForm, PreviewToolbar, PreviewGrid, PreviewCard, PreviewLarge, ErrorBanner, DeviceIcon
│       ├── composables/              usePreviewJob (start + poll), usePreviewClient
│       ├── utils/previewClient.ts    framework-free API client (unit tested)
│       └── types/preview.ts          shared types and the device list
├── backend/                  FastAPI app
│   ├── app/
│   │   ├── main.py                   app factory, lifespan, CORS, static mount
│   │   ├── config.py                 settings from environment
│   │   ├── api/                      health.py, preview.py
│   │   ├── models/                   pydantic responses, in-memory Job
│   │   ├── services/                 url_validator, screenshot_service, job_runner, job_store
│   │   └── utils/                    error mapping, ids
│   ├── tests/
│   ├── screenshots/                  generated output (git-ignored)
│   └── requirements.txt
├── docker-compose.yml
└── README.md
```

The job runner is an in-process asyncio task behind a small `JobStore`/`JobRunner` pair. Moving to a real queue later means replacing those two classes; the API surface stays the same.

## Known limitations

- Jobs live in memory. Restarting the backend forgets them, although the PNG files stay on disk. There is no cleanup of old screenshot folders yet.
- SSRF protection is a first layer. The submitted URL and the final URL after redirects are checked, but sub-resource requests made by the page are not filtered.
- Full-page capture is clipped at `MAX_FULL_PAGE_HEIGHT` pixels. Sites with infinite scroll, cookie walls, bot protection or heavy lazy loading may render partially or differently from a real visit.
- Only the viewport size changes between devices. The user agent and touch emulation are not changed, so sites that pick a layout by user-agent sniffing rather than CSS media queries will show their desktop layout.
- The browser talks to the backend directly, so the backend port must be reachable from the user's machine (true for local development and the provided Compose setup).

## License

MIT. See `LICENSE`.
