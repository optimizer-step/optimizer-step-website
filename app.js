
const $ = (s, scope = document) => scope.querySelector(s);
const $$ = (s, scope = document) => [...scope.querySelectorAll(s)];

const mobileToggle = $('.mobile-toggle');
const mobileMenu = $('.mobile-menu');
function setMenu(open) {
  mobileMenu.hidden = !open;
  mobileToggle.setAttribute('aria-expanded', String(open));
  mobileToggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
}
mobileToggle.addEventListener('click', () => setMenu(mobileMenu.hidden));
$$('.mobile-menu a').forEach(a => a.addEventListener('click', () => setMenu(false)));
const mobileLayout = window.matchMedia('(max-width: 680px)');
mobileLayout.addEventListener('change', () => setMenu(false));
document.addEventListener('click', event => {
  if (!mobileMenu.hidden && !event.target.closest('.site-header')) setMenu(false);
});

// Progressive enhancement: both assistants remain available if JavaScript is unavailable.
const demoTabs = $$('.demo-tab');
const demoTablist = $('.demo-tabs');
demoTablist.hidden = false;
demoTablist.setAttribute('role', 'tablist');
$('.demo-grid').classList.add('tabs-ready');
function selectDemo(tab, focus = false) {
  demoTabs.forEach(item => {
    const selected = item === tab;
    const panel = document.getElementById(item.getAttribute('aria-controls'));
    item.classList.toggle('active', selected);
    item.setAttribute('role', 'tab');
    item.setAttribute('aria-selected', String(selected));
    item.tabIndex = selected ? 0 : -1;
    panel.hidden = !selected;
    panel.setAttribute('role', 'tabpanel');
    panel.setAttribute('aria-labelledby', item.id);
    panel.tabIndex = 0;
  });
  if (focus) tab.focus();
  document.dispatchEvent(new CustomEvent('demochange', { detail: tab.id }));
}
demoTabs.forEach((tab, index) => {
  tab.addEventListener('click', () => selectDemo(tab));
  tab.addEventListener('keydown', event => {
    let next;
    if (['ArrowDown', 'ArrowRight'].includes(event.key)) next = (index + 1) % demoTabs.length;
    if (['ArrowUp', 'ArrowLeft'].includes(event.key)) next = (index + demoTabs.length - 1) % demoTabs.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = demoTabs.length - 1;
    if (next !== undefined) { event.preventDefault(); selectDemo(demoTabs[next], true); }
  });
});
selectDemo(demoTabs[0]);
const stackedDemos = window.matchMedia('(min-width: 901px)');
function updateTabOrientation() { demoTablist.setAttribute('aria-orientation', stackedDemos.matches ? 'vertical' : 'horizontal'); }
stackedDemos.addEventListener('change', updateTabOrientation);
updateTabOrientation();
function openLinkedDetails() {
  if (window.location.hash === '#technology') $('#technology').open = true;
}
window.addEventListener('hashchange', openLinkedDetails);
openLinkedDetails();

function appendMessage(container, text, who = 'bot') {
  const row = document.createElement('div');
  row.className = `chat-msg ${who}`;
  if (who === 'bot') {
    const av = document.createElement('div');
    av.className = 'avatar';
    av.textContent = 'AI';
    row.appendChild(av);
  }
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;
  row.appendChild(bubble);
  container.appendChild(row);
  container.scrollTop = container.scrollHeight;
}

const inlineForm = $('#inlineChatForm');
const inlineInput = $('#inlineChatInput');
const inlineChat = $('#inlineChat');
const floatingButton = $('#floatingChatButton');
const floating = $('#floatingChat');
const closeFloating = $('#closeFloatingChat');
const floatingForm = $('#floatingChatForm');
const floatingInput = $('#floatingChatInput');
const floatingBody = $('#floatingChatBody');

