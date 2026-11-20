/**
 * Optimizer Step — Founding 100 enrollment backend.
 *
 * A Google Apps Script web app bound to the "Optimizer Step — Founding 100 signups"
 * spreadsheet. The static site on GitHub Pages calls it directly from the browser.
 *
 *   GET  <web app URL>?action=stats   -> { ok, claimed, capacity, remaining, open }
 *   POST <web app URL>                -> { ok, accepted, duplicate, status, seat, claimed, capacity, remaining, open }
 *        body: JSON sent as text/plain (no CORS preflight)
 *        { name, email, track, experience, company (honeypot), page, device, elapsedMs, attribution: {...} }
 *
 * Seats are handed out inside a script lock, so two people can never get the same seat.
 * The first `capacity` signups (Settings sheet) are "founding"; everyone after that is "waitlist".
 * To exclude a row from the counts (a test or spam entry), change its Status to "removed".
 *
 * @OnlyCurrentDoc
 */

const SIGNUPS_SHEET = 'Signups';
const SETTINGS_SHEET = 'Settings';
const HEADERS = [
  'Timestamp', 'Status', 'Seat', 'Name', 'Email', 'Track', 'Experience',
  'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'Click ID',
  'Referrer', 'Landing page', 'First touch', 'Signup page', 'Device', 'Email sent', 'Flags'
];
const COL = HEADERS.reduce(function (map, header, index) { map[header] = index + 1; return map; }, {});

const TRACKS = {
  'foundations': 'ML Foundations',
  'deep-learning': 'Deep Learning & Vision',
  'nlp': 'NLP & Transformers',
  'rag': 'Build with RAG',
  'undecided': 'Not sure yet'
};
const EXPERIENCE = ['Just starting', 'Know some Python', 'Building ML projects'];

const DEFAULT_SETTINGS = {
  capacity: 100,
  campaign_open: true,
  send_emails: true,
  from_name: 'Optimizer Step',
  reply_to: 'admin@optimizerstep.com',
  site_url: 'https://www.optimizerstep.com',
  youtube_url: 'https://www.youtube.com/@optimizerstep'
};
const SETTING_NOTES = {
  capacity: 'Number of free founding seats. Signups after this join the waitlist.',
  campaign_open: 'Set to FALSE to pause new signups (the site shows a "paused" message).',
  send_emails: 'Set to FALSE to stop confirmation emails.',
  from_name: 'Sender name on confirmation emails.',
  reply_to: 'Where student replies to the confirmation email go.',
  site_url: 'Website address used in email links.',
  youtube_url: 'YouTube link used in the email.'
};

const STATS_CACHE_SECONDS = 30;
const SETTINGS_CACHE_SECONDS = 60;
const FLOOD_LIMIT_PER_MINUTE = 150;

/* ------------------------------------------------------------------ */
/* Web app entry points                                                */
/* ------------------------------------------------------------------ */

function doGet(e) {
  const action = String((e && e.parameter && e.parameter.action) || 'stats');
  try {
    if (action === 'stats') {
      const stats = getStats_(false);
      return json_({ ok: true, claimed: stats.claimed, capacity: stats.capacity, remaining: stats.remaining, open: stats.open });
    }
    if (action === 'health') return json_({ ok: true, time: new Date().toISOString() });
    return json_({ ok: false, error: 'Unknown action.' });
  } catch (err) {
    console.error(err);
    return json_({ ok: false, error: 'The enrollment service is temporarily unavailable.' });
  }
}

