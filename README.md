# Optimizer Step course platform

A responsive AI and machine learning course site with a browser-only ML Playground. The course pages and four Canvas labs run as static files on GitHub Pages and need no API keys. The existing FastAPI server remains available for the legacy API routes.

## Public preview on GitHub Pages

GitHub Pages publishes the `/docs` folder from `codex/ai-course-platform` at https://www.optimizerstep.com/. The playground is at https://www.optimizerstep.com/#playground. To update the published files after editing the root frontend files, run `python scripts/build_pages.py`, then commit and push the changed `/docs` files. Keep `docs/CNAME` in place so GitHub Pages retains the custom domain.

GitHub Pages serves only static files. The Founding 100 form is still a browser-local demonstration; it does not collect real enrollments, share a seat count, or send emails. A separate enrollment service is needed before using it for a live campaign.

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

This is a buildless frontend, so there is no npm build or TypeScript typecheck. The Python server can serve the checked HTML, CSS, and JavaScript files locally. The legacy chat, voice-token, and enquiry API routes remain in the server, but the new course frontend does not call them. Their operating notes are preserved in [the previous website README](docs/previous-website-readme.md).
The server may log that `DATABASE_URL` is unset during local checks; this is expected for the preserved enquiry endpoint and does not affect the course pages or browser labs.

## Founding 100 campaign

All campaign data lives in [launchCampaign.js](launchCampaign.js). The default `mode: "demo"` is deliberately visible in the interface. The initial 78/100 count and the sample enrollment toasts are illustrations; the form saves entries only to the current browser's local storage and increments only that browser's count. It does not reserve a real global seat or send an email. The planned regular price is editable in the same file.

For real enrollment:

1. Implement a shared server endpoint that validates name, email, experience, and track; prevents duplicate email enrollment; allocates one of 100 seats in a database transaction; and returns `{ "accepted": true, "claimed": 79 }`. Return a non-2xx status when full or when the request fails. Send confirmations from that server.
2. Implement a read endpoint that returns `{ "claimed": 79 }` from the same database. The client polls it every 30 seconds.
3. Set `mode: "live"`, `enrollmentEndpoint`, and `activityEndpoint` in `launchCampaign.js`. Remove or replace `sampleActivity` with verified, consented activity before displaying named enrollment events.
4. Confirm the offer terms, track availability, launch timing, and planned regular price before public enrollment.

If `mode` is live without an enrollment endpoint, the form fails closed with an error. Do not treat local-storage signups as real leads.

## Legacy Railway service

The previous production website is connected to `optimizer-step/optimizer-step-website` on Railway. Its trial is expired and the service has no active deployment. The course frontend now runs on GitHub Pages. Restoring the legacy API routes would require renewed Railway access or another server host.

## Domain cutover

The GoDaddy `www` CNAME now points to `optimizer-step.github.io`, and `www.optimizerstep.com` is the GitHub Pages custom domain. The apex continues to forward to `www`. See [the earlier domain diagnosis](docs/domain-diagnosis.md) for the former Railway record. Check DNS resolution and HTTPS after future domain changes; GitHub Pages may take time to provision a certificate for a new custom domain.