function setFloating(open) {
  floating.classList.toggle('open', open);
  floating.hidden = !open;
  floating.setAttribute('aria-hidden', String(!open));
  floatingButton.setAttribute('aria-expanded', String(open));
  floatingButton.setAttribute('aria-label', open ? 'Close AI assistant' : 'Open AI assistant');
  if (open) (floatingInput.disabled ? closeFloating : floatingInput).focus();
  else floatingButton.focus();
}
floatingButton?.addEventListener('click', () => setFloating(!floating.classList.contains('open')));
closeFloating?.addEventListener('click', () => setFloating(false));
document.addEventListener('keydown', event => {
  if (event.key !== 'Escape') return;
  if (!floating.hidden) setFloating(false);
  if (!mobileMenu.hidden) { setMenu(false); mobileToggle.focus(); }
});
// Both chat surfaces share one conversation and the same server allowance.
let chatBusy = false;
let chatRemaining = null;
let chatStatusError = '';
const chatHistory = [];
const chatPanels = [inlineChat, floatingBody];
const chatControls = [inlineInput, floatingInput, ...$$('#inlineChatForm button, #floatingChatForm button, .quick-prompts button')];
const chatNotes = [inlineForm, floatingForm].map(form => {
  const note = document.createElement('p');
  note.className = 'chat-allowance';
  note.setAttribute('role', 'status');
  note.setAttribute('aria-live', 'polite');
  form.after(note);
  return note;
});
[inlineInput, floatingInput].forEach(input => input.maxLength = 800);
function updateChatState(note) {
  chatControls.forEach(control => control.disabled = chatBusy || chatRemaining === 0);
  const text = note || (chatBusy ? 'Thinking...' : chatStatusError || (chatRemaining === 0
    ? 'Daily chat limit reached. Please come back tomorrow (UTC).'
    : `${chatRemaining ?? 4} AI replies available today. Refreshing does not reset the limit.`));
  chatNotes.forEach(el => el.textContent = text);
}
async function refreshChatAllowance() {
  try {
    const response = await fetch('/api/chat/status', { cache: 'no-store' });
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Chat is temporarily unavailable.');
    chatRemaining = data.remaining;
    chatStatusError = '';
    updateChatState();
  } catch (error) {
    chatStatusError = 'Chat is temporarily unavailable. Please try again later.';
    updateChatState();
  }
}
async function sendChat(question) {
  const text = question.trim();
  if (!text || chatBusy || chatRemaining === 0) return;
  if (text.length > 800) { updateChatState('Please keep your message under 800 characters.'); return; }
  chatBusy = true;
  chatStatusError = '';
  updateChatState();
  $('.quick-prompts').hidden = true;
  chatPanels.forEach(panel => panel.setAttribute('aria-busy', 'true'));
  chatPanels.forEach(panel => appendMessage(panel, text, 'user'));
  inlineInput.value = '';
  floatingInput.value = '';
  try {
    const response = await fetch('/api/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: chatHistory.slice(-6) }),
      signal: AbortSignal.timeout(30000),
    });
    const data = await response.json();
    if (typeof data.remaining === 'number') chatRemaining = data.remaining;
    if (!response.ok) {
      if (response.status === 429) chatRemaining = 0;
      throw new Error(typeof data.detail === 'string' ? data.detail : 'Chat is unavailable. Please try again later.');
    }
    chatPanels.forEach(panel => appendMessage(panel, data.reply));
    chatHistory.push({ role: 'user', content: text }, { role: 'assistant', content: data.reply.slice(0, 1600) });
    updateChatState();
  } catch (error) {
    const message = error.name === 'TimeoutError'
      ? 'The reply timed out. This attempt may count toward your daily allowance.'
      : error.message || 'Could not connect to chat.';
    chatPanels.forEach(panel => appendMessage(panel, message, 'notice'));
    await refreshChatAllowance();
  } finally {
    chatBusy = false;
    chatPanels.forEach(panel => panel.setAttribute('aria-busy', 'false'));
    updateChatState();
  }
}
inlineForm?.addEventListener('submit', event => { event.preventDefault(); sendChat(inlineInput.value); });
floatingForm?.addEventListener('submit', event => { event.preventDefault(); sendChat(floatingInput.value); });
$$('.quick-prompts button').forEach(button => button.addEventListener('click', () => sendChat(button.dataset.question)));
updateChatState();
refreshChatAllowance();

const volume = $('#roiVolume');
const minutes = $('#roiMinutes');
const rate = $('#roiRate');
const volumeVal = $('#roiVolumeValue');
const minutesVal = $('#roiMinutesValue');
const rateVal = $('#roiRateValue');
const hoursVal = $('#roiHours');
const costVal = $('#roiCost');

function formatINR(n) {
  return new Intl.NumberFormat('en-IN', { style:'currency', currency:'INR', maximumFractionDigits:0 }).format(n);
}
function updateROI() {
  const v = +volume.value;
  const m = +minutes.value;
  const r = +rate.value;
  const hours = (v * m) / 60;
  const cost = hours * r;
  volumeVal.textContent = v.toLocaleString('en-IN');
  minutesVal.textContent = `${m} min`;
  rateVal.textContent = formatINR(r);
  volume.setAttribute('aria-valuetext', `${v.toLocaleString('en-IN')} tasks per month`);
  minutes.setAttribute('aria-valuetext', `${m} minutes per task`);
  rate.setAttribute('aria-valuetext', `${formatINR(r)} per hour`);
  hoursVal.textContent = Math.round(hours).toLocaleString('en-IN');
  costVal.textContent = formatINR(cost);
}
[volume, minutes, rate].forEach(x => x?.addEventListener('input', updateROI));
updateROI();

const contactForm = $('#contactForm');
const formNote = $('#formNote');
const formButton = $('button[type="submit"]', contactForm);
const formNoteDefault = formNote.textContent;
contactForm.addEventListener('submit', async e => {
  e.preventDefault();
  const values = Object.fromEntries(new FormData(contactForm));
  formButton.disabled = true;
  formNote.classList.remove('success', 'error');
  formNote.textContent = 'Sending your request...';
  try {
    const response = await fetch('/api/enquiry', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values), signal: AbortSignal.timeout(20000),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(response.status === 422 ? 'Please check your details and try again.'
        : typeof data.detail === 'string' ? data.detail : 'Could not send your request. Please try again.');
    }
    contactForm.reset();
    formNote.textContent = `Thank you, ${values.name.trim()}. We have received your request and will reply to ${values.email.trim()}.`;
    formNote.classList.add('success');
  } catch (error) {
    formNote.textContent = error.name === 'TimeoutError' ? 'Sending timed out. Please try again.'
      : error instanceof TypeError ? 'Could not reach the server. Please try again.' : error.message;
    formNote.classList.add('error');
  } finally {
    formButton.disabled = false;
  }
});
contactForm.addEventListener('input', () => {
  formNote.textContent = formNoteDefault;
  formNote.classList.remove('success', 'error');
});
