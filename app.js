import { launchCampaign, submitEnrollment } from "./launchCampaign.js";
import { initPlayground, activateLab } from "./playground.js";

const courses = [
  { id:"foundations", icon:"∑", level:"Beginner", title:"ML Foundations", description:"Understand the algorithms before you reach for a library.", tags:["Python","Scikit-learn","Regression"], modules:["Data, features, and train/test splits","Regression and gradient descent","Classification, trees, and evaluation","Model selection and practical pitfalls"], project:"Predict a real-world outcome and explain the model." },
  { id:"deep-learning", icon:"◈", level:"Intermediate", title:"Deep Learning & Vision", description:"Build neural networks and make images useful.", tags:["PyTorch","Computer Vision","CNNs"], modules:["Tensors, autograd, and training loops","Neural networks from scratch","Convolutional models for images","Transfer learning and model debugging"], project:"Train an image classifier with PyTorch." },
  { id:"nlp", icon:"⌘", level:"Intermediate", title:"NLP & Transformers", description:"Turn text into useful signals and understand attention.", tags:["NLP","Embeddings","Attention"], modules:["Tokenization and text features","Embeddings and semantic similarity","Attention and transformer intuition","Text classification and evaluation"], project:"Build a text classifier and inspect its errors." },
  { id:"rag", icon:"▤", level:"Advanced", title:"Build with RAG", description:"Connect language models to your own knowledge base.", tags:["RAG","Vector search","Evaluation"], modules:["Chunking and document preparation","Retrieval and vector similarity","Grounded generation and citations","Evaluate answers and failure cases"], project:"Create a grounded question-answering workflow." }
];
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));
const storageKey = "optimizerstep-preview-enrollments-v1";
const themeKey = "optimizerstep-theme-v1";
let localEntries = [];
let liveClaimed = null;
let toastTimer = null;
let toastHideTimer = null;
let sampleIndex = 0;
let toastMuted = false;