function doPost(e) {
  let data;
  try {
    data = JSON.parse((e && e.postData && e.postData.contents) || '{}') || {};
  } catch (err) {
    return json_({ ok: false, error: 'We could not read that request. Please try again.' });
  }

  // Bots fill the hidden "company" field: answer like a success, store nothing.
  if (String(data.company || '').trim()) {
    return json_({ ok: true, accepted: true, duplicate: false, status: 'founding', seat: 0 });
  }

  const entry = validate_(data);
  if (entry.error) return json_({ ok: false, error: entry.error, field: entry.field });

  if (isFlooded_()) {
    return json_({ ok: false, error: 'Lots of people are signing up right now. Please try again in a minute.' });
  }

  const settings = getSettings_();
  if (!settings.campaign_open) {
    return json_({ ok: false, error: 'Signups are paused for a moment. Please try again soon.' });
  }

  const lock = LockService.getScriptLock();
  if (!lock.tryLock(25000)) {
    return json_({ ok: false, error: 'The server is busy. Please try again.' });
  }

  let result;
  try {
    const sheet = signupsSheet_();
    const existing = findByEmail_(sheet, entry.email);
    if (existing) {
      result = { duplicate: true, status: existing.status, seat: existing.seat, row: existing.row };
    } else {
      const counts = countStatuses_(sheet);
      const status = counts.founding < settings.capacity ? 'founding' : 'waitlist';
      const seat = status === 'founding' ? counts.founding + 1 : counts.waitlist + 1;
      sheet.appendRow(rowFor_(entry, status, seat));
      SpreadsheetApp.flush();
      result = { duplicate: false, status: status, seat: seat, row: sheet.getLastRow() };
    }
  } catch (err) {
    console.error(err);
    return json_({ ok: false, error: 'We could not save your seat. Please try again.' });
  } finally {
    lock.releaseLock();
  }

  CacheService.getScriptCache().remove('stats');

  if (!result.duplicate && settings.send_emails) {
    let note = 'sent';
    try {
      sendConfirmation_(entry, result, settings);
    } catch (err) {
      note = 'failed: ' + String((err && err.message) || err).slice(0, 140);
      console.error(err);
    }
    try {
      signupsSheet_().getRange(result.row, COL['Email sent']).setValue(note);
    } catch (err) {
      console.error(err);
    }
  }

  const stats = getStats_(true);
  return json_({
    ok: true,
    accepted: true,
    duplicate: result.duplicate,
    status: result.status,
    seat: result.seat,
    claimed: stats.claimed,
    capacity: stats.capacity,
    remaining: stats.remaining,
    open: stats.open
  });
}

/* ------------------------------------------------------------------ */
/* One-time setup (run from the editor)                                */
/* ------------------------------------------------------------------ */

function setup() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  ss.setSpreadsheetTimeZone('Asia/Kolkata');

  let sheet = ss.getSheetByName(SIGNUPS_SHEET);
  if (!sheet) {
    const first = ss.getSheets()[0];
    if (first && first.getLastRow() === 0 && first.getLastColumn() === 0) {
      sheet = first.setName(SIGNUPS_SHEET);
    } else {
      sheet = ss.insertSheet(SIGNUPS_SHEET, 0);
    }
  }
  sheet.getRange(1, 1, 1, HEADERS.length)
    .setValues([HEADERS])
    .setFontWeight('bold')
    .setBackground('#101522')
    .setFontColor('#ffffff');
  sheet.setFrozenRows(1);
  sheet.getRange('A:A').setNumberFormat('dd mmm yyyy, hh:mm');
  const widths = { Timestamp: 150, Status: 90, Seat: 60, Name: 170, Email: 230, Track: 170, Experience: 150, 'Landing page': 220, 'First touch': 220, 'Signup page': 140, 'Email sent': 110 };
  Object.keys(widths).forEach(function (header) { sheet.setColumnWidth(COL[header], widths[header]); });

  let settings = ss.getSheetByName(SETTINGS_SHEET);
  if (!settings) settings = ss.insertSheet(SETTINGS_SHEET);
  if (settings.getLastRow() < 2) {
    const rows = Object.keys(DEFAULT_SETTINGS).map(function (key) { return [key, DEFAULT_SETTINGS[key], SETTING_NOTES[key]]; });
    settings.getRange(1, 1, 1, 3).setValues([['Setting', 'Value', 'What it does']]).setFontWeight('bold');
    settings.getRange(2, 1, rows.length, 3).setValues(rows);
    settings.setColumnWidth(1, 150);
    settings.setColumnWidth(2, 260);
    settings.setColumnWidth(3, 480);
    settings.setFrozenRows(1);
  }

  CacheService.getScriptCache().removeAll(['stats', 'settings']);
  // Touching MailApp here makes Google ask for the send-email permission during setup.
  const quota = MailApp.getRemainingDailyQuota();
  Logger.log('Setup complete. Confirmation emails left today: ' + quota);
  return 'Setup complete';
}

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function validate_(d) {
  const name = clean_(d.name, 80);
  const email = clean_(d.email, 254).toLowerCase().replace(/\s+/g, '');
  const track = Object.prototype.hasOwnProperty.call(TRACKS, d.track) ? d.track : 'undecided';
  const experience = EXPERIENCE.indexOf(d.experience) >= 0 ? d.experience : '';

  if (name.length < 2) return { error: 'Please enter your name.', field: 'name' };
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return { error: 'Please enter a valid email address.', field: 'email' };
  if (!experience) return { error: 'Please choose your experience level.', field: 'experience' };

  const a = (d.attribution && typeof d.attribution === 'object') ? d.attribution : {};
  const clickKey = ['gclid', 'fbclid', 'gbraid', 'wbraid', 'msclkid', 'ttclid'].filter(function (k) { return a[k]; })[0];
  const elapsed = Number(d.elapsedMs);
  const flags = [];
  if (Number.isFinite(elapsed) && elapsed > 0 && elapsed < 2500) flags.push('fast-submit');

  return {
    name: name,
    email: email,
    track: track,
    experience: experience,
    utm_source: clean_(a.utm_source, 120),
    utm_medium: clean_(a.utm_medium, 120),
    utm_campaign: clean_(a.utm_campaign, 160),
    utm_content: clean_(a.utm_content, 160),
    utm_term: clean_(a.utm_term, 160),
    clickId: clickKey ? clickKey + ':' + clean_(a[clickKey], 200) : '',
    referrer: clean_(a.referrer, 300),
    landing: clean_(a.landing, 300),
    firstTouch: clean_(a.first_touch, 300),
    page: clean_(d.page, 200),
    device: clean_(d.device, 20),
    flags: flags.join(', ')
  };
}

