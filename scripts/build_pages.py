"""Build the static Optimizer Step website into /docs (published by GitHub Pages).

    python scripts/build_pages.py

Source files live in /site:
  site/content.py        words, tracks, labs, videos, FAQs
  site/assets/           CSS, JavaScript and images (copied with cache-busting ?v= hashes)
  site/static/           files served from the site root (favicon.ico, apple-touch-icon.png)

The build wipes /docs (except CNAME and .nojekyll), writes every page, the sitemap,
robots.txt and the web manifest, and then checks every internal link and #anchor.
"""
from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "site"
OUT = ROOT / "docs"
KEEP = {"CNAME", ".nojekyll"}

spec = importlib.util.spec_from_file_location("site_content", SRC / "content.py")
content = importlib.util.module_from_spec(spec)
spec.loader.exec_module(content)

SITE = content.SITE
TRACKS = content.TRACKS
LABS = content.LABS
VIDEOS = content.VIDEOS
FAQS = content.FAQS
LAB_PANELS = content.LAB_PANELS
LAB_EXPLAINERS = content.LAB_EXPLAINERS
PRICE_TIERS = content.PRICE_TIERS
TIER_BY_ID = {t["id"]: t for t in PRICE_TIERS}
FOUNDING_DISCOUNT = content.FOUNDING_DISCOUNT
PRO_LIVE_MONTHS = content.PRO_LIVE_MONTHS
SKILL_DEMAND = content.SKILL_DEMAND
SKILL_COMPANIES = content.SKILL_COMPANIES
SKILLS_CHECKED = content.SKILLS_CHECKED
SKILLS_POSTS_READ = content.SKILLS_POSTS_READ
TRACK_BY_ID = {t["id"]: t for t in TRACKS}
LAB_BY_SLUG = {lab["slug"]: lab for lab in LABS}
URL = SITE["url"]
TODAY = date.today().isoformat()

ASSET_HASHES: dict[str, str] = {}


def e(text: str) -> str:
    return html.escape(str(text), quote=True)


def strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def asset(rel: str) -> str:
    if rel not in ASSET_HASHES:
        raise KeyError(f"Unknown asset: {rel}")
    return f"/assets/{rel}?v={ASSET_HASHES[rel]}"


def config_endpoint() -> str:
    text = (SRC / "assets" / "js" / "config.js").read_text(encoding="utf-8")
    match = re.search(r'enrollmentEndpoint:\s*"([^"]*)"', text)
    return match.group(1) if match else ""


# --------------------------------------------------------------------------- components

def cta(label: str, where: str, track: str | None = None, cls: str = "button button-primary", arrow: bool = True) -> str:
    track_attr = f' data-track="{e(track)}"' if track else ""
    arrow_html = ' <span class="arrow" aria-hidden="true">→</span>' if arrow else ""
    return (f'<button class="{cls}" type="button" data-enroll data-cta="{e(where)}"{track_attr}>'
            f'<span data-cta-label="{e(label)}">{e(label)}</span>{arrow_html}</button>')


def signup_form(prefix: str, track: str = "undecided", context: str = "modal") -> str:
    options = [("undecided", "Not sure yet: help me choose")] + [(t["id"], f'{t["title"]} ({t["level"].lower()})') for t in TRACKS]
    option_html = "".join(
        f'<option value="{e(value)}"{" selected" if value == track else ""}>{e(label)}</option>' for value, label in options
    )
    experiences = ["Just starting", "Know some Python", "Building ML projects"]
    chips = "".join(
        f'<label class="chip"><input type="radio" name="experience" value="{e(x)}"{" required" if i == 0 else ""} '
        f'aria-describedby="{prefix}-experience-error"><span>{e(x)}</span></label>'
        for i, x in enumerate(experiences)
    )
    return f"""<form class="signup-form" data-signup-form="{e(context)}" novalidate>
  <p class="form-note" data-member-note hidden></p>
  <div class="field">
    <label for="{prefix}-name">Your name</label>
    <input id="{prefix}-name" name="name" type="text" autocomplete="name" required minlength="2" maxlength="80" placeholder="Your full name" aria-describedby="{prefix}-name-error">
    <p class="field-error" id="{prefix}-name-error" data-error-for="name" hidden></p>
  </div>
  <div class="field">
    <label for="{prefix}-email">Email address</label>
    <input id="{prefix}-email" name="email" type="email" inputmode="email" autocomplete="email" autocapitalize="off" spellcheck="false" required maxlength="254" placeholder="you@example.com" aria-describedby="{prefix}-email-hint {prefix}-email-error">
    <p class="field-hint" id="{prefix}-email-hint">We'll send your seat confirmation here.</p>
    <p class="field-suggest" data-email-suggest hidden>Did you mean <button type="button"></button>?</p>
    <p class="field-error" id="{prefix}-email-error" data-error-for="email" hidden></p>
  </div>
  <div class="field">
    <label for="{prefix}-track">Which track interests you most?</label>
    <select id="{prefix}-track" name="track">{option_html}</select>
  </div>
  <fieldset class="field">
    <legend>Your experience</legend>
    <div class="chip-row">{chips}</div>
    <p class="field-error" id="{prefix}-experience-error" data-error-for="experience" hidden></p>
  </fieldset>
  <div class="hp" aria-hidden="true"><label for="{prefix}-company">Company</label><input id="{prefix}-company" type="text" name="company" tabindex="-1" autocomplete="off"></div>
  <p class="form-error" data-form-error role="alert" hidden></p>
  <button class="button button-primary button-block" type="submit" data-submit><span data-cta-label="Claim my free seat">Claim my free seat</span> <span class="arrow" aria-hidden="true">→</span></button>
  <ul class="trust-row"><li>Free</li><li>No payment details</li><li>Takes 30 seconds</li></ul>
  <p class="form-fineprint">By claiming a seat you agree to the <a href="/terms/">terms</a> and <a href="/privacy/">privacy policy</a>. We only email you about the courses.</p>
</form>"""


def seat_meter() -> str:
    cap = SITE["capacity"]
    return (f'<div class="seats"><div class="seat-row"><strong data-seats-text>{cap} free founding seats. First come, first served.</strong></div>'
            f'<div class="progress" role="progressbar" aria-label="Founding seats claimed" aria-valuemin="0" aria-valuemax="{cap}" aria-valuenow="0" data-seats-meter hidden><span></span></div>'
            f'<p class="seat-today" data-seats-today hidden></p></div>')


def offer_card(prefix: str, track: str = "undecided") -> str:
    return f"""<div class="offer-card" data-signup-inline>
  <div class="offer-top"><span class="offer-icon" aria-hidden="true">✦</span><span>Founding member access</span></div>
  <div class="price"><del><span class="visually-hidden">Planned price </span>{e(SITE["planned_price"])}</del><strong>₹0</strong><span>for the first {SITE["capacity"]} students</span></div>
  <p class="offer-sub">One free founding seat per student.</p>
  {seat_meter()}
  {signup_form(prefix, track, "inline")}
</div>"""


# --------------------------------------------------------------------------- price ladder

def inr(amount: int) -> str:
    return "Free" if amount == 0 else f"₹{amount:,}"


def founding_pro_upgrade() -> int:
    """Founding students already have All Tracks free. Their Pro upgrade is the regular step from
    All Tracks to Pro minus the founding discount, rounded down to a price ending in 99."""
    step = TIER_BY_ID["pro"]["price"] - TIER_BY_ID["all"]["price"]
    price = step * (100 - FOUNDING_DISCOUNT) // 100
    return price // 100 * 100 - 1 if price >= 100 else price


def tier_nudge(t: dict) -> str:
    p = {key: tier["price"] for key, tier in TIER_BY_ID.items()}
    if t["id"] == "starter":
        return "Free for good, with no payment details."
    if t["id"] == "track":
        return "Pick the one skill your goal needs."
    if t["id"] == "all":
        return f"Only {inr(p['all'] - p['track'])} more than Single Track, for two more tracks."
    return f"{inr(p['pro'] - p['all'])} more than All Tracks, for a year of live help."


def tier_card(t: dict) -> str:
    featured = bool(t.get("badge"))
    badge = f'<span class="tier-badge">{e(t["badge"])}</span>' if featured else ""
    items = "".join(f"<li>{e(item)}</li>" for item in t["includes"])
    unit = "for good" if t["price"] == 0 else "one-time · taxes included"
    button = "button button-primary button-block" if featured else "button button-outline button-block"
    if t["id"] == "starter":
        action = cta("Start free", "pricing-starter", "foundations", button, arrow=False)
        perk = ""
    elif t["id"] == "pro":
        action = cta("Claim a founding seat", "pricing-pro", None, button, arrow=False)
        perk = f'<p class="tier-perk">Founding students upgrade for {inr(founding_pro_upgrade())}</p>'
    else:
        action = cta("Get it free as a founder", f"pricing-{t['id']}", None, button, arrow=False)
        perk = f'<p class="tier-perk">Free for the first {SITE["capacity"]} founding students</p>'
    return f"""<article class="tier-card{' is-featured' if featured else ''}" aria-labelledby="tier-{t['id']}">
  {badge}<h3 id="tier-{t['id']}">{e(t['name'])}</h3>
  <p class="tier-tagline">{e(t['tagline'])}</p>
  <p class="tier-price"><strong>{inr(t['price'])}</strong><span>{unit}</span></p>
  <p class="tier-nudge">{e(tier_nudge(t))}</p>
  <ul class="tier-list">{items}</ul>
  {perk}{action}
</article>"""


