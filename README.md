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
| "What AI teams hire for" section | `SKILL_*` in [`site/content.py`](site/content.py) | Company names (never logos) from real job posts; evidence in [`notes/skills-evidence-2026-11-20.json`](notes/skills-evidence-2026-11-20.json). |
| Price ladder and `/pricing/` | `PRICE_TIERS`, `FOUNDING_DISCOUNT`, `PRO_LIVE_MONTHS` in [`site/content.py`](site/content.py) | Every price on the site (cards, FAQ, terms, track pages, the "planned price") is computed from these. Research: [`notes/pricing-research-2026-11-20.md`](notes/pricing-research-2026-11-20.md). |
| Minifier | [`package.json`](package.json), [`scripts/minify.mjs`](scripts/minify.mjs) | esbuild shrinks the published CSS/JS. Run `npm ci` once. |
| Page templates and build | [`scripts/build_pages.py`](scripts/build_pages.py) | Writes `docs/`, sitemap, robots.txt, manifest; checks every internal link. |
| Styles | [`site/assets/css/site.css`](site/assets/css/site.css) | Dark theme by default, light theme via the toggle. |
| Behaviour | [`site/assets/js/`](site/assets/js) | `site.js` (forms, live seats, tracking), `hero.js`, `playground.js`, `welcome.js`. |
| Settings and ad tracking IDs | [`site/assets/js/config.js`](site/assets/js/config.js) | Backend URL, Meta Pixel, GA4, Google Ads, Clarity. |
| Images | [`site/assets/img/`](site/assets/img) | Made from [`site/source-images/`](site/source-images) by `python scripts/make_images.py`. |
| Published site | [`docs/`](docs) | GitHub Pages serves `/docs` from the `codex/ai-course-platform` branch. Keep `docs/CNAME`. |
| Signup backend | [`backend/apps-script/`](backend/apps-script) | Google Apps Script web app + Google Sheet. See its README. |

## Publish a change

```powershell
npm ci
```

(first time only: installs the minifier, esbuild). Then, for every change:

```powershell
python scripts/build_pages.py; if ($LASTEXITCODE -eq 0) { git add -A; git commit -m "Describe the change"; git push }
```

About a minute after the push, tell Bing and the other IndexNow search engines that the pages changed:

```powershell
python scripts/indexnow.py
```

GitHub Pages updates the live site about a minute after the push. The build prints `Internal links and anchors: all OK`;
if it lists link problems, fix them before pushing. CSS and JS URLs carry a content hash (`?v=…`), so visitors never get
a stale file after a deploy.

The published CSS and JS in `docs/` are minified (comments removed, local names shortened) and the HTML is compacted,
so the files are smaller and hard to read. Browsers must download a site's code to run it, so no website can hide its
front-end code completely; the readable source lives in `site/` and the signup data stays private in the Google Sheet.
This GitHub repository is public, so the source is also readable here unless the repository is made private
(GitHub Pages from a private repository needs a paid GitHub plan).

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
  "N of 100 free seats left", "Only N of 100 free seats left" (25 or fewer) and "Last N free founding seats" (10 or fewer).
  Under the counter, "N people joined in the last 24 hours" appears once at least 3 did (`todayAfter`).
  It never shows invented numbers.
- "Founding seat #23 claimed: A Python learner picked NLP & Transformers · 5 minutes ago" notices come from the
  real signups of the last 72 hours (seat, track, experience level and time only: never names or emails). They start
  once 10 seats are claimed, show at most 3 per page and 6 per visit, never to people who already signed up, and a
  visitor can close them. Settings: `liveNotices` in `config.js`. Making up signups or scarcity is illegal in India
  (CCPA dark-pattern guidelines, 2023) and breaks Meta's and Google's ad policies, so keep these real.
- After signing up, people land on `/welcome/` (confirmation, a first free lesson picked for their track, YouTube,
  Playground, share buttons).

Details, limits (100 confirmation emails per day on this account) and how to redeploy are in
[`backend/apps-script/README.md`](backend/apps-script/README.md).

## Pricing

- **Starter (free for good):** ML Foundations, its project, the ML Playground and the YouTube lessons. It is the way
  into Optimizer Step.
- **Single Track ₹999, All Tracks ₹1,999 ("Best value"), Pro ₹4,999:** one-time prices including all taxes.
  All Tracks is only ₹1,000 more than one track for three times the tracks, and Pro adds a monthly live Q&A for
  12 months plus written project feedback. Upgrades cost only the difference.
- **Founding 100:** All Tracks free, the Pro upgrade for ₹1,799 (40% off the ₹3,000 step) and 40% off future paid tracks.
- The paid tiers are **planned**: the pages say they open with the tracks. Before taking payments, add the checkout,
  publish the refund terms (the terms page promises they appear before payment) and keep every promise in
  `PRICE_TIERS` deliverable. To change a price, edit `PRICE_TIERS` and rebuild; nothing else needs editing.

## Ads and tracking

Meta: the pixel `1131433136148670` (dataset "Optimizer Step website") belongs to the **Optimizer Step** business
portfolio in Meta Business settings, together with the ad account. `optimizerstep.com` is verified there through the
`facebook-domain-verification` meta tag in every page's head (`SITE["facebook_domain_verification"]`); keep the tag.
Automatic advanced matching is on for email and name only (Events Manager → dataset → Settings).

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

## Search engines

- **Google:** the site is verified in Google Search Console (admin@optimizerstep.com) and `sitemap.xml` is submitted
  there. Use Search Console → URL inspection → "Request indexing" after big changes.
- **Bing, DuckDuckGo, Yahoo, Yandex:** run `python scripts/indexnow.py` after each deploy (IndexNow; the key file is
  `site/static/<key>.txt`, published at the site root).
- Each page has a title, description, canonical URL, Open Graph tags and structured data (organisation, website with the
  "OptimizerStep" alternate name, instructor, FAQ, courses, breadcrumbs). Keep the YouTube channel, Instagram and X
  profiles linking to https://www.optimizerstep.com/: those links help Google connect the brand to the site.

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