function rowFor_(entry, status, seat) {
  const values = {
    'Timestamp': new Date(),
    'Status': status,
    'Seat': seat,
    'Name': entry.name,
    'Email': entry.email,
    'Track': TRACKS[entry.track],
    'Experience': entry.experience,
    'utm_source': entry.utm_source,
    'utm_medium': entry.utm_medium,
    'utm_campaign': entry.utm_campaign,
    'utm_content': entry.utm_content,
    'utm_term': entry.utm_term,
    'Click ID': entry.clickId,
    'Referrer': entry.referrer,
    'Landing page': entry.landing,
    'First touch': entry.firstTouch,
    'Signup page': entry.page,
    'Device': entry.device,
    'Email sent': '',
    'Flags': entry.flags
  };
  return HEADERS.map(function (header) {
    const value = values[header];
    return typeof value === 'string' ? safeCell_(value) : value;
  });
}

function clean_(value, max) {
  return String(value == null ? '' : value)
    .replace(/[\u0000-\u001f\u007f<>]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, max);
}

// Stop spreadsheet formula injection ("=HYPERLINK(...)" typed into a form field).
function safeCell_(text) {
  return /^[=+\-@]/.test(text) ? "'" + text : text;
}

function signupsSheet_() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SIGNUPS_SHEET);
  if (!sheet) throw new Error('Run setup() first: the Signups sheet is missing.');
  return sheet;
}

function findByEmail_(sheet, email) {
  const last = sheet.getLastRow();
  if (last < 2) return null;
  const hit = sheet.getRange(2, COL['Email'], last - 1, 1)
    .createTextFinder(email)
    .matchEntireCell(true)
    .matchCase(false)
    .findNext();
  if (!hit) return null;
  const row = hit.getRow();
  const values = sheet.getRange(row, 1, 1, HEADERS.length).getValues()[0];
  const status = String(values[COL['Status'] - 1] || '').toLowerCase();
  if (status === 'removed') return null;
  return { row: row, status: status === 'waitlist' ? 'waitlist' : 'founding', seat: Number(values[COL['Seat'] - 1]) || 0 };
}

function countStatuses_(sheet) {
  const counts = { founding: 0, waitlist: 0 };
  const last = sheet.getLastRow();
  if (last < 2) return counts;
  sheet.getRange(2, COL['Status'], last - 1, 1).getValues().forEach(function (row) {
    const status = String(row[0]).toLowerCase();
    if (status === 'founding') counts.founding++;
    else if (status === 'waitlist') counts.waitlist++;
  });
  return counts;
}

function getStats_(fresh) {
  const cache = CacheService.getScriptCache();
  if (!fresh) {
    const hit = cache.get('stats');
    if (hit) return JSON.parse(hit);
  }
  const settings = getSettings_();
  const counts = countStatuses_(signupsSheet_());
  const stats = {
    claimed: Math.min(counts.founding, settings.capacity),
    capacity: settings.capacity,
    remaining: Math.max(0, settings.capacity - counts.founding),
    open: Boolean(settings.campaign_open)
  };
  cache.put('stats', JSON.stringify(stats), STATS_CACHE_SECONDS);
  return stats;
}

function getSettings_() {
  const cache = CacheService.getScriptCache();
  const hit = cache.get('settings');
  if (hit) return JSON.parse(hit);

  const settings = Object.assign({}, DEFAULT_SETTINGS);
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SETTINGS_SHEET);
  if (sheet && sheet.getLastRow() >= 2) {
    sheet.getRange(2, 1, sheet.getLastRow() - 1, 2).getValues().forEach(function (row) {
      const key = String(row[0] || '').trim();
      const value = row[1];
      if (!Object.prototype.hasOwnProperty.call(DEFAULT_SETTINGS, key)) return;
      const fallback = DEFAULT_SETTINGS[key];
      if (typeof fallback === 'number') {
        const n = Number(value);
        if (Number.isFinite(n) && n >= 0) settings[key] = Math.floor(n);
      } else if (typeof fallback === 'boolean') {
        settings[key] = value === true || String(value).trim().toUpperCase() === 'TRUE';
      } else if (String(value).trim()) {
        settings[key] = String(value).trim();
      }
    });
  }
  cache.put('settings', JSON.stringify(settings), SETTINGS_CACHE_SECONDS);
  return settings;
}