def ladder_steps() -> str:
    """The upgrade path as Apple-style step-ups: each step shows only what it adds."""
    steps, previous = [], 0
    for t in PRICE_TIERS:
        cost = "Free" if t["price"] == 0 else "+" + inr(t["price"] - previous)
        steps.append(f'<li><span class="step-name">{e(t["name"])}</span><span class="step-cost">{cost}</span></li>')
        previous = t["price"]
    return f'<ol class="ladder-steps" aria-label="Upgrade path and the extra cost of each step">{"".join(steps)}</ol>'


def tier_table() -> str:
    yes = '<span aria-hidden="true">✓</span><span class="visually-hidden">Included</span>'
    no = '<span aria-hidden="true">–</span><span class="visually-hidden">Not included</span>'
    rows = [
        ("ML Foundations track and its project", [yes, yes, yes, yes]),
        ("ML Playground and free YouTube lessons", [yes, yes, yes, yes]),
        ("Advanced tracks", [no, "1 of your choice", "All 3", "All 3"]),
        ("Projects for your portfolio", ["1", "2", "4", "4"]),
        ("Certificate for each completed track", [no, yes, yes, yes]),
        ("Live Q&amp;A sessions", [no, no, no, f"Monthly, {PRO_LIVE_MONTHS} months"]),
        ("Written feedback on your projects", [no, no, no, yes]),
        ("Price", [inr(t["price"]) for t in PRICE_TIERS]),
    ]
    head = "".join(f'<th scope="col">{e(t["name"])}</th>' for t in PRICE_TIERS)
    body = "".join(f'<tr><th scope="row">{label}</th>' + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>" for label, cells in rows)
    return f'<div class="table-scroll"><table class="tier-table"><caption class="visually-hidden">What each tier includes</caption><thead><tr><td></td>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def pricing_teaser() -> str:
    chips = "".join(f'<li><strong>{e(t["name"])}</strong><span>{inr(t["price"])}</span></li>' for t in PRICE_TIERS)
    return f"""<section class="section-tight container" aria-labelledby="ladder-title">
  <div class="pricing-teaser">
    <div><span class="eyebrow">After the Founding {SITE["capacity"]}</span><h2 id="ladder-title">Start free. <em>Step up when you're ready.</em></h2>
    <p>ML Foundations stays free for everyone. The advanced tracks start at {inr(TIER_BY_ID['track']['price'])}, and when you upgrade you only ever pay the difference.</p>
    <a class="text-link" href="/pricing/">See plans and pricing&nbsp;<span aria-hidden="true">→</span></a></div>
    <ol class="teaser-ladder" aria-label="Plans and planned prices">{chips}</ol>
  </div>
</section>"""


def course_card(t: dict, heading: str = "h3") -> str:
    tags = "".join(f"<li>{e(tag)}</li>" for tag in t["tags"])
    return f"""<article class="course-card">
  <div class="course-top"><span class="course-icon" aria-hidden="true">{t["icon"]}</span><span class="course-level">{e(t["level"])}</span></div>
  <{heading}><a href="/courses/{t["slug"]}/">{e(t["title"])}</a></{heading}>
  <p>{e(t["tagline"])}</p>
  <ul class="tag-row" aria-label="Tools and topics">{tags}</ul>
  <p class="course-project"><strong>You'll build:</strong> {e(t["project"])}</p>
  <div class="course-actions">{cta("Start free", "course-card", t["id"], "button button-outline", arrow=False)}<a class="text-link" href="/courses/{t["slug"]}/">Syllabus<span class="visually-hidden"> for {e(t["title"])}</span> <span aria-hidden="true">→</span></a></div>
</article>"""


def video_card(video_id: str) -> str:
    v = VIDEOS[video_id]
    label = "Hindi · YouTube" if v.get("hindi") else "YouTube"
    return (f'<a class="video-card" href="https://www.youtube.com/watch?v={e(video_id)}" target="_blank" rel="noopener" data-outbound="video-card">'
            f'<img src="https://i.ytimg.com/vi/{e(video_id)}/mqdefault.jpg" alt="" width="320" height="180" loading="lazy" decoding="async">'
            f'<div><strong>{e(v["title"])}</strong><span>{label} <span aria-hidden="true">↗</span><span class="visually-hidden"> (opens YouTube)</span></span></div></a>')


def video_facade(video_id: str, label: str) -> str:
    return (f'<a class="video-facade" href="https://www.youtube.com/watch?v={e(video_id)}" data-youtube="{e(video_id)}" data-title="{e(label)}">'
            f'<img src="https://i.ytimg.com/vi/{e(video_id)}/hqdefault.jpg" alt="" width="480" height="360" loading="lazy" decoding="async">'
            f'<span class="play" aria-hidden="true">▶</span><span class="video-label">{e(label)}</span></a>')


def social_links(where: str) -> str:
    links = [("YouTube", SITE["youtube"]), ("Instagram", SITE["instagram"]), ("LinkedIn", SITE["linkedin"]), ("X", SITE["x"])]
    return "".join(
        f'<li><a href="{e(href)}" target="_blank" rel="noopener" data-outbound="{e(where)}">{name} <span aria-hidden="true">↗</span></a></li>'
        for name, href in links
    )


def skills_section() -> str:
    """Skills named in current AI job posts. Company names only, never logos: they describe public
    job posts, and the section says plainly that Optimizer Step is not affiliated with these companies."""
    names = "".join(f"<li>{e(name)}</li>" for name in SKILL_COMPANIES)
    cards = []
    for skill in SKILL_DEMAND:
        t = TRACK_BY_ID[skill["track"]]
        companies = " · ".join(f"<strong>{e(c)}</strong>" for c in skill["companies"])
        cards.append(f"""<article class="skill-card">
  <span class="skill-icon" aria-hidden="true">{t["icon"]}</span>
  <h3>{e(skill["title"])}</h3>
  <p>{e(skill["text"])}</p>
  <p class="skill-seen"><span>Named in current job posts at</span>{companies}</p>
  <a class="text-link" href="/courses/{t["slug"]}/">Learn it in {e(t["title"])}&nbsp;<span aria-hidden="true">→</span></a>
</article>""")
    sources = "".join(
        f'<li><strong>{e(skill["title"])}:</strong> '
        + "; ".join(f'<a href="{e(url)}" target="_blank" rel="noopener nofollow" data-outbound="skills-source">{e(company)}, {e(title)}</a>'
                    for company, title, url in skill["sources"])
        + "</li>"
        for skill in SKILL_DEMAND
    )
    return f"""<section class="section container skills-section" id="skills" aria-labelledby="skills-title">
  <div class="section-heading"><div><span class="eyebrow">What AI teams hire for</span><h2 id="skills-title">Skills from today's AI job posts, <em>taught track by track.</em></h2></div><p>We read current AI and machine-learning job posts from the companies below. These four skill sets come up across their posts, and each one has its own track.</p></div>
  <div class="company-strip">
    <div class="company-marquee" role="region" aria-label="Companies whose job posts we checked"><ul class="company-track">{names}</ul><ul class="company-track" aria-hidden="true">{names}</ul></div>
    <button class="marquee-toggle" type="button" data-marquee-toggle aria-pressed="false" aria-label="Pause the scrolling company names">❚❚</button>
  </div>
  <div class="skill-grid">{"".join(cards)}</div>
  <details class="skills-sources"><summary>Where this comes from</summary>
    <p>On {e(SKILLS_CHECKED)} we scanned {e(SKILLS_POSTS_READ)} engineering, research and data-science job posts from the companies above, on their official job boards, and noted which skills each post names. One example post for each company listed:</p>
    <ul>{sources}</ul>
    <p>Job posts change often, so some of these links will close over time. Company names only describe their public job posts. Optimizer Step is independent and is not affiliated with, sponsored by or endorsed by any company named here. All trademarks belong to their owners.</p>
  </details>
</section>"""


def faq_html() -> str:
    items = "".join(
        f"<details><summary>{e(q)}</summary><div><p>{a.format(**SITE)}</p></div></details>" for q, a in FAQS
    )
    return f'<div class="faq-list">{items}</div>'


def cta_band(eyebrow: str, title: str, text: str, label: str, where: str, track: str | None = None, extra: str = "") -> str:
    return f"""<section class="section-tight"><div class="container"><div class="cta-band">
  <div><span class="eyebrow">{e(eyebrow)}</span><h2>{title}</h2><p>{text}</p></div>
  <div class="cta-actions">{cta(label, where, track)}{extra}<small data-seats-short>First {SITE["capacity"]} students join free</small></div>
</div></div></section>"""


def breadcrumbs(items: list[tuple[str, str | None]]) -> str:
    parts = []
    for name, href in items:
        parts.append(f'<li><a href="{href}">{e(name)}</a></li>' if href else f'<li aria-current="page">{e(name)}</li>')
    return f'<nav class="breadcrumbs" aria-label="Breadcrumb"><ol>{"".join(parts)}</ol></nav>'


# --------------------------------------------------------------------------- structured data

ORG_ID = URL + "/#organization"
PERSON_ID = URL + "/#instructor"


def org_schema() -> dict:
    return {
        "@type": "EducationalOrganization",
        "@id": ORG_ID,
        "name": SITE["name"],
        "alternateName": "OptimizerStep",
        "description": "Hands-on AI and machine learning courses and free YouTube lessons, from Python and ML foundations to deep learning, NLP and RAG.",
        "url": URL + "/",
        "logo": URL + "/assets/img/icon-512.png",
        "email": SITE["email"],
        "sameAs": [SITE["youtube"], SITE["instagram"], SITE["x"]],
        "founder": {"@id": PERSON_ID},
    }


def person_schema() -> dict:
    return {
        "@type": "Person",
        "@id": PERSON_ID,
        "name": SITE["instructor"],
        "jobTitle": "Founder and instructor",
        "image": URL + "/assets/img/venkatesh-480.webp",
        "worksFor": {"@id": ORG_ID},
        "sameAs": [SITE["youtube"], SITE["linkedin"], SITE["x"], SITE["instagram"]],
    }


def breadcrumb_schema(items: list[tuple[str, str]]) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": URL + path} for i, (name, path) in enumerate(items)
        ],
    }


