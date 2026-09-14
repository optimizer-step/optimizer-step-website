# Optimizer AI website

## Website experience

A restrained cobalt, navy and white design, an illustrative workflow, a static
AI ecosystem strip, concise services, and expandable industry examples. Chat
and voice share a tabbed playground with arrow-key navigation. Switching away
from voice ends any active call. The floating assistant supports Escape and
returns keyboard focus to its launcher when closed. The calculator announces
updated results. The contact form saves each enquiry and can email it to your
team (see Contact form enquiries). Existing endpoints and provider settings are preserved.


The voice panel now uses real microphone audio over LiveKit with Sarvam STT,
LLM and Bulbul speech synthesis. The text chatbot uses the OpenAI API.
Voice conversations do not save leads or book meetings.

## Run the voice website

Use Python 3.11 or newer. In this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill in `.env` with your LiveKit project URL, API key/secret and Sarvam API key.
Keep these values server-side. Run these in two terminals:

```powershell
.\.venv\Scripts\python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

```powershell
.\.venv\Scripts\python agent.py dev
```

Visit http://localhost:8000, select a language, start the conversation and allow
microphone access. Opening index.html directly or using python's static HTTP
server will not provide the token endpoint.

## Language and speech

Select Telugu, Hindi, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati,
Punjabi, Odia or Indian English before starting. STT and TTS use that locale;
the prompt encourages native script, everyday phrasing and English business
words where natural. Start a new call to change language. The agent uses short
replies, normal speech pace, turn detection and interruptions. Actual accent,
pronunciation and response latency must be evaluated with native speakers.

Model and voice defaults are configurable in `.env`. Defaults follow the supplied
agent: saaras:v4, sarvam-105b-conversations, bulbul:v3 and priya.
References: https://docs.livekit.io/agents/models/stt/sarvam/ and
https://docs.livekit.io/agents/models/tts/sarvam/ .

## Hosting

Host server.py on a Python web service and agent.py as a persistent worker
connected to the same LiveKit project (production command: python agent.py start).
Use HTTPS and set VOICE_ALLOWED_ORIGIN to the exact website origin, without a
trailing slash. The frontend uses a pinned LiveKit client from jsDelivr.
A static-only Sites deployment cannot host this Python worker or token endpoint.
No live deployment or end-to-end audio validation is possible without configured
provider credentials and an active worker.

The backend permits three token requests per IP per ten minutes, with a
60-second join token. The worker deletes each room after 90 seconds; a browser
limit also ends the call. Run one API worker: the limiter is in memory and resets
on restart. Before public rollout add shared rate limits, authenticated access
or a bot challenge, and provider spending limits. Behind a proxy, configure
trusted forwarded headers correctly; do not trust arbitrary forwarded IPs.
Origin checks alone are not authentication. No audio/transcript persistence is
implemented here; review provider retention settings separately.

Only explicit public files are served. `.env` and Python source are not served.
Telephony and CRM integrations are outside this browser voice implementation.

## Checks

```powershell
.\.venv\Scripts\python -m unittest discover -s tests
node --check app.js
node --check voice.js
```


## Real text chat and usage limits

Both text panels call `/api/chat` through the same Python server and share the
current page's conversation. OpenAI credentials stay on the server. Add `OPENAI_API_KEY` to `.env`.
The default `OPENAI_CHAT_MODEL` is `gpt-4.1-mini`. Voice still uses Sarvam. Refreshing clears the conversation text, but does not reset usage.

The default allowance is four API attempts per IP address per UTC day, across
both chat panels, plus a hard site-wide cap of 40 attempts per UTC day. These are
attempts/replies, not four unlimited chat sessions. People on the same network
share the allowance. Counters persist in `chat_usage.sqlite3`; preserve this file
on persistent storage when deploying. Multiple servers must share an atomic
central quota store; independent databases would each grant their own allowance.
A key rotation changes the hashed IP identifier but not the site-wide counter.

Change `CHAT_VISITOR_DAILY_LIMIT` (0-4) and `CHAT_SITE_DAILY_LIMIT` in `.env`.
New settings are read on each request unless overridden by process environment.
If a value was already loaded at startup, restart the server to change it.
A newly added `OPENAI_API_KEY` is picked up without a restart. Setting either to zero disables text generation. Defaults
work without editing an existing `.env`. Voice limits remain independent.

Each request accepts up to 800 characters plus at most six bounded history
messages; generated output is capped at 256 tokens. The server reserves quota
atomically before contacting OpenAI, counts failed calls and never retries them
automatically. This bounds usage, not a precise rupee amount. Provider pricing
and other services using the same key affect the total bill.

Only hashed IP usage counters are stored; chat text stays in page memory and is
sent to OpenAI for responses with `store: false`. Old daily counters are removed on the next request.
Set trusted reverse-proxy settings carefully so visitors cannot spoof their IP.
Reference: https://developers.openai.com/api/reference/python/resources/responses/methods/create


The text assistant represents Optimizer AI's consulting and implementation services.
Tool recommendation requests are answered with a relevant workflow our team could
build, followed by a discovery question. The prompt prohibits vendor referrals,
external product lists, invented commercial claims and fabricated contact actions.
Visitor-named systems may be discussed as integration context only. This is model
prompting, not an exhaustive output filter; review real conversations when refining
commercial messaging. Prior assistant recommendations do not override the policy.


## Logo strip assets

The static AI ecosystem strip displays brand references, not a partnership claim.
OpenAI, NVIDIA and Claude SVG wordmarks are sourced from the public SVGL library
(https://github.com/pheralb/svgl/tree/main/static/library). Sarvam's wordmark
image comes from its official brand guidelines (https://www.sarvam.ai/brand-guidelines).
Marks belong to their respective owners. Assets are hosted locally; the strip has
no external navigation or animation. It does not use any AI API quota.

The expandable technology note describes the implemented website stack. The
fictional company showcase and unsupported illustrative savings figures were
removed in the design update.

## Contact form enquiries

The contact form posts to `/api/enquiry`. Each enquiry is saved to
`enquiries.sqlite3` first, so a lead is never lost. When email is configured, the
server also emails it to your team with Reply-To set to the visitor, so you can
answer directly. If sending fails, the server terminal logs a warning and the
enquiry stays saved.

Add these to `.env`. New keys are picked up without a restart; changing a value
that was already loaded at startup requires restarting the server.

```
ENQUIRY_TO_EMAIL=you@yourcompany.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-sending-account@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-sending-account@gmail.com
```

For Gmail, `SMTP_PASSWORD` must be an App Password (Google Account > Security >
2-Step Verification > App passwords), not the normal account password. Port 465
uses implicit TLS; other ports use STARTTLS.

Export saved enquiries to a spreadsheet:

```powershell
.\.venv\Scripts\python enquiry_api.py enquiries.csv
```

The endpoint checks the website origin, allows five submissions per IP per ten
minutes (in memory, like the voice limiter) and silently discards submissions
that fill a hidden honeypot field. `enquiries.sqlite3` holds personal data: keep
it on persistent, access-restricted storage when deploying and delete old
enquiries according to your privacy policy.
#   o p t i m i z e r - s t e p - w e b s i t e  
 