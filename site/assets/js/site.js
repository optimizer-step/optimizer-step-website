/*
 * Optimizer Step — shared behaviour for every page:
 * theme, ad attribution (UTMs / click IDs), analytics, live seat count,
 * the signup dialog and forms, the sticky mobile button and YouTube facades.
 * Exposes window.OS for page scripts (welcome.js, playground.js).
 */
(function () {
  "use strict";

  var CFG = window.OS_CONFIG || {};
  var TRACKING = CFG.tracking || {};
  var doc = document;
  var root = doc.documentElement;
  var DAY = 864e5;
  var KEYS = {
    theme: "optimizerstep-theme-v1",
    attribution: "os-attr-v1",
    member: "os-member-v1",
    stats: "os-stats-v1",
    signup: "os-signup-v1",
    notices: "os-notices-v1"
  };
  var CAMPAIGN_KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "gclid", "fbclid", "gbraid", "wbraid", "msclkid", "ttclid"];
  var TRACK_NAMES = {
    foundations: "ML Foundations",
    "deep-learning": "Deep Learning & Vision",
    nlp: "NLP & Transformers",
    rag: "Build with RAG",
    undecided: "Not sure yet"
  };

  function $(selector, scope) { return (scope || doc).querySelector(selector); }
  function $$(selector, scope) { return Array.prototype.slice.call((scope || doc).querySelectorAll(selector)); }

  var store = {
    get: function (area, key) {
      try { var raw = window[area].getItem(key); return raw ? JSON.parse(raw) : null; } catch (e) { return null; }
    },
    set: function (area, key, value) {
      try { window[area].setItem(key, JSON.stringify(value)); } catch (e) { /* storage blocked (private mode) */ }
    },
    remove: function (area, key) {
      try { window[area].removeItem(key); } catch (e) { /* ignore */ }
    }
  };

  function hostOf(url) {
    try { return new URL(url).hostname.replace(/^www\./, ""); } catch (e) { return ""; }
  }
  function firstName(name) {
    return String(name || "").trim().split(/\s+/)[0].slice(0, 40);
  }

  /* ---------------- Theme ---------------- */
  function setupTheme() {
    var button = $("[data-theme-toggle]");
    if (!button) return;
    function sync() {
      var light = root.getAttribute("data-theme") === "light";
      button.setAttribute("aria-label", light ? "Switch to dark mode" : "Switch to light mode");
      button.setAttribute("aria-pressed", String(light));
    }
    sync();
    button.addEventListener("click", function () {
      var light = root.getAttribute("data-theme") !== "light";
      if (light) root.setAttribute("data-theme", "light"); else root.removeAttribute("data-theme");
      try { localStorage.setItem(KEYS.theme, light ? "light" : "dark"); } catch (e) { /* ignore */ }
      sync();
    });
  }

  /* ---------------- Attribution (first + last touch) ---------------- */
  function captureAttribution() {
    var params = new URLSearchParams(location.search);
    var touch = {};
    var hasCampaign = false;
    CAMPAIGN_KEYS.forEach(function (key) {
      var value = params.get(key);
      if (value) { touch[key] = value.slice(0, 200); hasCampaign = true; }
    });
    var referrer = "";
    if (doc.referrer && hostOf(doc.referrer) !== location.hostname.replace(/^www\./, "")) referrer = doc.referrer.slice(0, 300);

    var data = store.get("localStorage", KEYS.attribution) || {};
    var now = Date.now();
    if (data.first && now - data.first.ts > 90 * DAY) data.first = null;
    if (data.last && now - data.last.ts > 30 * DAY) data.last = null;
    var landing = (location.pathname + location.search).slice(0, 300);

    if (hasCampaign || referrer) {
      touch.referrer = referrer;
      touch.landing = landing;
      touch.ts = now;
      data.last = touch;
      if (!data.first) data.first = touch;
    } else if (!data.first) {
      data.first = { referrer: "", landing: landing, ts: now };
    }
    store.set("localStorage", KEYS.attribution, data);
  }

  function describeTouch(t) {
    if (!t) return "";
    var source = t.utm_source
      ? [t.utm_source, t.utm_medium, t.utm_campaign].filter(Boolean).join(" / ")
      : t.gclid || t.gbraid || t.wbraid ? "google ads"
      : t.fbclid ? "meta"
      : t.referrer ? hostOf(t.referrer)
      : "direct";
    return source + " → " + (t.landing || "/");
  }

  function attributionPayload() {
    var data = store.get("localStorage", KEYS.attribution) || {};
    var touch = data.last || data.first || {};
    var out = {};
    CAMPAIGN_KEYS.forEach(function (key) { if (touch[key]) out[key] = touch[key]; });
    out.referrer = touch.referrer || "";
    out.landing = touch.landing || "";
    out.first_touch = describeTouch(data.first);
    return out;
  }

  /* ---------------- Analytics ---------------- */
  function loadScript(src) {
    var s = doc.createElement("script");
    s.async = true;
    s.src = src;
    doc.head.appendChild(s);
  }

  function initAnalytics() {
    var ga = String(TRACKING.ga4MeasurementId || "").trim();
    var ads = String(TRACKING.googleAdsId || "").trim();
    var pixel = String(TRACKING.metaPixelId || "").trim();
    var clarity = String(TRACKING.clarityProjectId || "").trim();

    if (/^G-[A-Z0-9]+$/i.test(ga) || /^AW-\d+$/i.test(ads)) {
      window.dataLayer = window.dataLayer || [];
      window.gtag = function () { window.dataLayer.push(arguments); };
      window.gtag("js", new Date());
      if (/^G-[A-Z0-9]+$/i.test(ga)) window.gtag("config", ga);
      if (/^AW-\d+$/i.test(ads)) window.gtag("config", ads);
      loadScript("https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(ga || ads));
    }

    if (/^\d{6,20}$/.test(pixel)) {
      /* Meta Pixel base code */
      (function (f, b, e, v) {
        if (f.fbq) return;
        var n = f.fbq = function () { if (n.callMethod) n.callMethod.apply(n, arguments); else n.queue.push(arguments); };
        if (!f._fbq) f._fbq = n;
        n.push = n; n.loaded = true; n.version = "2.0"; n.queue = [];
        var t = b.createElement(e); t.async = true; t.src = v;
        var s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
      })(window, doc, "script", "https://connect.facebook.net/en_US/fbevents.js");
      window.fbq("init", pixel);
      window.fbq("track", "PageView");
    }

    if (/^[a-z0-9]{6,20}$/i.test(clarity)) {
      (function (c, l, a, r, i) {
        c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
        var t = l.createElement(r); t.async = true; t.src = "https://www.clarity.ms/tag/" + i;
        var y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
      })(window, doc, "clarity", "script", clarity);
    }
  }

  var META_EVENTS = {
    view_track: ["track", "ViewContent"],
    form_open: ["trackCustom", "SignupFormOpen"],
    cta_click: ["trackCustom", "CTAClick"],
    playground_interaction: ["trackCustom", "PlaygroundInteraction"],
    video_play: ["trackCustom", "VideoPlay"]
  };

  function track(name, params) {
    params = params || {};
    try {
      if (typeof window.gtag === "function") window.gtag("event", name, params);
      if (typeof window.fbq === "function" && META_EVENTS[name]) window.fbq(META_EVENTS[name][0], META_EVENTS[name][1], params);
      if (typeof window.clarity === "function") window.clarity("event", name);
    } catch (e) { /* never let tracking break the page */ }
  }

  function trackConversion(info) {
    var trackName = TRACK_NAMES[info.track] || "Not sure yet";
    try {
      if (typeof window.gtag === "function") {
        window.gtag("event", "sign_up", { method: "founding_form", track: info.track, seat_status: info.status });
        window.gtag("event", "generate_lead", { currency: "INR", value: 0, track: info.track, seat_status: info.status });
        if (TRACKING.googleAdsId && TRACKING.googleAdsLeadLabel) {
          window.gtag("event", "conversion", { send_to: TRACKING.googleAdsId + "/" + TRACKING.googleAdsLeadLabel, value: 0, currency: "INR" });
        }
      }
      if (typeof window.fbq === "function") {
        var eventId = "signup-" + (info.ts || Date.now());
        window.fbq("track", "Lead", { content_name: "Founding 100", content_category: trackName, value: 0, currency: "INR" }, { eventID: eventId + "-lead" });
        window.fbq("track", "CompleteRegistration", { content_name: "Founding 100", status: info.status, value: 0, currency: "INR" }, { eventID: eventId + "-reg" });
      }
      if (typeof window.clarity === "function") window.clarity("event", "sign_up");
    } catch (e) { /* ignore */ }
  }

  /* ---------------- Network ---------------- */
  function fetchJSON(url, options, timeoutMs) {
    var controller = typeof AbortController === "function" ? new AbortController() : null;
    var timer = controller ? setTimeout(function () { controller.abort(); }, timeoutMs) : null;
    var opts = Object.assign({ redirect: "follow" }, options || {});
    if (controller) opts.signal = controller.signal;
    return fetch(url, opts).then(function (response) {
      if (timer) clearTimeout(timer);
      return response.text().then(function (text) {
        try { return JSON.parse(text); } catch (e) { var err = new Error("bad-json"); err.kind = "server"; throw err; }
      });
    }, function (error) {
      if (timer) clearTimeout(timer);
      error.kind = "network";
      throw error;
    });
  }

  /* ---------------- Live seat count ---------------- */
  var currentStats = null;

  // Every number here comes from the live signup sheet; nothing is invented or rounded up.
  function applyStats(s, fetchedAt) {
    if (!s) return;
    currentStats = s;
    var capacity = Number(s.capacity) || CFG.capacity || 100;
    var claimed = Math.max(0, Number(s.claimed) || 0);
    var remaining = typeof s.remaining === "number" ? Math.max(0, s.remaining) : Math.max(0, capacity - claimed);
    var full = remaining <= 0;
    var showCounts = full || claimed >= (Number(CFG.showCountsAfter) || 0);
    var critical = !full && showCounts && remaining <= 10;
    var low = !full && showCounts && remaining <= 25;

    root.classList.toggle("seats-full", full);
    root.classList.toggle("seats-low", low);
    root.classList.toggle("seats-critical", critical);
    $$("[data-seats-text]").forEach(function (el) {
      el.textContent = full
        ? "All " + capacity + " founding seats are taken. Join the waitlist."
        : critical ? (remaining === 1 ? "Last free founding seat" : "Last " + remaining + " free founding seats")
        : low ? "Only " + remaining + " of " + capacity + " free seats left"
        : showCounts ? remaining + " of " + capacity + " free seats left" : capacity + " free founding seats. First come, first served.";
    });
    $$("[data-seats-short]").forEach(function (el) {
      el.textContent = full ? "Founding seats are full. Waitlist open."
        : critical ? (remaining === 1 ? "Last free seat left" : "Last " + remaining + " free seats")
        : low ? "Only " + remaining + " free seats left"
        : showCounts ? remaining + " of " + capacity + " free seats left" : "First " + capacity + " students join free";
    });
    if (typeof s.today === "number") {
      var showToday = showCounts && !full && s.today >= (Number(CFG.todayAfter) || 3);
      $$("[data-seats-today]").forEach(function (el) {
        el.hidden = !showToday;
        if (showToday) el.textContent = s.today + " people joined in the last 24 hours";
      });
    }
    $$("[data-seats-meter]").forEach(function (el) {
      el.hidden = !showCounts;
      el.setAttribute("aria-valuemax", String(capacity));
      el.setAttribute("aria-valuenow", String(Math.min(claimed, capacity)));
      var bar = $("span", el);
      if (bar) bar.style.width = Math.min(100, (claimed / capacity) * 100).toFixed(1) + "%";
    });
    $$("[data-seats-claimed]").forEach(function (el) { el.textContent = String(Math.min(claimed, capacity)); });
    $$("[data-cta-label]").forEach(function (el) {
      el.textContent = full ? "Join the waitlist" : el.getAttribute("data-cta-label");
    });
    updateNotices(s, fetchedAt || Date.now());
  }

  function loadStats(force) {
    if (!CFG.enrollmentEndpoint) return;
    var cached = store.get("sessionStorage", KEYS.stats);
    if (cached && !force && Date.now() - cached.ts < 60000) { applyStats(cached.data, cached.ts); return; }
    fetchJSON(CFG.enrollmentEndpoint + "?action=stats", { method: "GET", cache: "no-store" }, 12000)
      .then(function (data) {
        if (data && data.ok) {
          var now = Date.now();
          store.set("sessionStorage", KEYS.stats, { ts: now, data: data });
          applyStats(data, now);
        }
      })
      .catch(function () { /* keep the static "100 free founding seats" copy */ });
  }

  function setupStats() {
    var cached = store.get("sessionStorage", KEYS.stats);
    if (cached) applyStats(cached.data, cached.ts);
    loadStats(false);
    var every = Math.max(30, Number(CFG.statsRefreshSeconds) || 90) * 1000;
    setInterval(function () { if (doc.visibilityState === "visible") loadStats(true); }, every);
    doc.addEventListener("visibilitychange", function () {
      var c = store.get("sessionStorage", KEYS.stats);
      if (doc.visibilityState === "visible" && (!c || Date.now() - c.ts > 60000)) loadStats(true);
    });
  }

  /* ---------------- "Seat claimed" notices: real signups only, never names ---------------- */
  var NOTICES = CFG.liveNotices || {};
  var NOTICE_MAX_AGE = 72 * 3600 * 1000;
  var EXPERIENCE_WHO = ["A beginner", "A Python learner", "An ML builder"];
  var notice = { el: null, items: [], timer: 0, hideTimer: 0, shownHere: 0, started: false, state: null, returnTo: null };
  var lastFormEdit = 0;

  function agoText(ms) {
    var minutes = Math.floor(ms / 60000);
    if (minutes < 1) return "just now";
    if (minutes < 60) return minutes === 1 ? "1 minute ago" : minutes + " minutes ago";
    var hours = Math.floor(minutes / 60);
    if (hours < 24) return hours === 1 ? "1 hour ago" : hours + " hours ago";
    var days = Math.floor(hours / 24);
    return days === 1 ? "1 day ago" : days + " days ago";
  }

  // Kept in memory and saved for the visit, so the per-visit limit and "closed" carry across pages.
  function noticeState() {
    if (!notice.state) {
      var saved = store.get("sessionStorage", KEYS.notices);
      notice.state = saved && Array.isArray(saved.seen) ? saved : { seen: [], count: 0, off: false };
    }
    return notice.state;
  }

  function saveNoticeState() { store.set("sessionStorage", KEYS.notices, noticeState()); }

  // Without working session storage the per-visit limit and the close choice would reset on every
  // page, so that visitor gets no notices at all.
  function canKeepSessionState() {
    try {
      var probe = "os-probe";
      window.sessionStorage.setItem(probe, "1");
      var ok = window.sessionStorage.getItem(probe) === "1";
      window.sessionStorage.removeItem(probe);
      return ok;
    } catch (e) { return false; }
  }

  function keyboardFocusElsewhere() {
    var active = doc.activeElement;
    if (!active || active === doc.body || active === doc.documentElement || (notice.el && notice.el.contains(active))) return false;
    try { return active.matches(":focus-visible"); } catch (e) { return false; }
  }

  // Never interrupt someone who is filling in the form, submitting, or moving around by keyboard.
  function noticeShouldWait() {
    var active = doc.activeElement;
    var typing = active && /^(INPUT|SELECT|TEXTAREA)$/.test(active.tagName);
    return doc.visibilityState !== "visible" || typing || stickyState.formVisible ||
      Date.now() - lastFormEdit < 30000 || Boolean($("form[data-signup-form][data-busy]")) ||
      Boolean(dialog && dialog.open) || window.innerHeight < 480 || keyboardFocusElsewhere();
  }

  function updateNotices(s, fetchedAt) {
    if (!notice.el || !s || !Array.isArray(s.recent)) return;
    var claimed = Number(s.claimed) || 0;
    var full = typeof s.remaining === "number" && s.remaining <= 0;
    var after = NOTICES.showAfter != null ? Number(NOTICES.showAfter) : Number(CFG.showCountsAfter) || 0;
    if (!full && claimed < after) { notice.items = []; return; }
    notice.items = s.recent.filter(function (r) {
      return r && (r.status === "founding" || r.status === "waitlist") && typeof r.ago === "number" && r.ago >= 0 && r.ago * 1000 < NOTICE_MAX_AGE;
    }).map(function (r) {
      return { key: r.status + ":" + r.seat, seat: Number(r.seat) || 0, status: r.status, track: r.track, exp: Number(r.exp), at: fetchedAt - r.ago * 1000 };
    });
    if (!notice.started && notice.items.length) {
      notice.started = true;
      scheduleNotice(7000);
    }
  }

  function scheduleNotice(delay) {
    clearTimeout(notice.timer);
    notice.timer = setTimeout(showNotice, delay);
  }

  function showNotice() {
    var state = noticeState();
    if (!notice.el || state.off || state.count >= (Number(NOTICES.perSession) || 6) || notice.shownHere >= (Number(NOTICES.perPage) || 3)) return;
    if (store.get("localStorage", KEYS.member)) return;
    if (noticeShouldWait()) { scheduleNotice(8000); return; }
    var item = null;
    for (var i = 0; i < notice.items.length; i++) {
      var candidate = notice.items[i];
      if (state.seen.indexOf(candidate.key) < 0 && Date.now() - candidate.at < NOTICE_MAX_AGE) { item = candidate; break; }
    }
    if (!item) { scheduleNotice(30000); return; } // a newer signup may arrive with the next stats refresh

    var trackName = item.track && item.track !== "undecided" ? TRACK_NAMES[item.track] : "";
    var who = EXPERIENCE_WHO[item.exp] || "Someone";
    $("[data-notice-title]", notice.el).textContent = item.status === "waitlist"
      ? "Someone joined the waitlist"
      : item.seat ? "Founding seat #" + item.seat + " claimed" : "A founding seat was claimed";
    $("[data-notice-meta]", notice.el).textContent = (trackName ? who + " picked " + trackName : who + " joined") + " · " + agoText(Date.now() - item.at);
    notice.el.hidden = false;
    requestAnimationFrame(function () { requestAnimationFrame(function () { notice.el.classList.add("is-visible"); }); });

    state.seen = state.seen.concat(item.key).slice(-60);
    state.count += 1;
    saveNoticeState();
    notice.shownHere += 1;
    clearTimeout(notice.hideTimer);
    notice.hideTimer = setTimeout(hideNotice, 7000);
  }

  // Hide after the timer, but keep it while hovered, focused, or while the dialog it opened is up
  // (closing the dialog returns focus to "Claim yours", so it must still be there).
  function hideNotice() {
    if (!notice.el || notice.el.hidden) return;
    if ((dialog && dialog.open) || notice.el.matches(":hover") || notice.el.contains(doc.activeElement)) {
      clearTimeout(notice.hideTimer);
      notice.hideTimer = setTimeout(hideNotice, 2500);
      return;
    }
    hideNoticeNow();
  }

  function hideNoticeNow() {
    if (!notice.el || notice.el.hidden) return;
    clearTimeout(notice.hideTimer);
    notice.el.classList.remove("is-visible");
    setTimeout(function () { if (notice.el && !notice.el.classList.contains("is-visible")) notice.el.hidden = true; }, 400);
    scheduleNotice(24000);
  }

  function closeNotices() {
    if (!notice.el) return;
    noticeState().off = true;
    saveNoticeState();
    clearTimeout(notice.timer);
    clearTimeout(notice.hideTimer);
    if (notice.el.contains(doc.activeElement)) {
      var back = notice.returnTo && doc.contains(notice.returnTo) ? notice.returnTo : $("#main");
      if (back) back.focus({ preventScroll: true });
    }
    notice.el.classList.remove("is-visible");
    notice.el.hidden = true;
    track("notice_close", {});
  }

  function setupNotices() {
    notice.el = $("[data-live-notice]");
    if (!notice.el) return;
    if (NOTICES.enabled === false || store.get("localStorage", KEYS.member) || !canKeepSessionState()) { notice.el.remove(); notice.el = null; return; }
    $("[data-notice-close]", notice.el).addEventListener("click", closeNotices);
    notice.el.addEventListener("focusin", function (event) {
      if (event.relatedTarget && !notice.el.contains(event.relatedTarget)) notice.returnTo = event.relatedTarget;
    });
    doc.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && notice.el && !notice.el.hidden && !(dialog && dialog.open)) closeNotices();
    });
    // Get out of the way when someone starts on a signup form or moves focus by keyboard.
    doc.addEventListener("focusin", function (event) {
      if (!notice.el || notice.el.hidden || notice.el.contains(event.target)) return;
      if ((event.target.closest && event.target.closest("form[data-signup-form]")) || keyboardFocusElsewhere()) hideNoticeNow();
    });
    $$("form[data-signup-form]").forEach(function (form) {
      var edited = function () { lastFormEdit = Date.now(); };
      form.addEventListener("input", edited);
      form.addEventListener("change", edited);
    });
  }

  /* ---------------- Company-name strip: a real pause button (not hover-only) ---------------- */
  function setupMarquee() {
    $$("[data-marquee-toggle]").forEach(function (button) {
      var strip = button.parentNode && $(".company-marquee", button.parentNode);
      if (!strip) return;
      button.addEventListener("click", function () {
        var paused = strip.classList.toggle("is-paused");
        button.setAttribute("aria-pressed", String(paused));
        button.textContent = paused ? "▶" : "❚❚";
      });
    });
  }

  /* ---------------- Signup dialog ---------------- */
  var dialog = null;

  function openSignup(trackId, source) {
    dialog = dialog || $("#signupDialog");
    if (!dialog || typeof dialog.showModal !== "function") {
      var inline = $("[data-signup-inline]");
      if (inline) { inline.scrollIntoView({ behavior: "smooth", block: "start" }); return; }
      location.href = "/#join";
      return;
    }
    var form = $("form", dialog);
    if (trackId && form.elements.track) form.elements.track.value = trackId;
    clearErrors(form);
    form.setAttribute("data-opened-at", String(Date.now()));
    if (!dialog.open) dialog.showModal();
    updateSticky();
    setTimeout(function () { if (form.elements.name) form.elements.name.focus(); }, 60);
    track("form_open", { location: source || "page", track: trackId || "" });
  }

  function setupDialog() {
    dialog = $("#signupDialog");
    doc.addEventListener("click", function (event) {
      var trigger = event.target.closest("[data-enroll]");
      if (!trigger) return;
      event.preventDefault();
      track("cta_click", { location: trigger.getAttribute("data-cta") || "page", track: trigger.getAttribute("data-track") || "" });
      openSignup(trigger.getAttribute("data-track"), trigger.getAttribute("data-cta"));
    });
    if (!dialog) return;
    $$("[data-dialog-close]", dialog).forEach(function (button) {
      button.addEventListener("click", function () { dialog.close(); });
    });
    dialog.addEventListener("click", function (event) { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener("close", updateSticky);
  }

  /* ---------------- Forms ---------------- */
  var KNOWN_DOMAINS = ["gmail.com", "yahoo.com", "yahoo.co.in", "ymail.com", "hotmail.com", "outlook.com", "live.com", "icloud.com", "rediffmail.com", "protonmail.com", "proton.me", "mail.com", "aol.com", "zoho.com"];

  function levenshtein(a, b) {
    var prev = [], cur, i, j;
    for (j = 0; j <= b.length; j++) prev[j] = j;
    for (i = 1; i <= a.length; i++) {
      cur = [i];
      for (j = 1; j <= b.length; j++) {
        cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1));
      }
      prev = cur;
    }
    return prev[b.length];
  }

  function suggestEmail(email) {
    var at = email.lastIndexOf("@");
    if (at < 1) return null;
    var domain = email.slice(at + 1).toLowerCase();
    if (!domain || KNOWN_DOMAINS.indexOf(domain) >= 0) return null;
    var best = null, bestDistance = 3;
    KNOWN_DOMAINS.forEach(function (candidate) {
      var d = levenshtein(domain, candidate);
      if (d < bestDistance) { bestDistance = d; best = candidate; }
    });
    return best && bestDistance <= 2 ? email.slice(0, at + 1) + best : null;
  }

  function fieldError(form, name, message) {
    var input = form.elements[name];
    var box = $("[data-error-for='" + name + "']", form);
    if (input && input.length && input[0] && input[0].type === "radio") {
      Array.prototype.forEach.call(input, function (r) { r.setAttribute("aria-invalid", message ? "true" : "false"); });
    } else if (input) {
      input.setAttribute("aria-invalid", message ? "true" : "false");
    }
    if (box) { box.textContent = message || ""; box.hidden = !message; }
  }

  function clearErrors(form) {
    ["name", "email", "experience"].forEach(function (n) { fieldError(form, n, ""); });
    var general = $("[data-form-error]", form);
    if (general) { general.hidden = true; general.textContent = ""; }
  }

  function showGeneralError(form, message) {
    var general = $("[data-form-error]", form);
    if (!general) return;
    general.textContent = message;
    general.hidden = false;
  }

  function validateForm(form) {
    clearErrors(form);
    var name = form.elements.name.value.trim().replace(/\s+/g, " ");
    var email = form.elements.email.value.trim().toLowerCase();
    var experienceInput = form.querySelector("input[name='experience']:checked");
    var firstInvalid = null;
    if (name.length < 2) { fieldError(form, "name", "Please enter your name."); firstInvalid = firstInvalid || form.elements.name; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) { fieldError(form, "email", "Please enter a valid email address, like you@gmail.com."); firstInvalid = firstInvalid || form.elements.email; }
    if (!experienceInput) {
      fieldError(form, "experience", "Please choose your experience level.");
      firstInvalid = firstInvalid || form.querySelector("input[name='experience']");
    }
    if (firstInvalid) {
      firstInvalid.focus();
      track("form_error", { field: firstInvalid.name });
      return null;
    }
    return {
      name: name,
      email: email,
      track: form.elements.track ? form.elements.track.value : "undecided",
      experience: experienceInput.value
    };
  }

  function setBusy(form, busy) {
    var button = $("[data-submit]", form);
    if (!button) return;
    if (busy) {
      form.setAttribute("data-busy", "1");
      button.disabled = true;
      button.setAttribute("aria-disabled", "true");
      button.setAttribute("data-original", button.innerHTML);
      button.innerHTML = '<span class="spinner" aria-hidden="true"></span><span>Reserving your seat...</span>';
    } else {
      form.removeAttribute("data-busy");
      button.disabled = false;
      button.removeAttribute("aria-disabled");
      if (button.getAttribute("data-original")) button.innerHTML = button.getAttribute("data-original");
    }
  }

  function finishSignup(result, payload) {
    var info = {
      first: firstName(payload.name),
      seat: Number(result.seat) || 0,
      status: result.status === "waitlist" ? "waitlist" : "founding",
      track: payload.track,
      duplicate: Boolean(result.duplicate),
      pending: Boolean(result.pending),
      tracked: false,
      ts: Date.now()
    };
    store.set("sessionStorage", KEYS.signup, info);
    // A duplicate answer carries no seat number (the server never reveals one), so keep any seat this browser already knows.
    if (!(info.duplicate && !info.seat && store.get("localStorage", KEYS.member))) {
      store.set("localStorage", KEYS.member, { first: info.first, seat: info.seat, status: info.status, ts: info.ts });
    }
    store.remove("sessionStorage", KEYS.stats);
    location.href = "/welcome/";
  }

  function submitForm(event) {
    event.preventDefault();
    var form = event.currentTarget;
    if (form.getAttribute("data-busy")) return;

    var honeypot = form.elements.company && form.elements.company.value.trim();
    var data = validateForm(form);
    if (!data) return;
    if (honeypot) return; // bots: silently ignore

    if (!CFG.enrollmentEndpoint) {
      showGeneralError(form, "Signups open very soon. Please check back in a few minutes.");
      return;
    }

    var openedAt = Number(form.getAttribute("data-opened-at")) || Number(root.getAttribute("data-loaded-at")) || Date.now();
    var payload = {
      name: data.name,
      email: data.email,
      track: data.track,
      experience: data.experience,
      company: "",
      page: location.pathname,
      device: /Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent) ? "mobile" : "desktop",
      elapsedMs: Date.now() - openedAt,
      attribution: attributionPayload()
    };

    setBusy(form, true);
    fetchJSON(CFG.enrollmentEndpoint, { method: "POST", body: JSON.stringify(payload) }, 25000)
      .then(function (result) {
        if (result && result.ok && result.accepted) {
          finishSignup(result, payload);
          return;
        }
        setBusy(form, false);
        var message = (result && result.error) || "Something went wrong. Please try again.";
        if (result && result.field && form.elements[result.field]) fieldError(form, result.field, message);
        else showGeneralError(form, message);
        track("form_error", { field: (result && result.field) || "server" });
      })
      .catch(function (error) {
        // The request never got an answer (offline, timeout, blocked). Hand it to the browser to
        // deliver in the background: the server drops duplicates, so a retry can't double-book.
        var queued = false;
        if (error && error.kind === "network" && navigator.sendBeacon) {
          try {
            queued = navigator.sendBeacon(CFG.enrollmentEndpoint, new Blob([JSON.stringify(payload)], { type: "text/plain;charset=UTF-8" }));
          } catch (e) { queued = false; }
        }
        if (queued) {
          finishSignup({ ok: true, accepted: true, pending: true, status: "founding", seat: 0 }, payload);
          return;
        }
        setBusy(form, false);
        showGeneralError(form, "We couldn't reach our server. Check your internet connection and try again.");
        track("form_error", { field: "network" });
      });
  }

  function setupForms() {
    var member = store.get("localStorage", KEYS.member);
    $$("form[data-signup-form]").forEach(function (form) {
      form.setAttribute("data-opened-at", String(Date.now()));
      form.addEventListener("submit", submitForm);

      var started = false;
      form.addEventListener("input", function () {
        if (started) return;
        started = true;
        track("form_start", { form: form.getAttribute("data-signup-form") || "form" });
      });

      var email = form.elements.email;
      var suggestBox = $("[data-email-suggest]", form);
      if (email && suggestBox) {
        var suggestButton = $("button", suggestBox);
        var check = function () {
          var suggestion = suggestEmail(email.value.trim());
          suggestBox.hidden = !suggestion;
          if (suggestion) suggestButton.textContent = suggestion;
        };
        email.addEventListener("blur", check);
        email.addEventListener("change", check);
        suggestButton.addEventListener("click", function () {
          email.value = suggestButton.textContent;
          suggestBox.hidden = true;
          email.focus();
        });
      }

      var note = $("[data-member-note]", form);
      if (note && member && member.seat) {
        note.textContent = "This browser already claimed " + (member.status === "waitlist" ? "waitlist place #" : "founding seat #") + member.seat + ". Signing up someone else? Go ahead.";
        note.hidden = false;
      }
    });

    // ?join=1 opens the form straight away (useful for ads that link to the form).
    var params = new URLSearchParams(location.search);
    if (params.get("join") === "1") openSignup(params.get("track") || "", "url");
    else if (params.get("track") && TRACK_NAMES[params.get("track")]) {
      $$("form[data-signup-form] select[name='track']").forEach(function (select) { select.value = params.get("track"); });
    }
  }

  /* ---------------- Sticky mobile button ---------------- */
  var stickyState = { heroVisible: true, formVisible: false };
  function updateSticky() {
    var bar = $("[data-sticky-cta]");
    if (!bar) return;
    var show = !stickyState.heroVisible && !stickyState.formVisible && !(dialog && dialog.open);
    bar.classList.toggle("is-visible", show);
    root.classList.toggle("sticky-on", show);
    if (stickyState.formVisible) hideNoticeNow(); // never cover the inline signup form
    bar.setAttribute("aria-hidden", String(!show));
    $$("button, a", bar).forEach(function (el) { el.tabIndex = show ? 0 : -1; });
  }

  function setupSticky() {
    var bar = $("[data-sticky-cta]");
    if (!bar) return;
    if (store.get("localStorage", KEYS.member) || !("IntersectionObserver" in window)) { bar.remove(); return; }
    bar.hidden = false;
    // The notice sits just above the bar, whatever height the bar wraps to.
    if ("ResizeObserver" in window) {
      new ResizeObserver(function () { root.style.setProperty("--sticky-h", bar.offsetHeight + "px"); }).observe(bar);
    }
    var anchor = $("[data-hero-cta]") || $("h1");
    var forms = $$("[data-signup-inline]");
    stickyState.heroVisible = Boolean(anchor);
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.target === anchor) stickyState.heroVisible = entry.isIntersecting || entry.boundingClientRect.top > 0;
        else stickyState.formVisible = entry.isIntersecting;
      });
      updateSticky();
    });
    if (anchor) observer.observe(anchor);
    forms.forEach(function (f) { observer.observe(f); });
    updateSticky();
  }

  /* ---------------- YouTube facades + outbound clicks ---------------- */
  function setupVideos() {
    doc.addEventListener("click", function (event) {
      var facade = event.target.closest("[data-youtube]");
      if (!facade) return;
      event.preventDefault();
      var id = facade.getAttribute("data-youtube");
      var iframe = doc.createElement("iframe");
      iframe.className = "video-frame";
      iframe.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(id) + "?autoplay=1&rel=0&modestbranding=1&playsinline=1";
      iframe.title = facade.getAttribute("data-title") || "YouTube video";
      iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
      iframe.allowFullscreen = true;
      iframe.referrerPolicy = "strict-origin-when-cross-origin";
      facade.replaceWith(iframe);
      track("video_play", { video_id: id });
    });
    doc.addEventListener("click", function (event) {
      var link = event.target.closest("a[data-outbound]");
      if (link) track("outbound_click", { link_url: link.href, location: link.getAttribute("data-outbound") });
    });
  }

  /* ---------------- Boot ---------------- */
  root.setAttribute("data-loaded-at", String(Date.now()));
  if (location.pathname === "/" && location.hash === "#playground") {
    location.replace("/playground/");
    return;
  }

  window.OS = {
    config: CFG,
    store: store,
    keys: KEYS,
    trackNames: TRACK_NAMES,
    track: track,
    trackConversion: trackConversion,
    openSignup: openSignup,
    stats: function () { return currentStats; }
  };

  captureAttribution();
  initAnalytics();
  setupTheme();
  setupDialog();
  setupForms();
  setupNotices();
  setupStats();
  setupMarquee();
  setupSticky();
  setupVideos();
  $$("[data-year]").forEach(function (el) { el.textContent = String(new Date().getFullYear()); });

  var trackPage = doc.body.getAttribute("data-track-page");
  if (trackPage) track("view_track", { track: trackPage, content_name: TRACK_NAMES[trackPage] || trackPage });
})();