def jsonld(nodes: list[dict]) -> str:
    if not nodes:
        return ""
    data = {"@context": "https://schema.org", "@graph": nodes}
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'<script type="application/ld+json">{text}</script>'


# --------------------------------------------------------------------------- layout

THEME_BOOT = ('<script>document.documentElement.classList.add("js");try{if(localStorage.getItem("optimizerstep-theme-v1")==="light")'
              'document.documentElement.setAttribute("data-theme","light")}catch(e){}</script>')

NAV = [("/courses/", "Courses", "courses"), ("/playground/", "Playground", "playground"), ("/pricing/", "Pricing", "pricing"), ("/#instructor", "Instructor", None), ("/#faq", "FAQ", None)]


def header(section: str | None) -> str:
    links = "".join(
        f'<a href="{href}"{" aria-current=\"page\"" if key and key == section else ""}>{label}</a>' for href, label, key in NAV
    )
    return f"""<header class="site-header">
  <div class="container nav-inner">
    <a class="brand" href="/" aria-label="Optimizer Step home"><img src="{asset("img/emblem-72.webp")}" srcset="{asset("img/emblem-72.webp")} 1x, {asset("img/emblem-144.webp")} 2x" width="36" height="36" alt=""><span>optimizer<span class="brand-muted">step</span><span class="brand-period">.</span></span></a>
    <nav class="site-nav" aria-label="Main">{links}</nav>
    <div class="nav-actions"><button class="theme-toggle" type="button" data-theme-toggle aria-label="Switch to light mode" aria-pressed="false">◐</button>{cta("Claim free seat", "header", cls="button button-primary button-small", arrow=False)}</div>
  </div>
</header>"""


def announcement() -> str:
    return (f'<div class="announcement"><span class="spark" aria-hidden="true">✦</span><strong>Founding 100</strong>'
            f'<span class="announcement-text" data-seats-short>First {SITE["capacity"]} students join free</span>'
            f'<button type="button" class="announcement-cta" data-enroll data-cta="announcement"><span data-cta-label="Claim yours">Claim yours</span> <span aria-hidden="true">→</span></button></div>')


def footer() -> str:
    track_links = "".join(f'<li><a href="/courses/{t["slug"]}/">{e(t["title"])}</a></li>' for t in TRACKS)
    return f"""<footer class="site-footer">
  <div class="container footer-inner">
    <div class="footer-brand">
      <a class="brand" href="/" aria-label="Optimizer Step home"><img src="{asset("img/emblem-72.webp")}" width="36" height="36" alt="" loading="lazy"><span>optimizer<span class="brand-muted">step</span><span class="brand-period">.</span></span></a>
      <p>{e(SITE["tagline"])} Hands-on AI and machine learning courses from the Optimizer Step YouTube channel.</p>
      <ul class="social-row" aria-label="Optimizer Step on social media">{social_links("footer")}</ul>
    </div>
    <div class="footer-col"><h2>Learn</h2><ul><li><a href="/courses/">All courses</a></li><li><a href="/playground/">ML Playground</a></li><li><a href="{e(SITE["youtube"])}" target="_blank" rel="noopener" data-outbound="footer">Free YouTube lessons</a></li></ul></div>
    <div class="footer-col"><h2>Tracks</h2><ul>{track_links}</ul></div>
    <div class="footer-col"><h2>Optimizer Step</h2><ul><li><a href="/#instructor">Meet the instructor</a></li><li><a href="/#faq">FAQ</a></li><li><a href="mailto:{e(SITE["email"])}">Contact: {e(SITE["email"])}</a></li><li><a href="/privacy/">Privacy policy</a></li><li><a href="/terms/">Terms</a></li></ul></div>
  </div>
  <div class="container footer-bottom"><span>© <span data-year>{date.today().year}</span> Optimizer Step. All rights reserved.</span><span>Free founding seats for the first {SITE["capacity"]} students.</span></div>
</footer>"""


def signup_dialog() -> str:
    return f"""<dialog id="signupDialog" class="signup-dialog" aria-labelledby="signupDialogTitle">
  <div class="dialog-inner">
    <button class="dialog-close" type="button" data-dialog-close aria-label="Close">×</button>
    <span class="eyebrow">Founding 100 · Free</span>
    <h2 id="signupDialogTitle">Claim your free seat.</h2>
    <p>All four launch tracks, free for the first {SITE["capacity"]} students. No payment details needed.</p>
    <p class="dialog-seats" data-seats-text>{SITE["capacity"]} free founding seats. First come, first served.</p>
    {signup_form("m")}
  </div>
</dialog>"""


def sticky_cta() -> str:
    return (f'<div class="sticky-cta" data-sticky-cta hidden aria-hidden="true"><div><strong>Free founding seat</strong>'
            f'<span data-seats-short>First {SITE["capacity"]} students join free</span></div>'
            f'<button class="button button-primary" type="button" data-enroll data-cta="sticky" tabindex="-1"><span data-cta-label="Claim free seat">Claim free seat</span></button></div>')


def live_notice() -> str:
    # Filled by site.js from real, anonymous signups (seat, track, experience, time); never names.
    return ('<aside class="live-notice" data-live-notice hidden aria-label="Recent signups">'
            '<span class="live-dot" aria-hidden="true"></span>'
            '<p class="live-body"><strong data-notice-title></strong><span data-notice-meta></span></p>'
            '<button class="live-cta" type="button" data-enroll data-cta="live-notice"><span data-cta-label="Claim yours">Claim yours</span></button>'
            '<button class="live-close" type="button" data-notice-close aria-label="Hide signup notices">×</button></aside>')


def layout(page: dict) -> str:
    path = page["path"]
    canonical = URL + path
    title = page["title"]
    description = page["description"]
    og_title = page.get("og_title", title)
    robots = '<meta name="robots" content="noindex, follow">' if page.get("noindex") else '<meta name="robots" content="index, follow, max-image-preview:large">'
    preconnect = ""
    if config_endpoint():
        preconnect = ('<link rel="preconnect" href="https://script.google.com" crossorigin>'
                      '<link rel="preconnect" href="https://script.googleusercontent.com" crossorigin>')
    scripts = [asset("js/config.js"), asset("js/site.js")] + [asset(f"js/{name}.js") for name in page.get("scripts", [])]
    script_tags = "".join(f'<script defer src="{src}"></script>' for src in scripts)
    body_attrs = page.get("body_attrs", "")
    show_marketing = page.get("marketing", True)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
{robots}
<meta name="facebook-domain-verification" content="{e(SITE["facebook_domain_verification"])}">
<link rel="canonical" href="{e(canonical)}">
<meta name="theme-color" content="#080b13">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Optimizer Step">
<meta property="og:locale" content="en_IN">
<meta property="og:title" content="{e(og_title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:image" content="{URL}/assets/img/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Optimizer Step: learn AI and machine learning by building it">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="{e(SITE["x_handle"])}">
<meta name="twitter:title" content="{e(og_title)}">
<meta name="twitter:description" content="{e(description)}">
<meta name="twitter:image" content="{URL}/assets/img/og-image.jpg">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" sizes="192x192" href="{asset("img/icon-192.png")}">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
{preconnect}
<link rel="stylesheet" href="{asset("css/site.css")}">
{THEME_BOOT}
{jsonld(page.get("schema", []))}
{script_tags}
</head>
<body{(" " + body_attrs) if body_attrs else ""}>
<a class="skip-link" href="#main">Skip to content</a>
{announcement() if show_marketing else ""}
{header(page.get("section"))}
<main id="main" tabindex="-1">
{page["body"]}
</main>
{footer()}
{signup_dialog()}
{sticky_cta() if show_marketing else ""}
{live_notice() if show_marketing else ""}
</body>
</html>
"""


# --------------------------------------------------------------------------- pages

HERO_VISUAL = """<div class="hero-visual" data-hero-visual role="img" aria-label="A model training run: the loss falls from 0.31 to 0.0248 and accuracy reaches 97.6 percent">
  <div class="visual-top"><span class="window-dots"><i></i><i></i><i></i></span><span>model_training.py</span><span class="visual-status" data-badge>✓ CONVERGED</span></div>
  <div class="visual-code"><span class="code-line"><b>01</b> <span class="code-purple">model</span> = PolynomialRegressor(degree=<span class="code-orange">2</span>)</span><span class="code-line"><b>02</b> <span class="code-purple">model</span>.fit(X_train, y_train)</span><span class="code-line"><b>03</b> <span class="code-muted"># watch every optimizer step</span></span></div>
  <div class="chart-wrap"><div class="chart-title"><span>Training loss</span><span>epoch <span data-epoch>100</span> / 100</span></div>
    <svg viewBox="0 0 500 210" aria-hidden="true" focusable="false"><defs><linearGradient id="lossFill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#875dff" stop-opacity=".3"/><stop offset="1" stop-color="#875dff" stop-opacity="0"/></linearGradient></defs><path d="M0 35 H500 M0 85 H500 M0 135 H500 M0 185 H500" stroke="#2b3146" stroke-width="1"/><path class="loss-area" d="M12 28 C45 45 66 69 94 88 S145 132 174 145 S240 164 275 174 S355 181 390 184 S457 186 488 186 L488 205 L12 205Z" fill="url(#lossFill)"/><path class="loss-line" pathLength="1" d="M12 28 C45 45 66 69 94 88 S145 132 174 145 S240 164 275 174 S355 181 390 184 S457 186 488 186" fill="none" stroke="#a78bfa" stroke-width="3" stroke-linecap="round"/><circle class="loss-dot" cx="488" cy="186" r="5" fill="#c4b5fd"/></svg>
  </div>
  <div class="visual-bottom"><span><small>Loss</small><strong><span data-loss>0.0248</span> <span class="delta" data-delta>↓ 92%</span></strong></span><span><small>Accuracy</small><strong data-acc>97.6%</strong></span><span><small>Status</small><strong class="mint" data-status>Converged</strong></span></div>
  <div class="float-card"><span>✦</span><div><strong>Aha! moment</strong><small>Now you know why it works.</small></div></div>
