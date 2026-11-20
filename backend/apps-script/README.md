# Founding 100 signup backend (Google Apps Script)

The website's signup form and live seat counter talk to a Google Apps Script web app that
stores every signup in a Google Sheet and emails each student a confirmation.

| What | Where |
| --- | --- |
| Spreadsheet | **Optimizer Step - Founding 100 signups** in the `admin@optimizerstep.com` Google Drive |
| Script | **Optimizer Step enrollment backend** (Sheet → Extensions → Apps Script) |
| Code | [`Code.gs`](Code.gs) in this folder (keep the two in sync) |
| Web app URL | `https://script.google.com/macros/s/AKfycbwIJKFScnpdf3f6hOsWhtm7kzTjuc5_8yj7oHDtSJPnXf7vkKjtG61HE3I_s4SQFKFX/exec` |
| Runs as | `admin@optimizerstep.com`, access: Anyone |
| Website setting | `enrollmentEndpoint` in [`site/assets/js/config.js`](../../site/assets/js/config.js) |

## What it does

- `GET ?action=stats` returns `{ ok, claimed, capacity, remaining, open }` for the live seat counter (cached for 30 seconds).
- `POST` (JSON sent as `text/plain`, so browsers skip the CORS preflight) validates the signup, refuses duplicates
  by email (case-insensitive), hands out seat numbers inside a script lock, appends a row and sends the confirmation email.
  The first `capacity` signups are `founding`; later ones are `waitlist`.
- Bots that fill the hidden `company` field get a fake success and nothing is stored.
- Text that starts with `= + - @` is stored with a leading apostrophe, so nobody can inject a formula into the sheet.

## The spreadsheet

**Signups** has one row per person: timestamp (IST), status, seat, name, email, track, experience,
`utm_source` / `utm_medium` / `utm_campaign` / `utm_content` / `utm_term`, ad click ID (`gclid` / `fbclid` / …),
referrer, landing page, first touch, signup page, device, whether the email was sent, and flags
(`fast-submit` = the form was submitted within 2.5 seconds, which is often a bot).

To remove a test or spam entry from the counts, change its **Status** to `removed` (or delete the row).

**Settings** controls the live campaign without touching code (changes apply within about a minute):

| Setting | Meaning |
| --- | --- |
| `capacity` | Number of free founding seats (default 100). Raise it to open more seats. |
| `campaign_open` | `FALSE` pauses new signups. |
| `send_emails` | `FALSE` stops confirmation emails. |
| `from_name`, `reply_to` | Sender name and reply address of the confirmation email. |
| `site_url`, `youtube_url` | Links used inside the email. |

## Email limit

Google currently allows this account **100 Apps Script emails per day** (the setup log reported 100).
If more than 100 people sign up in one day, their signups are still saved, but the extra confirmation
emails fail and the **Email sent** column says `failed: …`. If the ads bring more than that, either
email those students manually from the sheet, or move confirmations to an email service (Brevo, MailerLite, etc.).

## Updating the code

1. Edit `Code.gs` here, then paste it into the Apps Script editor (replace everything) and save.
2. **Deploy → Manage deployments → ✏️ Edit → Version: New version → Deploy.**
   Editing the existing deployment keeps the same URL, so the website needs no change.
   (Creating a *new* deployment gives a new URL, which would then have to go into `config.js`.)

## Quick checks

```powershell
curl.exe -sL "https://script.google.com/macros/s/AKfycbwIJKFScnpdf3f6hOsWhtm7kzTjuc5_8yj7oHDtSJPnXf7vkKjtG61HE3I_s4SQFKFX/exec?action=stats"
```

Executions and errors are listed in the Apps Script editor under **Executions**.
