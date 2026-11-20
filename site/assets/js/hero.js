/* Optimizer Step — homepage hero: a short "training run" in the code window.
 * The final, converged state is in the HTML, so the panel looks right with no JS or with reduced motion. */
(function () {
  "use strict";
  var visual = document.querySelector("[data-hero-visual]");
  if (!visual || !document.documentElement.classList.contains("js")) return;

  var path = visual.querySelector(".loss-line");
  var dot = visual.querySelector(".loss-dot");
  var epochEl = visual.querySelector("[data-epoch]");
  var lossEl = visual.querySelector("[data-loss]");
  var deltaEl = visual.querySelector("[data-delta]");
  var accEl = visual.querySelector("[data-acc]");
  var statusEl = visual.querySelector("[data-status]");
  var badgeEl = visual.querySelector("[data-badge]");

  var START_LOSS = 0.31, END_LOSS = 0.0248, START_ACC = 61.0, END_ACC = 97.6, DURATION = 3600;

  function finish() {
    if (path) path.style.strokeDashoffset = "";
    visual.classList.remove("is-training");
    visual.classList.add("is-done");
    if (epochEl) epochEl.textContent = "100";
    if (lossEl) lossEl.textContent = END_LOSS.toFixed(4);
    if (deltaEl) deltaEl.textContent = "↓ " + Math.round((1 - END_LOSS / START_LOSS) * 100) + "%";
    if (accEl) accEl.textContent = END_ACC.toFixed(1) + "%";
    if (statusEl) statusEl.textContent = "Converged";
    if (badgeEl) badgeEl.textContent = "✓ CONVERGED";
  }

  if (!path || window.matchMedia("(prefers-reduced-motion: reduce)").matches) { finish(); return; }

  var total = 0;
  try { total = path.getTotalLength(); } catch (e) { finish(); return; }
  var decay = 5;
  var norm = 1 - Math.exp(-decay);

  function render(p) {
    var lossShape = (Math.exp(-decay * p) - Math.exp(-decay)) / norm;
    var loss = END_LOSS + (START_LOSS - END_LOSS) * lossShape;
    path.style.strokeDashoffset = String(1 - p);
    if (dot && total) {
      var pt = path.getPointAtLength(total * p);
      dot.setAttribute("cx", pt.x.toFixed(1));
      dot.setAttribute("cy", pt.y.toFixed(1));
      dot.style.opacity = "1";
    }
    if (epochEl) epochEl.textContent = String(Math.round(p * 100)).padStart(3, "0");
    if (lossEl) lossEl.textContent = loss.toFixed(4);
    if (deltaEl) deltaEl.textContent = "↓ " + Math.max(0, Math.round((1 - loss / START_LOSS) * 100)) + "%";
    if (accEl) accEl.textContent = (START_ACC + (END_ACC - START_ACC) * (1 - lossShape)).toFixed(1) + "%";
  }

  var started = false;
  function start() {
    if (started) return;
    started = true;
    visual.classList.add("is-training");
    if (statusEl) statusEl.textContent = "Training";
    if (badgeEl) badgeEl.textContent = "● TRAINING";
    var t0 = performance.now();
    function frame(now) {
      var t = Math.min(1, (now - t0) / DURATION);
      render(1 - Math.pow(1 - t, 3));
      if (t < 1) requestAnimationFrame(frame); else finish();
    }
    requestAnimationFrame(frame);
  }

  // Show the starting state, then train once the panel is on screen.
  render(0);
  if (dot) dot.style.opacity = "0";
  if (statusEl) statusEl.textContent = "Ready";
  if (badgeEl) badgeEl.textContent = "● READY";
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      if (entries.some(function (e) { return e.isIntersecting; })) { io.disconnect(); setTimeout(start, 350); }
    }, { threshold: 0.35 });
    io.observe(visual);
  } else {
    start();
  }
})();