</div>"""


def page_home() -> dict:
    cards = "".join(course_card(t) for t in TRACKS)
    faq_schema = {
        "@type": "FAQPage",
        "@id": URL + "/#faq",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a.format(**SITE))}} for q, a in FAQS
        ],
    }
    website = {"@type": "WebSite", "@id": URL + "/#website", "url": URL + "/", "name": SITE["name"],
               "alternateName": ["OptimizerStep", "optimizerstep.com"], "inLanguage": "en-IN", "publisher": {"@id": ORG_ID}}
    body = f"""
<section class="container hero">
  <div class="hero-copy">
    <span class="eyebrow">Free founding seats · AI &amp; ML courses</span>
    <h1>Learn AI by <em>building it.</em></h1>
    <p class="hero-lead">From your first regression model to production-minded RAG: learn machine learning through code, visual experiments and projects you can explain. The first {SITE["capacity"]} students join free.</p>
    <div class="hero-actions" data-hero-cta>{cta("Claim my free seat", "hero")}<a class="button button-outline" href="/playground/">Try the ML Playground</a></div>
    <div class="hero-trust"><img src="{asset("img/venkatesh-96.webp")}" width="48" height="48" alt=""><p>Taught by <strong>{e(SITE["instructor"])}</strong>, creator of the <a class="text-link" href="{e(SITE["youtube"])}" target="_blank" rel="noopener" data-outbound="hero-trust">Optimizer Step YouTube channel</a>: {SITE["subscribers"]} subscribers, {SITE["videos"]} videos.</p></div>
    <ul class="hero-points"><li>Beginner to builder</li><li>Real projects</li><li>No payment details</li></ul>
  </div>
  {HERO_VISUAL}
</section>
<section class="proof-strip" aria-label="Optimizer Step in numbers"><div class="container proof-inner">
  <div class="proof-item"><strong>{SITE["subscribers"]}</strong><span>YouTube subscribers</span></div>
  <div class="proof-item"><strong>{SITE["videos"]}</strong><span>free videos on the channel</span></div>
  <div class="proof-item"><strong>4 tracks</strong><span>from regression to RAG</span></div>
  <div class="proof-item"><strong>₹0</strong><span>for the first {SITE["capacity"]} students</span></div>
</div></section>
{skills_section()}
<section class="section container" id="courses" aria-labelledby="courses-title">
  <div class="section-heading"><div><span class="eyebrow">The learning path</span><h2 id="courses-title">Go from “what is ML?” <em>to “I built that.”</em></h2></div><p>Four focused tracks, each ending in a project you can show and explain. Founding students get every launch track free.</p></div>
  <div class="course-grid">{cards}</div>
</section>
<section class="section container" id="approach" aria-labelledby="approach-title">
  <div class="section-heading"><div><span class="eyebrow">Why this works</span><h2 id="approach-title">Less passive watching. <em>More doing.</em></h2></div><p>Every concept becomes something you can run, tune, break and rebuild.</p></div>
  <ol class="method-grid">
    <li><span class="method-number">01</span><h3>See the mechanism</h3><p>Every idea starts with a visual, hands-on experiment, from loss curves to decision boundaries, so the maths makes sense.</p></li>
    <li><span class="method-number">02</span><h3>Write the code</h3><p>Build each algorithm in Python yourself, then move to the tools developers use: Scikit-learn, PyTorch and vector search.</p></li>
    <li><span class="method-number">03</span><h3>Ship a project</h3><p>Finish every track with a concrete project you can show and explain.</p></li>
  </ol>
  <div class="playground-promo">
    <div><span class="eyebrow">Try before you enrol</span><h3>Open the lab. Move the model.</h3><p>Four free experiments that run in your browser: gradient descent, decision boundaries, k-means and attention. No sign-up needed.</p><a class="button button-outline" href="/playground/">Open the ML Playground <span class="arrow" aria-hidden="true">→</span></a></div>
    <div class="promo-graphic" aria-hidden="true"><span class="orb orb-one"></span><span class="orb orb-two"></span><span class="orb orb-three"></span><span class="promo-line"></span></div>
  </div>
</section>
<section class="section offer-section" id="join" aria-labelledby="join-title">
  <div class="container offer-grid">
    <div class="offer-copy">
      <span class="eyebrow">The Founding 100</span>
      <h2 id="join-title">Your first step <em>is on us.</em></h2>
      <p>We're opening the Optimizer Step course platform with {SITE["capacity"]} free founding seats. Claim one now and you're in when the tracks open.</p>
      <ul class="check-list">
        <li>All four launch tracks, free <span>(planned price {e(SITE["planned_price"])})</span></li>
        <li>Project-first lessons, from regression to RAG</li>
        <li>Your track's start date by email, before it opens</li>
        <li>The ML Playground and YouTube lessons, free while you wait</li>
      </ul>
    </div>
    {offer_card("j")}
  </div>
</section>
{pricing_teaser()}
<section class="section container" id="instructor" aria-labelledby="instructor-title">
  <div class="instructor-card">
    <figure class="instructor-photo">
      <img src="{asset("img/venkatesh-480.webp")}" width="480" height="600" alt="{e(SITE["instructor"])}, founder and instructor at Optimizer Step" loading="lazy" decoding="async">
      <figcaption><strong>{e(SITE["instructor"])}</strong>Founder and instructor, Optimizer Step</figcaption>
    </figure>
    <div class="instructor-body">
      <span class="eyebrow">Meet your instructor</span>
      <h2 id="instructor-title">Learn from the creator of the Optimizer Step channel.</h2>
      <p>{e(SITE["instructor_first"])} runs the Optimizer Step YouTube channel: {SITE["videos"]} videos that take AI and machine learning apart, from Python and the maths behind ML to backpropagation, optimizers and RAG pipelines built from scratch.</p>
      <p>Every lesson follows the same idea: understand the concept, see it visually, then build it in code. The courses take the same approach, with more depth, structure and projects.</p>
      <ul class="stat-row"><li><strong>{SITE["subscribers"]}</strong> YouTube subscribers</li><li><strong>{SITE["videos"]}</strong> videos</li><li><strong>Python · PyTorch · RAG</strong></li></ul>
      <ul class="social-row" aria-label="Follow Optimizer Step">{social_links("instructor")}</ul>
      <div class="instructor-video">{video_facade("D37cTKjtXvU", "Watch: Welcome to Optimizer Step")}</div>
    </div>
  </div>
</section>
<section class="section container faq-section" id="faq" aria-labelledby="faq-title">
  <div class="faq-aside"><span class="eyebrow">Good to know</span><h2 id="faq-title">Questions, answered.</h2><p>Something else? Email <a class="text-link" href="mailto:{e(SITE["email"])}">{e(SITE["email"])}</a>.</p></div>
  {faq_html()}
