# Optimizer Step course platform

A responsive AI and machine learning course site with a browser-only ML Playground. The site runs on the existing FastAPI server. The four labs use Canvas and local JavaScript math; they need no API keys.

## Local preview

Use Python 3.11 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/ and http://127.0.0.1:8000/playground.

## Checks

```powershell
.\.venv\Scripts\python -m pip install -r requirements-test.txt
node --check app.js
node --check playground.js
node --check launchCampaign.js
node --check voice.js
.\.venv\Scripts\python -m unittest discover -s tests
```

This is a buildless frontend, so there is no npm build or TypeScript typecheck. The Python server serves the checked HTML, CSS, and JavaScript files directly. The legacy chat, voice-token, and enquiry API routes remain in the server, but the new course frontend does not call them. Their operating notes are preserved in [the previous website README](docs/previous-website-readme.md).
The server may log that `DATABASE_URL` is unset during local checks; this is expected for the preserved enquiry endpoint and does not affect the course pages or browser labs.

## Founding 100 campaign

All campaign data lives in [launchCampaign.js](launchCampaign.js). The default `mode: "demo"` is deliberately visible in the interface. The initial 78/100 count and the sample enrollment toasts are illustrations; the form saves entries only to the current browser's local storage and increments only that browser's count. It does not reserve a real global seat or send an email. The planned regular price is editable in the same file.

For real enrollment:

1. Implement a shared server endpoint that validates name, email, experience, and track; prevents duplicate email enrollment; allocates one of 100 seats in a database transaction; and returns `{ "accepted": true, "claimed": 79 }`. Return a non-2xx status when full or when the request fails. Send confirmations from that server.
2. Implement a read endpoint that returns `{ "claimed": 79 }` from the same database. The client polls it every 30 seconds.
3. Set `mode: "live"`, `enrollmentEndpoint`, and `activityEndpoint` in `launchCampaign.js`. Remove or replace `sampleActivity` with verified, consented activity before displaying named enrollment events.
4. Confirm the offer terms, track availability, launch timing, and planned regular price before public enrollment.

If `mode` is live without an enrollment endpoint, the form fails closed with an error. Do not treat local-storage signups as real leads.

## Deploy the website service

The production website is connected to `optimizer-step/optimizer-step-website` on Railway. Railway already has the website start command `python -m uvicorn server:app --host 0.0.0.0 --port $PORT` and health check `/health` in service settings. The current Railway trial is expired and the service has no active deployment. A workspace owner must restore Railway service access before deployment can succeed.

After service access is restored, deploy this checkout directly:

```powershell
npm i -g @railway/cli
railway login
railway link
railway up --service optimizer-step-website --environment production
```

Choose the existing `daring-spirit` project when `railway link` asks. Alternatively, push and merge this branch to the connected repository's `main` branch; Railway is configured to deploy changes from that branch automatically. Verify `GET /health` and both public pages after the deployment becomes active.

## Domain diagnosis

See [the domain diagnosis](docs/domain-diagnosis.md) for the GoDaddy records and live response checks. No GoDaddy DNS change has been made. The apex already forwards permanently to `www`. The current `www` record resolves to Railway, but Railway returns a fallback 404 because the service is offline and there is no active deployment. After restoring Railway access, confirm the custom domain is attached and verified. Change the CNAME or verification TXT only if Railway displays a different required value; request approval before any GoDaddy DNS edit.
