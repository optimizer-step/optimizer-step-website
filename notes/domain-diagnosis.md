# optimizerstep.com diagnosis — 20 November 2026

## Observed behavior

- `GET https://optimizerstep.com/` returns **301** to `https://www.optimizerstep.com`.
- `GET https://www.optimizerstep.com/` returns **404** with `server: railway-hikari` and `x-railway-fallback: true`.
- `GET https://nngjq0lu.up.railway.app/` also returns Railway fallback **404**.
- TLS validation succeeded for both public HTTPS hosts (`curl` SSL verify result `0`). The observed failure is service availability/routing, not a browser certificate error. GoDaddy's forwarding service returns **405** for HEAD requests at the apex but **301** for GET.
- In the Railway dashboard, project `daring-spirit` reports **Trial expired**, **0 / 3 services online**. The `optimizer-step-website` service says **Service offline** and **There is no active deployment for this service**. The Postgres and voice-worker services are offline too. The website service's start command and `/health` check are already configured.
- GoDaddy forwarding is set to **Permanent (301)** from `optimizerstep.com` to `https://www.optimizerstep.com`.

## GoDaddy DNS records

These were read in the logged-in GoDaddy DNS view. A `@` host is the zone apex. Trailing dots are shown as GoDaddy displays them.

| Type | Host | Value | TTL |
| --- | --- | --- | --- |
| A | @ | `15.197.225.128` | 1 hour |
| A | @ | `3.33.251.168` | 1 hour |
| NS | @ | `ns57.domaincontrol.com.` | 1 hour |
| NS | @ | `ns58.domaincontrol.com.` | 1 hour |
| CNAME | www | `nngjq0lu.up.railway.app.` | 1 hour |
| CNAME | _domainconnect | `_domainconnect.gd.domaincontrol.com.` | 1 hour |
| TXT | @ | `google-site-verification=nFCRLM3qHHoManzcxd5Gn5MFrsKAlu9lsAc1SdbI7dY` | 600 seconds |
| TXT | @ | `v=spf1 include:dc-bdaca08905._spfm.optimizerstep.com ~all` | 1 hour |
| TXT | dc-bdaca08905._spfm | `v=spf1 include:_spf.google.com ~all` | 600 seconds |
| TXT | _dmarc | `v=DMARC1; p=quarantine; adkim=r; aspf=r; rua=mailto:dmarc_rua@onsecureserver.net;` | 1 hour |
| TXT | _railway-verify.www | `railway-verify=4fc8d7b0c37acbb0832c77812eaf7bdf2bcb00636aa71a4aa101ca3718443705` | 1 hour |
| TXT | google._domainkey | Google DKIM RSA public key (full value below) | 600 seconds |

The GoDaddy view also has an MX record for Google mail at `@` → `smtp.google.com.` (priority 1, TTL 600 seconds) and the standard SOA record. They are unrelated to the website routing and should be preserved.

Google DKIM TXT value:

```text
v=DKIM1;k=rsa;p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsdxDABDhugA/tmm2J1JxWjrljYfAQs3G1ZoeUkbXOh+bTvodGnUn5p7LdsKulpsncpbjZKIwpTnYlN11zcCiAbMCs5q4v8FB4A53tYoSdhgn3dESTrbHt7kmeUQqNXBx4+NvBPCX1cnr4bpJS7iiKYkKQFSTDEjn7W0UAMsSSZtm6ck20nWBKg2l5XR9SB4azmuUXWvLzux4uWfqfyZCqlgnJebMEq0NP9H24imjMOLBD21p4SQGNjoqbAlg7I1u5nkI+uoQJ46k9qr8d7FcVyCLjEGw5vuQu5OFx6gQYxGhVffbc15bd5dl39jFWnZFqQdl5KKlLkQCOPI5u6P7VwIDAQAB
```

## Required hosting target and exact next action

The domain is currently configured for **GoDaddy apex forwarding → www → Railway**. The current `www` CNAME and Railway ownership TXT are present. The Railway service is inactive because the trial has expired. **No GoDaddy DNS changes are recommended now.** Restore Railway service access, redeploy the website, and inspect the `www.optimizerstep.com` custom-domain status in the Railway service. If Railway still lists `nngjq0lu.up.railway.app` and the current verification token, keep the GoDaddy records exactly as they are. If Railway supplies a new CNAME or TXT value, report that exact replacement and get explicit approval before changing GoDaddy.

Railway's [domain documentation](https://docs.railway.com/networking/domains/working-with-domains) says both the service CNAME and ownership TXT are required; a missing or mismatched TXT can also produce fallback 404. The current GoDaddy view shows both records, but Railway's per-domain verification status could not be confirmed while the project is in limited access.