</section>
{cta_band("Founding 100", "Ready to take your first <em>optimizer step?</em>", "Claim a free founding seat in under a minute. No payment details.", "Claim my free seat", "final-band")}
"""
    return {
        "path": "/",
        "out": "index.html",
        "title": "Learn AI & Machine Learning by Building It | Optimizer Step",
        "og_title": "Learn AI by building it: free founding seats | Optimizer Step",
        "description": f"Hands-on AI and machine learning courses: regression to RAG, taught with code, visual experiments and real projects. The first {SITE['capacity']} students join free.",
        "body": body,
        "scripts": ["hero"],
        "schema": [org_schema(), website, person_schema(), faq_schema],
        "body_attrs": 'class="page-home"',
    }


def page_courses() -> dict:
    cards = "".join(course_card(t, "h2") for t in TRACKS)
    path = """<ol class="path-list">
  <li><small>Start here</small><strong>ML Foundations</strong><span>The core ideas, gradient descent and honest evaluation.</span></li>
  <li><small>Then</small><strong>Deep Learning &amp; Vision</strong><span>Neural networks, PyTorch and convolutional models.</span></li>
  <li><small>Or</small><strong>NLP &amp; Transformers</strong><span>Tokens, embeddings, attention and text classifiers.</span></li>
  <li><small>Finally</small><strong>Build with RAG</strong><span>Grounded LLM applications on your own documents.</span></li>
</ol>"""
    item_list = {
        "@type": "ItemList",
        "name": "Optimizer Step courses",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": f'{URL}/courses/{t["slug"]}/', "name": t["title"]} for i, t in enumerate(TRACKS)
        ],
    }
    body = f"""
<section class="container page-hero">
  {breadcrumbs([("Home", "/"), ("Courses", None)])}
  <p class="eyebrow" style="margin-top:28px">Four tracks · Free for founding students</p>
  <h1>AI and machine learning courses, <em>built around projects.</em></h1>
  <p class="lead">Four tracks take you from your first regression model to retrieval-augmented generation. Each one ends in a project you can show. The first {SITE["capacity"]} founding students get every launch track free.</p>
  <div class="hero-actions" data-hero-cta>{cta("Claim my free seat", "courses-hero")}<a class="button button-outline" href="/playground/">Try the ML Playground</a></div>
</section>
<section class="container" aria-label="Course tracks"><div class="course-grid">{cards}</div></section>
<section class="section container" aria-labelledby="path-title">
  <div class="section-intro"><span class="eyebrow">Suggested path</span><h2 id="path-title">Not sure where to start?</h2><p>Start with ML Foundations unless you already train models. Pick Deep Learning or NLP next, then finish with RAG. Choose "Not sure yet" when you sign up and we'll help you pick.</p></div>
  {path}
</section>
{cta_band("Founding 100", "One seat. <em>Every launch track.</em>", f"Claim a free founding seat and get all four tracks free. Planned price {e(SITE['planned_price'])}.", "Claim my free seat", "courses-band")}
"""
    return {
        "path": "/courses/",
        "out": "courses/index.html",
        "title": "AI & Machine Learning Courses: From ML to RAG | Optimizer Step",
        "description": "Four project-first AI and machine learning tracks: ML Foundations, Deep Learning & Vision, NLP & Transformers and Build with RAG. Free for the first 100 founding students.",
        "body": body,
        "section": "courses",
        "schema": [org_schema(), item_list, breadcrumb_schema([("Home", "/"), ("Courses", "/courses/")])],
    }


def track_price_text(t: dict) -> str:
    """What this track costs: ML Foundations is the free Starter course; the others are paid after the founding cohort."""
    if t["id"] == "foundations":
        return '<strong>Free</strong> for everyone: it is the <a class="text-link" href="/pricing/">Starter</a> course'
    return (f'<strong>Free</strong> for the first {SITE["capacity"]} founding students. Then {inr(TIER_BY_ID["track"]["price"])} for this track, '
            f'or {inr(TIER_BY_ID["all"]["price"])} for <a class="text-link" href="/pricing/">All Tracks</a>')


def page_track(t: dict) -> dict:
    lab = LAB_BY_SLUG[t["lab"]]
    modules = "".join(f"<li><h3>{e(title)}</h3><p>{e(text)}</p></li>" for title, text in t["modules"])
    badges = "".join(f'<li class="badge">{e(tag)}</li>' for tag in t["tags"])
    videos = "".join(video_card(v) for v in t["videos"])
    others = "".join(
        f'<a href="/courses/{o["slug"]}/"><small>{e(o["level"])}</small><strong>{e(o["title"])}</strong></a>' for o in TRACKS if o["id"] != t["id"]
    )
    course_schema = {
        "@type": "Course",
        "@id": f'{URL}/courses/{t["slug"]}/#course',
        "name": t["title"],
        "description": t["intro"],
        "url": f'{URL}/courses/{t["slug"]}/',
        "provider": {"@id": ORG_ID},
        "instructor": {"@id": PERSON_ID},
        "educationalLevel": t["level"],
        "teaches": [title for title, _ in t["modules"]],
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "INR", "category": "Free",
                   "description": f'Free for the first {SITE["capacity"]} founding students', "url": f'{URL}/courses/{t["slug"]}/'},
    }
    crumbs = [("Home", "/"), ("Courses", "/courses/"), (t["title"], f'/courses/{t["slug"]}/')]
    body = f"""
<section class="container page-hero">
  {breadcrumbs([("Home", "/"), ("Courses", "/courses/"), (t["title"], None)])}
  <p class="eyebrow" style="margin-top:28px">{e(t["level"])} track · Free for founding students</p>
  <h1>{e(t["title"])}</h1>
  <p class="lead">{e(t["intro"])}</p>
  <ul class="badge-row" aria-label="Tools and topics">{badges}</ul>
  <div class="hero-actions" data-hero-cta>{cta("Start " + t["title"] + " free", "track-hero", t["id"])}<a class="button button-outline" href="#syllabus">See the syllabus</a></div>
</section>
<section class="container" id="syllabus" aria-labelledby="syllabus-title">
  <div class="track-layout">
    <div>
      <div class="content-block">
        <h2 class="subhead" id="syllabus-title">What you'll learn</h2>
        <ol class="module-list">{modules}</ol>
        <div class="project-card"><span class="eyebrow">Your project</span><h3>{e(t["project"])}</h3><p>{e(t["project_detail"])}</p></div>
      </div>
      <div class="content-block">
        <h2 class="subhead">Start learning today, free</h2>
        <p class="muted">These free lessons from the Optimizer Step YouTube channel cover ideas from this track. Watch them while your track gets ready.</p>
        <div class="video-grid">{videos}</div>
        <a class="lab-link-card" href="/playground/{lab["slug"]}/"><span class="icon" aria-hidden="true">◎</span><span><strong>Try it in the ML Playground: {e(lab["name"])}</strong><span>{e(lab["card"])}</span></span></a>
      </div>
    </div>
    <aside class="side-card" aria-label="Track details">
      <h2>Track details</h2>
      <dl>
        <div><dt>Level</dt><dd>{e(t["level"])}</dd></div>
        <div><dt>Who it's for</dt><dd>{e(t["audience"])}</dd></div>
        <div><dt>Recommended background</dt><dd>{e(t["background"])}</dd></div>
        <div><dt>Format</dt><dd>Online, project-first lessons</dd></div>
        <div><dt>Price</dt><dd>{track_price_text(t)}</dd></div>
      </dl>
      {cta("Claim my free seat", "track-sidebar", t["id"], "button button-primary button-block")}
      <p class="form-fineprint" style="margin-top:12px" data-seats-short>First {SITE["capacity"]} students join free</p>
    </aside>
  </div>
</section>
<section class="section offer-section" id="join" aria-labelledby="join-title" style="margin-top:96px">
  <div class="container offer-grid">
    <div class="offer-copy">
      <span class="eyebrow">Founding 100</span>
      <h2 id="join-title">Claim your free seat in <em>{e(t["title"])}.</em></h2>
      <p>Founding students get this track and every other launch track free, plus the start date by email before it opens.</p>
      <ul class="check-list">
        <li>{e(t["title"])} and all other launch tracks, free <span>(planned price {e(SITE["planned_price"])})</span></li>
        <li>A project you can show: {e(t["project"][0].lower() + t["project"][1:])}</li>
        <li>Free YouTube lessons and the ML Playground while you wait</li>
      </ul>
    </div>
    {offer_card("t", t["id"])}
  </div>
</section>
<section class="section-tight container" aria-labelledby="other-title"><h2 class="subhead" id="other-title">Explore the other tracks</h2><div class="other-tracks">{others}</div></section>
"""
    return {
        "path": f'/courses/{t["slug"]}/',
        "out": f'courses/{t["slug"]}/index.html',
        "title": f'{t["seo_title"]} | Optimizer Step',
        "og_title": f'{t["title"]}: free for founding students | Optimizer Step',
        "description": f'{t["intro"]} Free for the first {SITE["capacity"]} founding students.'[:300],
        "body": body,
        "section": "courses",
        "schema": [org_schema(), person_schema(), course_schema, breadcrumb_schema(crumbs)],
        "body_attrs": f'data-track-page="{e(t["id"])}"',
    }


def page_playground() -> dict:
    cards = "".join(
        f'<a class="lab-card" href="/playground/{lab["slug"]}/"><span class="eyebrow no-line">Lab {lab["number"]} · {e(lab["chip"].title())}</span>'
        f'<h2>{e(lab["name"][0].upper() + lab["name"][1:])}</h2><p>{e(lab["card"])}</p><span class="text-link">Open the lab <span aria-hidden="true">→</span></span></a>'
        for lab in LABS
    )
    item_list = {
        "@type": "ItemList",
        "name": "ML Playground labs",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": f'{URL}/playground/{lab["slug"]}/', "name": lab["name"]} for i, lab in enumerate(LABS)
        ],
    }
    body = f"""