function isFlooded_() {
  const cache = CacheService.getScriptCache();
  const key = 'flood:' + Math.floor(Date.now() / 60000);
  const count = Number(cache.get(key) || 0) + 1;
  cache.put(key, String(count), 120);
  return count > FLOOD_LIMIT_PER_MINUTE;
}

function json_(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload)).setMimeType(ContentService.MimeType.JSON);
}

function escapeHtml_(text) {
  return String(text).replace(/[&<>"']/g, function (ch) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch];
  });
}

/* ------------------------------------------------------------------ */
/* Confirmation email                                                  */
/* ------------------------------------------------------------------ */

function sendConfirmation_(entry, result, settings) {
  const firstName = entry.name.split(' ')[0];
  const trackName = TRACKS[entry.track];
  const site = settings.site_url.replace(/\/+$/, '');
  const playground = site + '/playground/?utm_source=email&utm_medium=confirmation&utm_campaign=founding100';
  const youtube = settings.youtube_url;
  const founding = result.status === 'founding';

  const subject = founding
    ? 'Your free founding seat is confirmed (#' + result.seat + ')'
    : 'You are on the Optimizer Step waitlist (#' + result.seat + ')';

  const intro = founding
    ? 'Your Optimizer Step founding seat is confirmed. You are founding student #' + result.seat + ' of ' + settings.capacity + ', and your seat is free. No payment is needed.'
    : 'All ' + settings.capacity + ' free founding seats have been claimed, so you are #' + result.seat + ' on the waitlist. We will email you as soon as more seats open.';

  const trackLine = entry.track === 'undecided'
    ? 'You have not picked a track yet. Reply to this email with what you want to build and we will help you choose.'
    : 'Your track: ' + trackName + '.';

  const steps = [
    'The tracks open in stages. We will email you the start date for your track before it opens.',
    'While you wait, try the free ML Playground: ' + playground,
    'Free lessons on YouTube: ' + youtube
  ];

  const text = [
    'Hi ' + firstName + ',',
    '',
    intro,
    '',
    trackLine,
    '',
    'What happens next:',
    steps.map(function (s) { return '- ' + s; }).join('\n'),
    '',
    'Questions? Just reply to this email.',
    '',
    'Venkatesh',
    'Optimizer Step',
    '',
    'You are getting this email because you claimed a seat at optimizerstep.com. If that was not you, reply and we will delete your details.'
  ].join('\n');

  const p = 'margin:0 0 16px;font-size:16px;line-height:1.6;color:#1d2433;';
  const html = [
    '<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;max-width:560px;margin:0 auto;padding:8px 4px;">',
    '<p style="' + p + '">Hi ' + escapeHtml_(firstName) + ',</p>',
    '<p style="' + p + '">' + escapeHtml_(intro) + '</p>',
    '<p style="' + p + '"><strong>' + escapeHtml_(trackLine) + '</strong></p>',
    '<p style="' + p + 'margin-bottom:8px;"><strong>What happens next</strong></p>',
    '<ul style="margin:0 0 20px;padding-left:20px;font-size:16px;line-height:1.6;color:#1d2433;">',
    '<li style="margin-bottom:6px;">The tracks open in stages. We will email you the start date for your track before it opens.</li>',
    '<li style="margin-bottom:6px;">While you wait, try the free <a href="' + playground + '" style="color:#5b3fd6;">ML Playground</a>: move a point and watch a model learn.</li>',
    '<li style="margin-bottom:6px;">Watch free lessons on the <a href="' + youtube + '" style="color:#5b3fd6;">Optimizer Step YouTube channel</a>.</li>',
    '</ul>',
    '<p style="margin:0 0 24px;"><a href="' + playground + '" style="display:inline-block;background:#6b4fe3;color:#ffffff;text-decoration:none;font-weight:600;padding:12px 20px;border-radius:8px;font-size:15px;">Open the ML Playground</a></p>',
    '<p style="' + p + '">Questions? Just reply to this email.</p>',
    '<p style="' + p + '">Venkatesh<br>Optimizer Step</p>',
    '<p style="margin:24px 0 0;font-size:12px;line-height:1.5;color:#6b7280;">You are getting this email because you claimed a seat at optimizerstep.com. If that was not you, reply and we will delete your details.</p>',
    '</div>'
  ].join('');

  MailApp.sendEmail({
    to: entry.email,
    subject: subject,
    body: text,
    htmlBody: html,
    name: settings.from_name,
    replyTo: settings.reply_to
  });
}
