# Optimizer Step website

The public website at https://www.optimizerstep.com/: a conversion-focused landing page for the
**Founding 100** free-seat campaign, four course track pages, a free browser-only ML Playground
(four labs, each on its own page), privacy and terms pages, and a thank-you page for ad conversion tracking.
Signups go to a Google Sheet through a small Google Apps Script backend.

## How it fits together

| Part | Where | Notes |
| --- | --- | --- |
| Website source | [`site/`](site) | Edit here, never in `docs/`. |
| Words, tracks, labs, videos, FAQ | [`site/content.py`](site/content.py) | Keep every claim true. |
| Page templates and build | [`scripts/build_pages.py`](scripts/build_pages.py) | Writes `docs/`, sitemap, robots.txt, manifest; checks every internal link. |
| Styles | [`site/assets/css/site.css`](site/assets/css/site.css) | Dark theme by default, light theme via the toggle. |
| Behaviour | [`site/assets/js/`](site/assets/js) | `site.js` (forms, live seats, tracking), `hero.js`, `playground.js`, `welcome.js`. |
| Settings and ad tracking IDs | [`site/assets/js/config.js`](site/assets/js/config.js) | Backend URL, Meta Pixel, GA4, Google Ads, Clarity. |
| Images | [`site/assets/img/`](site/assets/img) | Made from [`site/source-images/`](site/source-images) by `python scripts/make_images.py`. |
| Published site | [`docs/`](docs) | GitHub Pages serves `/docs` from the `codex/ai-course-platform` branch. Keep `docs/CNAME`. |
| Signup backend | [`backend/apps-script/`](backend/apps-script) | Google Apps Script web app + Google Sheet. See its README. |

## Publish a change

```powershell
python scripts/build_pages.py
git add -A
git commit -m "Describe the change"
git push
```

GitHub Pages updates the live site about a minute after the push. The build prints `Internal links and anchors: all OK`;
if it lists link problems, fix them before pushing. CSS and JS URLs carry a content hash (`?v=…`), so visitors never get
a stale file after a deploy.

## Local preview

```powershell
python -m http.server 8765 --directory docs
```

Then open http://127.0.0.1:8765/. Signups from the local preview go to the real backend, so use a test address
and delete the test row from the sheet afterwards (or set its Status to `removed`).

## Signups and the seat counter

- The form posts to the Apps Script web app in `config.js` → `enrollmentEndpoint`.
- Every signup is a row in **Optimizer Step - Founding 100 signups** (Google Drive of `admin@optimizerstep.com`),
  with the ad campaign that brought the person (UTM tags and click IDs).
- The first 100 are founding seats; later signups join the waitlist automatically. Change the number of seats,
  pause signups or stop emails in the sheet's **Settings** tab.
- The counter shows "100 free founding seats" until 10 seats are claimed (`showCountsAfter` in `config.js`), then
  "N of 100 free seats left". It never shows invented numbers.
- After signing up, people land on `/welcome/` (confirmation, YouTube, Playground, share buttons).

Details, limits (100 confirmation emails per day on this account) and how to redeploy are in
[`backend/apps-script/README.md`](backend/apps-script/README.md).

## Ads and tracking

1. Paste your IDs into `site/assets/js/config.js` → `tracking` (Meta Pixel ID, GA4 measurement ID, Google Ads ID
   and sign-up conversion label, Microsoft Clarity project ID), rebuild and push. Empty IDs load nothing.
2. Events sent automatically:
   - Meta: `PageView`, `Lead` and `CompleteRegistration` on `/welcome/` (once per signup), plus custom
     `SignupFormOpen`, `CTAClick`, `PlaygroundInteraction`, `VideoPlay`, and `ViewContent` on track pages.
   - Google (GA4 / Ads): `page_view`, `sign_up`, `generate_lead`, `conversion` (when the Ads label is set),
     `form_open`, `form_start`, `form_error`, `cta_click`, `share`, `outbound_click`.
   - URL-based conversions also work: count visits to `/welcome/`.
3. Tag every ad link so each signup row shows where it came from, for example
   `https://www.optimizerstep.com/?utm_source=instagram&utm_medium=paid_social&utm_campaign=founding100&utm_content=reel_1`.
   Click IDs (`fbclid`, `gclid`) are captured automatically.
4. Add `&join=1` to open the signup form straight away, and `&track=rag` (or `foundations`, `deep-learning`, `nlp`)
   to preselect a track. Track pages such as `/courses/rag/` are good landing pages for track-specific ads.

## Domain

- `www.optimizerstep.com` → CNAME `optimizer-step.github.io` (GitHub Pages custom domain, HTTPS enforced).
- `optimizerstep.com` → A `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` and
  AAAA `2606:50c0:8000::153` … `2606:50c0:8003::153` (GitHub Pages), so every path on the bare domain redirects to
  the same path on www. The old GoDaddy forwarding was removed on 20 November 2026.
- Email (Google Workspace MX, SPF, DKIM, DMARC) is unchanged. Older DNS notes: [notes/domain-diagnosis.md](notes/domain-diagnosis.md).

## Legacy files

The root `index.html`, `app.js`, `playground.js`, `launchCampaign.js` and `styles.css` are the previous single-page
version, kept only for the legacy FastAPI server (`server.py`, tests in `tests/`). They are not published.
The legacy chat, voice and enquiry API routes are documented in [notes/previous-website-readme.md](notes/previous-website-readme.md);
the Railway service that hosted them has an expired trial.

```powershell
.\.venv\Scripts\python -m unittest discover -s tests
```