<section class="container page-hero">
  {breadcrumbs([("Home", "/"), ("ML Playground", None)])}
  <p class="eyebrow" style="margin-top:28px">The ML Playground · Free</p>
  <h1>Machine learning, <em>in your hands.</em></h1>
  <p class="lead">Change a parameter. Move a point. Watch the model respond. Four free labs that run entirely in your browser: no sign-up, no setup, no API keys.</p>
  <p class="playground-badge">100% in your browser<span>Works on your phone too.</span></p>
</section>
<section class="container" aria-label="Labs"><div class="lab-cards">{cards}</div></section>
{cta_band("Go deeper", "Understand the maths <em>behind every lab.</em>", "The courses turn these experiments into real code and projects. Free for the first 100 founding students.", "Claim my free seat", "playground-band")}
"""
    return {
        "path": "/playground/",
        "out": "playground/index.html",
        "title": "ML Playground: Free Machine Learning Visualizers | Optimizer Step",
        "description": "Free, interactive machine learning labs in your browser: gradient descent, decision boundaries, k-means clustering and transformer attention. No sign-up needed.",
        "body": body,
        "section": "playground",
        "schema": [org_schema(), item_list, breadcrumb_schema([("Home", "/"), ("ML Playground", "/playground/")])],
    }


def page_lab(lab: dict) -> dict:
    track = TRACK_BY_ID[lab["track"]]
    nav = "".join(
        f'<a href="/playground/{other["slug"]}/"{" aria-current=\"page\"" if other is lab else ""}>{e(other["nav"])}</a>' for other in LABS
    )
    videos = "".join(video_card(v) for v in lab["videos"])
    schema = {
        "@type": "LearningResource",
        "name": lab["name"][0].upper() + lab["name"][1:],
        "description": lab["description"],
        "url": f'{URL}/playground/{lab["slug"]}/',
        "learningResourceType": "Interactive simulation",
        "isAccessibleForFree": True,
        "provider": {"@id": ORG_ID},
    }
    crumbs = [("Home", "/"), ("ML Playground", "/playground/"), (lab["nav"], f'/playground/{lab["slug"]}/')]
    body = f"""
<section class="container page-hero">
  {breadcrumbs([("Home", "/"), ("ML Playground", "/playground/"), (lab["nav"], None)])}
  <p class="eyebrow" style="margin-top:28px">ML Playground · Lab {lab["number"]}</p>
  <h1>{lab["h1"]}</h1>
  <p class="lead">{e(lab["lead"])}</p>
</section>
<section class="container" aria-label="Interactive lab" data-hero-cta>
  <nav class="lab-nav" aria-label="Playground labs">{nav}</nav>
  {LAB_PANELS[lab["id"]]}
</section>
<section class="section container explainer" aria-label="How it works">
  <div class="prose">{LAB_EXPLAINERS[lab["id"]]}</div>
  <aside class="side-card" aria-label="Related lessons">
    <h2>Watch the lesson</h2>
    <div class="video-grid">{videos}</div>
  </aside>
</section>
{cta_band("Go deeper", f"Learn this properly in <em>{e(track['title'])}.</em>", f"The {e(track['title'])} track turns this lab into real code and a project you can show. Free for the first {SITE['capacity']} founding students.", "Claim my free seat", "lab-band", track["id"], f'<a class="text-link" href="/courses/{track["slug"]}/">See the {e(track["title"])} syllabus</a>')}
"""
    return {
        "path": f'/playground/{lab["slug"]}/',
        "out": f'playground/{lab["slug"]}/index.html',
        "title": f'{lab["title"]} | Optimizer Step',
        "description": lab["description"],
        "body": body,
        "section": "playground",
        "scripts": ["playground"],
        "schema": [org_schema(), schema, breadcrumb_schema(crumbs)],
        "body_attrs": f'data-lab="{e(lab["id"])}"',
    }


def faq_list(items: list[tuple[str, str]]) -> str:
    rows = "".join(f"<details><summary>{e(q)}</summary><div><p>{a}</p></div></details>" for q, a in items)
    return f'<div class="faq-list">{rows}</div>'


def page_pricing() -> dict:
    cap = SITE["capacity"]
    upgrade = inr(founding_pro_upgrade())
    pro_step = inr(TIER_BY_ID["pro"]["price"] - TIER_BY_ID["all"]["price"])
    cards = "".join(tier_card(t) for t in PRICE_TIERS)
    faqs = [
        ("Is Starter really free for good?", "Yes. ML Foundations, its project, the ML Playground and the YouTube lessons stay free for everyone, with no payment details."),
        ("When can I buy a paid tier?", "The paid tiers open with the tracks, which open in stages. Founding students hear first, by email. Until then, the best deal is a free founding seat."),
        ("Do the prices include taxes?", "Yes. The price you see is the price you pay, including all taxes. Nothing is added at checkout."),
        ("Is it a subscription?", "No. Every tier is a one-time payment, and nothing renews automatically."),
        ("Can I upgrade later?", "Yes, at any time. Everything you have already paid counts towards the higher tier, so you only pay the difference."),
        ("What do founding students get?", f"All Tracks free (planned price {e(SITE['price_all'])}), a Pro upgrade for {upgrade} instead of {pro_step}, and {FOUNDING_DISCOUNT}% off any future paid track."),
        ("How do the Pro live sessions work?", f"Pro includes a live Q&amp;A session every month for {PRO_LIVE_MONTHS} months from the date you buy it, plus written feedback on each of your track projects."),
        ("What about refunds?", "The refund terms will be shown clearly before you pay."),
    ]
    faq_schema = {
        "@type": "FAQPage",
        "@id": URL + "/pricing/#faq",
        "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": strip_tags(html.unescape(a))}} for q, a in faqs],
    }
    body = f"""
<section class="container page-hero">
  {breadcrumbs([("Home", "/"), ("Pricing", None)])}
  <p class="eyebrow" style="margin-top:28px">Pricing · planned prices</p>
  <h1>Start free. <em>Step up when you're ready.</em></h1>
  <p class="lead">ML Foundations is free for everyone, for good. When you want more, each step up costs a little and adds a lot, and you only ever pay the difference.</p>
  <div class="founding-callout">
    <div><strong>Right now: the Founding {cap}</strong><p>The first {cap} students get All Tracks free (planned price {e(SITE['price_all'])}), can upgrade to Pro for {upgrade}, and keep {FOUNDING_DISCOUNT}% off every future paid track.</p><p class="dialog-seats" data-seats-text>{cap} free founding seats. First come, first served.</p></div>
    {cta("Claim my free seat", "pricing-hero")}
  </div>
</section>
<section class="container" aria-labelledby="plans-title">
  <h2 class="visually-hidden" id="plans-title">Plans</h2>
  <div class="tier-grid">{cards}</div>
  <p class="tier-footnote">Planned prices in Indian rupees, including all taxes. The paid tiers open with the tracks, and founding students hear first.</p>
</section>
<section class="section container" aria-labelledby="path-title">
  <div class="section-heading"><div><span class="eyebrow">How upgrading works</span><h2 id="path-title">Every step is small. <em>You only pay the difference.</em></h2></div><p>Start with Starter. Whatever you have paid counts towards the next tier, so moving up costs only what the new tier adds.</p></div>
  {ladder_steps()}
</section>
<section class="section-tight container" aria-labelledby="compare-title">
  <h2 class="subhead" id="compare-title">Compare the plans</h2>
  {tier_table()}
</section>
<section class="section container faq-section" id="faq" aria-labelledby="pricing-faq-title">
  <div class="faq-aside"><span class="eyebrow">Pricing questions</span><h2 id="pricing-faq-title">Good to know.</h2><p>Anything else? Email <a class="text-link" href="mailto:{e(SITE["email"])}">{e(SITE["email"])}</a>.</p></div>
  {faq_list(faqs)}
</section>
{cta_band("Founding " + str(cap), "The best price is <em>free.</em>", f"Claim a founding seat now: All Tracks free and {FOUNDING_DISCOUNT}% off every upgrade.", "Claim my free seat", "pricing-band")}
"""
    p = {key: tier["price"] for key, tier in TIER_BY_ID.items()}
    return {
        "path": "/pricing/",
        "out": "pricing/index.html",
        "title": f"Pricing: Free ML Course, Advanced Tracks from {inr(p['track'])} | Optimizer Step",
        "og_title": "Start free, step up when you're ready | Optimizer Step pricing",
        "description": (f"ML Foundations is free for everyone. Advanced AI/ML tracks from {inr(p['track'])}, All Tracks {inr(p['all'])}, "
                        f"Pro with monthly live Q&A {inr(p['pro'])}. One-time prices including taxes; upgrade by paying only the difference."),
        "body": body,
        "section": "pricing",
        "schema": [org_schema(), faq_schema, breadcrumb_schema([("Home", "/"), ("Pricing", "/pricing/")])],
    }


def page_privacy() -> dict:
    email = e(SITE["email"])
    body = f"""