function readLocalEntries() {
  try { const parsed = JSON.parse(localStorage.getItem(storageKey) || "[]"); return Array.isArray(parsed) ? parsed : []; }
  catch { return []; }
}
function saveLocalEntries() {
  try { localStorage.setItem(storageKey, JSON.stringify(localEntries)); } catch { /* private browsing can block storage */ }
}
function cardMarkup(c) {
  return '<article class="course-card"><div class="course-top"><span class="course-icon" aria-hidden="true">' + c.icon + '</span><span class="course-level">' + c.level + '</span></div><h3>' + c.title + '</h3><p>' + c.description + '</p><div class="tag-row">' + c.tags.map((tag) => '<span>' + tag + '</span>').join("") + '</div><details><summary>Explore syllabus</summary><ul>' + c.modules.map((m) => '<li>' + m + '</li>').join("") + '</ul></details><p class="course-project"><strong>Build:</strong> ' + c.project + '</p><button class="button button-outline" type="button" data-enroll data-track="' + c.id + '">Start Free</button></article>';
}
function renderCourses() {
  $("#courseGrid").innerHTML = courses.map(cardMarkup).join("");
  const select = $("#enrollTrack");
  courses.forEach((c) => { const option = document.createElement("option"); option.value = c.id; option.textContent = c.title; select.append(option); });
}
function claimedSeats() {
  return Math.min(launchCampaign.capacity, launchCampaign.mode === "live" ? (liveClaimed ?? 0) : launchCampaign.demoClaimed + localEntries.length);
}
function updateSeats() {
  const claimed = claimedSeats();
  const remaining = Math.max(0, launchCampaign.capacity - claimed);
  $("#seatText").textContent = claimed + " / " + launchCampaign.capacity + " free seats claimed";
  $("#seatRemaining").textContent = remaining + " left";
  $("#seatBar").style.width = (claimed / launchCampaign.capacity * 100) + "%";
  $("#seatProgress").setAttribute("aria-valuenow", String(claimed));
  $("#regularPrice").textContent = "₹" + launchCampaign.plannedRegularPriceINR.toLocaleString("en-IN");
  $("#campaignDisclosure").textContent = launchCampaign.mode === "demo" ? "Preview counter — sample activity plus signups saved on this device." : "Verified enrollments from the live campaign.";
  $$("[data-enroll]").forEach((button) => { if (button.tagName === "BUTTON") button.disabled = remaining === 0; });
}
function showView(view, push = true) {
  const isPlayground = view === "playground";
  $("#homeView").hidden = isPlayground;
  $("#playgroundView").hidden = !isPlayground;
  $$("[data-playground]").forEach((a) => a.classList.toggle("active", isPlayground));
  $$("[data-home-link]").forEach((a) => a.classList.toggle("active", !isPlayground && a.getAttribute("href") === "#courses"));
  document.title = isPlayground ? "ML Playground — Optimizer Step" : "Optimizer Step — Learn AI by building it";
  if (push) history.pushState({view}, "", isPlayground ? "/playground" : "/");
  window.scrollTo({top:0,behavior:"instant"});
  if (isPlayground) initPlayground();
}
function openEnrollment(track) {
  if (track) $("#enrollTrack").value = track;
  $("#formError").hidden = true;
  $("#enrollFormView").hidden = false;
  $("#enrollSuccess").hidden = true;
  $("#enrollDialog").showModal();
  $("#enrollForm input[name=name]").focus();
}
function closeEnrollment() { $("#enrollDialog").close(); }
function validateEntry(form) {
  const name = form.elements.name.value.trim();
  const email = form.elements.email.value.trim().toLowerCase();
  const experience = form.elements.experience.value;
  const track = form.elements.track.value;
  if (name.length < 2) return {error:"Enter your full name."};
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return {error:"Enter a valid email address."};
  if (!experience || !track) return {error:"Choose your experience level and a course track."};
  if (localEntries.some((e) => e.email === email)) return {error:"This email already has a preview seat on this device."};
  return {name,email,experience,track,createdAt:new Date().toISOString()};
}
async function handleEnrollment(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const entry = validateEntry(form);
  const error = $("#formError");
  if (entry.error) { error.textContent = entry.error; error.hidden = false; return; }
  error.hidden = true;
  const submit = form.querySelector('[type="submit"]');
  submit.disabled = true;
  try {
    const result = await submitEnrollment(entry);
    if (result.mode === "demo") {
      localEntries.push(entry);
      saveLocalEntries();
    } else {
      liveClaimed = result.claimed;
    }
    updateSeats();
    $("#enrollFormView").hidden = true;
    $("#enrollSuccess").hidden = false;
    $("#successMessage").textContent = result.mode === "demo" ? "Your preview seat is saved on this device. Live enrollment and access details will appear when the launch backend is connected." : "Your founding seat is reserved. Check your email for the next steps.";
    form.reset();
  } catch (err) {
    error.textContent = err instanceof Error ? err.message : "Something went wrong. Please try again.";
    error.hidden = false;
  } finally { submit.disabled = false; }
}
function showToast() {
  if (toastMuted || launchCampaign.mode !== "demo") return;
  const item = launchCampaign.sampleActivity[sampleIndex % launchCampaign.sampleActivity.length];
  sampleIndex++;
  $("#toastTitle").textContent = item.name + " from " + item.city + " · sample signup";
  $("#toastMeta").textContent = "Example free seat #" + item.seat + " · " + item.minutesAgo + " mins ago";
  const toast = $("#enrollmentToast");
  toast.hidden = false;
  clearTimeout(toastHideTimer);
  toastHideTimer = setTimeout(() => { toast.hidden = true; }, 7200);
  scheduleToast();
}
function scheduleToast() {
  clearTimeout(toastTimer);
  toastTimer = setTimeout(showToast, 90000 + Math.random() * 60000);
}
async function refreshLiveActivity() {
  if (launchCampaign.mode !== "live" || !launchCampaign.activityEndpoint) return;
  try {
    const response = await fetch(launchCampaign.activityEndpoint, {cache:"no-store"});
    if (!response.ok) return;
    const data = await response.json();
    if (Number.isInteger(data.claimed)) { liveClaimed = data.claimed; updateSeats(); }
  } catch { /* preserve last verified count */ }
}
function setupTheme() {
  let saved = null;
  try { saved = localStorage.getItem(themeKey); } catch {}
  if (saved === "light") document.documentElement.dataset.theme = "light";
  if (saved === "light") $("#themeToggle").setAttribute("aria-label", "Switch to dark mode");
  $("#themeToggle").addEventListener("click", () => {
    const light = document.documentElement.dataset.theme !== "light";
    document.documentElement.dataset.theme = light ? "light" : "dark";
    $("#themeToggle").setAttribute("aria-label", light ? "Switch to dark mode" : "Switch to light mode");
    try { localStorage.setItem(themeKey, light ? "light" : "dark"); } catch {}
  });
}
function setupNavigation() {
  document.addEventListener("click", (event) => {
    const playgroundLink = event.target.closest("[data-playground]");
    if (playgroundLink) { event.preventDefault(); showView("playground"); return; }
    const homeLink = event.target.closest("[data-home]");
    if (homeLink) { event.preventDefault(); showView("home"); return; }
    const homeAnchor = event.target.closest("[data-home-link]");
    if (homeAnchor && $("#homeView").hidden) {
      event.preventDefault();
      showView("home");
      requestAnimationFrame(() => document.querySelector(homeAnchor.getAttribute("href"))?.scrollIntoView());
      return;
    }
    const enrollButton = event.target.closest("[data-enroll]");
    if (enrollButton) { event.preventDefault(); openEnrollment(enrollButton.dataset.track); }
  });
  window.addEventListener("popstate", () => showView(location.pathname === "/playground" ? "playground" : "home", false));
}
function setupDialog() {
  $("#enrollForm").addEventListener("submit", handleEnrollment);
  $("#dialogClose").addEventListener("click", closeEnrollment);
  $("#successClose").addEventListener("click", closeEnrollment);
  $("#enrollDialog").addEventListener("click", (event) => { if (event.target === $("#enrollDialog")) closeEnrollment(); });
}
function setupToasts() {
  $("#toastClose").addEventListener("click", () => { toastMuted = true; clearTimeout(toastTimer); clearTimeout(toastHideTimer); $("#enrollmentToast").hidden = true; });
  if (launchCampaign.mode === "demo") toastTimer = setTimeout(showToast, 8000);
  else { refreshLiveActivity(); setInterval(refreshLiveActivity, 30000); }
}
function setupLabs() {
  $$("[data-lab]").forEach((button) => button.addEventListener("click", () => activateLab(button.dataset.lab)));
}
localEntries = readLocalEntries();
renderCourses();
updateSeats();
setupTheme();
setupNavigation();
setupDialog();
setupToasts();
setupLabs();
showView(location.pathname === "/playground" ? "playground" : "home", false);