<article class="legal narrow">
  {breadcrumbs([("Home", "/"), ("Privacy policy", None)])}
  <h1>Privacy policy</h1>
  <p class="updated">Last updated: {e(SITE["policy_updated"])}</p>
  <p>This policy explains what personal data Optimizer Step ("we", "us") collects on www.optimizerstep.com, why we collect it and what you can do about it. We collect as little as we can and we never sell your data.</p>

  <h2>Who is responsible</h2>
  <p>Optimizer Step, run by {e(SITE["instructor"])}, is responsible for your data. For any privacy question or request, email <a href="mailto:{email}">{email}</a>.</p>

  <h2>What we collect</h2>
  <table>
    <thead><tr><th>When</th><th>What</th></tr></thead>
    <tbody>
      <tr><td>You claim a founding seat or join the waitlist</td><td>Your name, email address, chosen track and experience level, the page you signed up on and whether you used a phone or a computer.</td></tr>
      <tr><td>You arrive from an ad, email or another website</td><td>The campaign details in the link (such as utm_source, utm_campaign, or an ad click ID like gclid or fbclid), the website that sent you and the first page you saw. We attach these to your signup so we know which channels bring students.</td></tr>
      <tr><td>You use the site</td><td>The Meta Pixel (see "Advertising and analytics tools" below) records the pages you view, actions such as opening the signup form or signing up, the ad that brought you, and device and browser details.</td></tr>
      <tr><td>You email us</td><td>Your email address and whatever you choose to write.</td></tr>
    </tbody>
  </table>
  <p>The ML Playground runs entirely in your browser. Nothing you type or draw in the labs is sent to us.</p>

  <h2>Why we use it</h2>
  <ul>
    <li>To reserve your founding seat or waitlist place and send your confirmation.</li>
    <li>To email you about the courses: start dates, access details and course updates.</li>
    <li>To understand which channels and ads bring students, and to improve the site.</li>
    <li>To show visitors short notices about recent signups, such as "Founding seat #23 claimed: a Python learner picked NLP &amp; Transformers, 5 minutes ago". They show a seat number, the track, the experience level and roughly how long ago the seat was claimed, never your name or your email. Email us if you would like your seat left out of these notices.</li>
  </ul>
  <p>We process your signup details because you ask us to reserve a seat and agree to these uses when you sign up. You can withdraw that consent at any time (see "Your rights").</p>

  <h2>Where it is stored and who can see it</h2>
  <p>Signups are stored in Google Sheets in our Google Workspace account, and confirmation emails are sent through Google (Gmail). Only Optimizer Step can see your details. We share data only with the service providers that run these tools for us, or when the law requires it.</p>
  <h2>Advertising and analytics tools</h2>
  <p>We use the <strong>Meta Pixel</strong> (Meta Platforms, which runs Instagram and Facebook) to measure our Instagram and Facebook ads and show them to people likely to be interested. It receives the pages you view and actions such as signing up, together with your browser and device details. When you sign up, it also receives a scrambled (hashed) copy of your email address and name, so Meta can match the signup to its ads without us sending the plain details. Meta processes this data under its own privacy policy. You can limit ad tracking in your Meta ad preferences and in your browser's privacy settings.</p>
  <p>Google Analytics, Google Ads and Microsoft Clarity are not switched on. If we add them, we will list them here first.</p>

  <h2>Cookies and local storage</h2>
  <p>The site stores a few small items in your browser: your light/dark theme choice, the campaign that brought you (for up to 90 days), which signup notices you have already seen or closed (for the current visit only) and, after you sign up, your first name and seat number so the site can recognise you. The Meta Pixel sets its own cookie (_fbp) to recognise your browser between visits. You can clear or block all of this at any time in your browser settings.</p>

  <h2>How long we keep it</h2>
  <p>We keep your signup details while the founding cohort and the courses you signed up for are running. We delete them sooner if you ask.</p>

  <h2>Your rights</h2>
  <p>Under India's Digital Personal Data Protection Act, 2023, you can ask us to:</p>
  <ul>
    <li>tell you what personal data we hold about you and how we use it;</li>
    <li>correct or update it;</li>
    <li>delete it, or stop emailing you (withdraw consent);</li>
    <li>handle a complaint about how we use your data.</li>
  </ul>
  <p>Email <a href="mailto:{email}">{email}</a> from the address you signed up with. Every email we send also lets you reply to unsubscribe.</p>

  <h2>Children</h2>
  <p>If you are under 18, please ask a parent or guardian before you sign up. They can contact us at any time to review or delete your details.</p>

  <h2>Changes</h2>
  <p>If we change how we use your data, we will update this page and the date at the top. For important changes, we will also email founding students.</p>
</article>
"""
    return {
        "path": "/privacy/",
        "out": "privacy/index.html",
        "title": "Privacy Policy | Optimizer Step",
        "description": "How Optimizer Step collects, uses and protects your personal data, and how to access, correct or delete it.",
        "body": body,
        "marketing": False,
        "schema": [breadcrumb_schema([("Home", "/"), ("Privacy policy", "/privacy/")])],
    }


def page_terms() -> dict:
    email = e(SITE["email"])
    cap = SITE["capacity"]
    body = f"""
<article class="legal narrow">
  {breadcrumbs([("Home", "/"), ("Terms", None)])}
  <h1>Terms of use</h1>
  <p class="updated">Last updated: {e(SITE["policy_updated"])}</p>
  <p>These terms cover your use of www.optimizerstep.com and the Founding {cap} offer. By using the site or claiming a seat, you agree to them.</p>

  <h2>The Founding {cap} offer</h2>
  <ul>
    <li>The first {cap} people who sign up with a valid email address get a free founding seat. A founding seat gives you free access to all of the launch tracks: ML Foundations, Deep Learning &amp; Vision, NLP &amp; Transformers and Build with RAG.</li>
    <li>You never pay for a founding seat, and we never ask for payment details. The planned regular price ({e(SITE["planned_price"])}) is shown for reference only.</li>
    <li>One seat per person and per email address. Seats are personal and cannot be sold or transferred.</li>
    <li>Signups after the first {cap} join the waitlist. Joining the waitlist does not guarantee a seat.</li>
    <li>We may cancel seats claimed with fake details, automated signups or multiple addresses for one person.</li>
  </ul>

  <h2>Course availability</h2>
  <p>The tracks open in stages. We will email you the start date for your track before it opens. Course content, schedules and formats may change as the platform grows. If we ever cannot deliver a launch track, we will tell founding students by email.</p>

  <h2>Plans and payments</h2>
  <ul>
    <li>ML Foundations (the Starter plan) is free for everyone. The paid plans, Single Track ({e(SITE["price_track"])}), All Tracks ({e(SITE["price_all"])}) and Pro ({e(SITE["price_pro"])}), open with the tracks. These are planned prices in Indian rupees and include all taxes.</li>
    <li>Every plan is a one-time payment. Nothing renews automatically.</li>
    <li>You can upgrade at any time: what you have already paid counts towards the higher plan, so you pay only the difference.</li>
    <li>Founding students get All Tracks free, can upgrade to Pro for {inr(founding_pro_upgrade())} and get {FOUNDING_DISCOUNT}% off any future paid track.</li>
    <li>Pro includes a live Q&amp;A session every month for {PRO_LIVE_MONTHS} months from the date of purchase, and written feedback on each of the student's track projects.</li>
    <li>Paid plans include a certificate for each track a student completes, including its project.</li>
    <li>Founding seats are free, so there is nothing to refund. For paid plans, the refund terms will be shown clearly before you pay.</li>
  </ul>

  <h2>Using the site and the ML Playground</h2>
  <p>The site and the ML Playground are provided for learning. The labs are simplified teaching models and are provided as they are, without any guarantee of accuracy. Please don't try to disrupt the site, scrape it in bulk or submit automated signups.</p>

  <h2>Content</h2>
  <p>The course material, videos, text and design on this site belong to Optimizer Step. You may share links to them, but please don't republish them without permission.</p>

  <h2>Liability</h2>
  <p>To the extent the law allows, Optimizer Step is not liable for indirect losses arising from your use of the site or the free courses.</p>

  <h2>Governing law</h2>
  <p>These terms are governed by the laws of India.</p>

  <h2>Contact</h2>
  <p>Questions about these terms? Email <a href="mailto:{email}">{email}</a>. See also our <a href="/privacy/">privacy policy</a>.</p>
</article>
"""
    return {
        "path": "/terms/",
        "out": "terms/index.html",
        "title": "Terms of Use | Optimizer Step",
        "description": f"The terms for using Optimizer Step and the Founding {cap} free seat offer.",
        "body": body,
        "marketing": False,
        "schema": [breadcrumb_schema([("Home", "/"), ("Terms", "/terms/")])],
    }


def page_welcome() -> dict:
    # A first lesson right away: welcome.js swaps in the first video of the track the student picked.
    lessons = {t["id"]: t["videos"][0] for t in TRACKS}
    lessons["undecided"] = "D37cTKjtXvU"
    lesson_data = {k: {"id": v, "title": VIDEOS[v]["title"], "hindi": bool(VIDEOS[v].get("hindi"))} for k, v in lessons.items()}
    lesson_json = e(json.dumps(lesson_data, ensure_ascii=False, separators=(",", ":")))
    first = lessons["undecided"]
    body = f"""
<section class="container welcome-hero" data-welcome-personal>
  <div class="success-icon" aria-hidden="true">✓</div>
  <h1 data-welcome-heading>You're in!</h1>
  <p data-welcome-lead>Your free founding seat is reserved. We've emailed your confirmation.</p>
  <p class="seat-badge" data-welcome-badge>Founding seat confirmed</p>
</section>
<section class="container welcome-hero" data-welcome-generic hidden>
  <div class="success-icon" aria-hidden="true">✦</div>
  <h1>Claim your free seat.</h1>
  <p>The first {SITE["capacity"]} students get all four launch tracks free. It takes 30 seconds and needs no payment details.</p>
  <div class="hero-actions" style="justify-content:center;margin-top:28px">{cta("Claim my free seat", "welcome-generic")}</div>
</section>
<section class="container first-lesson" aria-labelledby="lesson-title" data-first-lesson="{lesson_json}">
  <div class="first-lesson-copy"><span class="eyebrow">Start now</span><h2 id="lesson-title">Your first free lesson</h2><p data-lesson-text>Watch this now while your track gets ready. It's a free lesson from the Optimizer Step YouTube channel.</p></div>
  <div class="first-lesson-video">{video_facade(first, "Watch: " + VIDEOS[first]["title"])}</div>
</section>
<section class="container" aria-labelledby="next-title" style="padding-bottom:100px">
  <h2 class="visually-hidden" id="next-title">What to do next</h2>
  <ol class="next-steps">
    <li><h2>Check your inbox</h2><p>Your confirmation comes from <strong>{e(SITE["email"])}</strong>. If you can't see it in a few minutes, check Promotions or Spam and mark it "Not spam" so you don't miss your start date.</p></li>
    <li><h2>Start learning on YouTube</h2><p>Subscribe to the Optimizer Step channel for free lessons on Python, the maths behind ML, PyTorch and RAG while your track gets ready.</p><a class="button button-outline" href="{e(SITE["youtube"])}?sub_confirmation=1" target="_blank" rel="noopener" data-outbound="welcome">Subscribe on YouTube <span aria-hidden="true">↗</span></a></li>
    <li><h2>Play with a real model</h2><p>Open the free ML Playground and watch gradient descent, decision boundaries, k-means and attention work in your browser.</p><a class="button button-outline" href="/playground/">Open the ML Playground <span class="arrow" aria-hidden="true">→</span></a></li>
    <li><h2>Invite a friend</h2><p>Learning with a friend keeps you going. Founding seats are limited, so share the link while seats are left.</p>
      <div class="share-row"><a class="button button-outline" data-share="whatsapp" href="https://wa.me/" target="_blank" rel="noopener">WhatsApp</a><a class="button button-outline" data-share="x" data-via="{e(SITE["x_handle"].lstrip("@"))}" href="https://twitter.com/intent/tweet" target="_blank" rel="noopener">X</a><a class="button button-outline" data-share="linkedin" href="https://www.linkedin.com/" target="_blank" rel="noopener">LinkedIn</a><button class="button button-outline" type="button" data-share="copy">Copy link</button><button class="button button-outline" type="button" data-share="native" hidden>Share</button></div>
    </li>
  </ol>
</section>
"""
    return {
        "path": "/welcome/",
        "out": "welcome/index.html",
        "title": "You're in! | Optimizer Step",
        "description": "Your Optimizer Step founding seat is confirmed. Here's what happens next.",
        "body": body,
        "scripts": ["welcome"],
        "noindex": True,
        "marketing": False,
    }


def page_404() -> dict:
    body = f"""
<section class="container not-found">
  <p class="code">404 · PAGE NOT FOUND</p>
  <h1>This page took a <em>wrong step.</em></h1>
  <p>The page you're looking for doesn't exist or has moved. Even good optimizers overshoot sometimes.</p>
  <div class="hero-actions"><a class="button button-primary" href="/">Go to the homepage</a><a class="button button-outline" href="/courses/">See the courses</a><a class="button button-outline" href="/playground/">Open the ML Playground</a></div>
</section>
"""
    return {
        "path": "/404.html",
        "out": "404.html",
        "title": "Page not found | Optimizer Step",
        "description": "This page doesn't exist. Explore Optimizer Step's AI and machine learning courses and the free ML Playground.",
        "body": body,
        "noindex": True,
    }


# --------------------------------------------------------------------------- build

def clean_output() -> None:
    OUT.mkdir(exist_ok=True)
    for item in OUT.iterdir():
        if item.name in KEEP:
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    (OUT / ".nojekyll").write_text("", encoding="utf-8")


def minify_assets(folder: Path) -> None:
    """Minify the published CSS and JS with esbuild (installed by `npm ci`). The readable source stays in site/assets."""
    node = shutil.which("node")
    if not node or not (ROOT / "node_modules" / "esbuild").exists():
        print("NOTE: esbuild is not installed (run `npm ci`), so CSS and JS are published unminified.")
        return
    result = subprocess.run([node, str(ROOT / "scripts" / "minify.mjs"), str(folder)],
                            capture_output=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise SystemExit("Minifying CSS/JS failed (docs/ was left as it was):\n" + (result.stderr or "") + (result.stdout or ""))
    print((result.stdout or "").strip())


def stage_assets() -> Path:
    """Copy and minify the assets in a temporary folder first, so a failure never empties docs/."""
    stage = Path(tempfile.mkdtemp(prefix="os-assets-"))
    shutil.copytree(SRC / "assets", stage / "assets")
    minify_assets(stage / "assets")
    return stage


def compact_html(text: str) -> str:
    # Drop indentation and blank lines. Safe because no page uses <pre> or <textarea>.
    if "<pre" in text or "<textarea" in text:
        return text
    return "\n".join(line.strip() for line in text.splitlines() if line.strip()) + "\n"


def copy_assets(stage: Path) -> None:
    dst = OUT / "assets"
    shutil.copytree(stage / "assets", dst)
    shutil.rmtree(stage, ignore_errors=True)
    for path in sorted(dst.rglob("*")):
        if path.is_file():
            rel = path.relative_to(dst).as_posix()
            ASSET_HASHES[rel] = hashlib.sha256(path.read_bytes()).hexdigest()[:10]
    static = SRC / "static"
    if static.exists():
        for path in static.iterdir():
            if path.is_file():
                shutil.copy2(path, OUT / path.name)


def write_meta_files(pages: list[dict]) -> None:
    urls = [p for p in pages if not p.get("noindex")]
    priority = {"/": "1.0", "/courses/": "0.9", "/pricing/": "0.8", "/playground/": "0.8"}
    entries = "".join(
        f"  <url><loc>{URL}{p['path']}</loc><lastmod>{TODAY}</lastmod><priority>{priority.get(p['path'], '0.7')}</priority></url>\n" for p in urls
    )
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + entries + "</urlset>\n",
        encoding="utf-8",
    )
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {URL}/sitemap.xml\n", encoding="utf-8")
    manifest = {
        "name": "Optimizer Step",
        "short_name": "Optimizer Step",
        "description": "Learn AI and machine learning by building it.",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#080b13",
        "theme_color": "#080b13",
        "icons": [
            {"src": "/assets/img/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/img/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
    (OUT / "site.webmanifest").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def check_links() -> list[str]:
    problems = []
    pages = {p.relative_to(OUT).as_posix(): p.read_text(encoding="utf-8") for p in OUT.rglob("*.html")}
    ids = {name: set(re.findall(r'\sid="([^"]+)"', text)) for name, text in pages.items()}
    for name, text in pages.items():
        for attr, target in re.findall(r'\s(href|src|srcset)="([^"]+)"', text):
            for ref in [part.strip().split(" ")[0] for part in target.split(",")] if attr == "srcset" else [target]:
                if ref.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                    continue
                if ref.startswith("#"):
                    if ref[1:] and ref[1:] not in ids[name]:
                        problems.append(f"{name}: missing anchor {ref}")
                    continue
                path, _, anchor = ref.partition("#")
                path = path.split("?")[0]
                if not path.startswith("/"):
                    problems.append(f"{name}: relative link {ref}")
                    continue
                rel = path.lstrip("/")
                target_page = rel + "index.html" if (rel == "" or rel.endswith("/")) else rel
                if not (OUT / target_page).exists():
                    problems.append(f"{name}: broken link {ref}")
                elif anchor and target_page in ids and anchor not in ids[target_page]:
                    problems.append(f"{name}: missing anchor {ref}")
    return problems


def build() -> int:
    stage = stage_assets()
    clean_output()
    copy_assets(stage)
    pages = [page_home(), page_courses(), page_pricing(), *[page_track(t) for t in TRACKS], page_playground(), *[page_lab(lab) for lab in LABS],
             page_privacy(), page_terms(), page_welcome(), page_404()]
    for page in pages:
        target = OUT / page["out"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(compact_html(layout(page)), encoding="utf-8")
    write_meta_files(pages)
    problems = check_links()
    endpoint = config_endpoint()
    print(f"Built {len(pages)} pages into {OUT.relative_to(ROOT)}/")
    print("Enrollment endpoint:", endpoint or "NOT SET (signups will show 'opening soon')")
    if problems:
        print("\nLink problems:")
        for problem in problems:
            print("  -", problem)
        return 1
    print("Internal links and anchors: all OK")
    return 0


if __name__ == "__main__":
    sys.exit(build())
