/*
 * Optimizer Step — ML Playground labs (browser only: JavaScript math + Canvas).
 * Each lab page sets <body data-lab="regression|boundary|clusters|attention">; only that lab starts.
 */
(function () {
  "use strict";

  function $(s) { return document.querySelector(s); }
  function $$(s) { return Array.prototype.slice.call(document.querySelectorAll(s)); }
  var palette = ["#aa95ff", "#ff9aab", "#76e2c8", "#f9c978", "#83bcff", "#e6a6f7"];
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var interacted = {};

  function noteInteraction(lab) {
    if (interacted[lab]) return;
    interacted[lab] = true;
    if (window.OS) window.OS.track("playground_interaction", { lab: lab });
  }
  function canvasPoint(canvas, event) {
    var rect = canvas.getBoundingClientRect();
    return { x: (event.clientX - rect.left) / rect.width * canvas.width, y: (event.clientY - rect.top) / rect.height * canvas.height };
  }
  function plotGrid(ctx, w, h) {
    ctx.fillStyle = "#101523"; ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = "#293248"; ctx.lineWidth = 1;
    for (var x = 0; x <= w; x += 60) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
    for (var y = 0; y <= h; y += 54) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
  }
  function dot(ctx, x, y, color, r) {
    ctx.beginPath(); ctx.arc(x, y, r || 7, 0, Math.PI * 2); ctx.fillStyle = color; ctx.fill();
    ctx.lineWidth = 2; ctx.strokeStyle = "#101523"; ctx.stroke();
  }
  function rand(min, max) { return min + Math.random() * (max - min); }
  function normal() { return (Math.random() + Math.random() + Math.random() + Math.random() - 2) / 2; }

  /* ---------------- Lab 1: gradient descent regression ---------------- */
  var reg = { points: [], weights: [0, 0, 0, 0, 0], step: 0, running: true, drag: -1, last: 0, onScreen: true };

  function regCoordinates(p) { return { x: p.x / 360 - 1, y: 1 - p.y / 215 }; }
  function regPrediction(x) {
    var degree = Number($("#degree").value), sum = 0;
    for (var j = 0; j <= degree; j++) sum += reg.weights[j] * Math.pow(x, j);
    return sum;
  }
  function regLoss() {
    if (!reg.points.length) return 0;
    var sum = 0;
    reg.points.forEach(function (p) { var c = regCoordinates(p), d = regPrediction(c.x) - c.y; sum += d * d; });
    return sum / reg.points.length;
  }
  function setRunning(running) {
    reg.running = running;
    $("#regRun").textContent = running ? "Pause training" : (reg.step ? "Resume training" : "Start training");
  }
  function regStep() {
    if (!reg.points.length) return;
    var degree = Number($("#degree").value), grad = [], rate = Number($("#learningRate").value), j;
    for (j = 0; j <= degree; j++) grad.push(0);
    reg.points.forEach(function (p) {
      var c = regCoordinates(p), error = regPrediction(c.x) - c.y;
      for (var k = 0; k <= degree; k++) grad[k] += 2 * error * Math.pow(c.x, k) / reg.points.length;
    });
    for (j = 0; j <= degree; j++) reg.weights[j] -= rate * grad[j];
    reg.step++;
    var loss = regLoss();
    if (!Number.isFinite(loss) || Math.abs(loss) > 1e9) setRunning(false);
  }
  function drawRegression() {
    var c = $("#regressionCanvas"), ctx = c.getContext("2d");
    plotGrid(ctx, c.width, c.height);
    ctx.strokeStyle = "#4d5066"; ctx.lineWidth = 2; ctx.setLineDash([5, 5]);
    ctx.beginPath(); ctx.moveTo(0, c.height / 2); ctx.lineTo(c.width, c.height / 2); ctx.stroke(); ctx.setLineDash([]);
    ctx.strokeStyle = "#b6a4ff"; ctx.lineWidth = 4; ctx.beginPath();
    for (var px = 0; px < c.width; px += 3) {
      var y = regPrediction(px / 360 - 1), py = (1 - y) * 215;
      if (px === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.stroke();
    reg.points.forEach(function (p, i) { dot(ctx, p.x, p.y, i === reg.drag ? "#fff" : palette[0], 8); });
    var loss = regLoss();
    $("#regLoss").textContent = !Number.isFinite(loss) || loss > 1e6 ? "Exploding" : loss.toFixed(4);
    $("#regSteps").textContent = String(reg.step);
    $("#regInsight").textContent = !Number.isFinite(loss) || loss > 10
      ? "The learning rate is too high: each update overshoots and the loss explodes. Lower the rate or reset."
      : reg.step > 120 ? "The curve is settling. Drag a point and watch the optimizer adapt."
      : "Each step nudges the weights in the direction that reduces the loss.";
  }
  function animateRegression(time) {
    if (reg.running && reg.onScreen && time - reg.last > 45) {
      for (var i = 0; i < 3; i++) regStep();
      drawRegression();
      reg.last = time;
    }
    requestAnimationFrame(animateRegression);
  }
  function setRegressionPreset(type) {
    reg.weights = [0, 0, 0, 0, 0]; reg.step = 0;
    if (type === "linear") {
      reg.points = Array.from({ length: 15 }, function (_, i) { return { x: 55 + i * 43, y: 330 - i * 14 + normal() * 24 }; });
      $("#degree").value = "1"; $("#learningRate").value = "0.08";
    } else {
      reg.points = Array.from({ length: 17 }, function (_, i) { var x = -0.85 + i * 0.106; return { x: (x + 1) * 360, y: (1 - (0.6 * x * x - 0.38 + normal() * 0.13)) * 215 }; });
      $("#degree").value = "2"; $("#learningRate").value = type === "explode" ? "1.5" : "0.08";
    }
    $("#degreeValue").textContent = $("#degree").value;
    $("#lrValue").textContent = Number($("#learningRate").value).toFixed(3);
    setRunning(!reduceMotion || reg.running);
    drawRegression();
  }
  function setupRegression() {
    var c = $("#regressionCanvas");
    c.addEventListener("pointerdown", function (e) {
      noteInteraction("gradient-descent");
      var p = canvasPoint(c, e);
      var i = reg.points.findIndex(function (q) { return Math.hypot(q.x - p.x, q.y - p.y) < 18; });
      if (i >= 0) reg.drag = i; else { reg.points.push(p); reg.drag = reg.points.length - 1; }
      c.setPointerCapture(e.pointerId);
      drawRegression();
    });
    c.addEventListener("pointermove", function (e) {
      if (reg.drag < 0) return;
      var p = canvasPoint(c, e);
      reg.points[reg.drag] = { x: Math.max(0, Math.min(c.width, p.x)), y: Math.max(0, Math.min(c.height, p.y)) };
      drawRegression();
    });
    var release = function () { reg.drag = -1; };
    c.addEventListener("pointerup", release);
    c.addEventListener("pointercancel", release);
    $("#learningRate").addEventListener("input", function () { noteInteraction("gradient-descent"); $("#lrValue").textContent = Number($("#learningRate").value).toFixed(3); });
    $("#degree").addEventListener("input", function () { noteInteraction("gradient-descent"); reg.weights = [0, 0, 0, 0, 0]; reg.step = 0; $("#degreeValue").textContent = $("#degree").value; drawRegression(); });
    $("#regRun").addEventListener("click", function () { noteInteraction("gradient-descent"); setRunning(!reg.running); });
    $("#regReset").addEventListener("click", function () { noteInteraction("gradient-descent"); setRegressionPreset("curve"); });
    $$("[data-reg-preset]").forEach(function (b) { b.addEventListener("click", function () { noteInteraction("gradient-descent"); setRegressionPreset(b.getAttribute("data-reg-preset")); }); });
    reg.running = !reduceMotion;
    setRegressionPreset("curve");
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) { reg.onScreen = entries[0].isIntersecting; }).observe(c);
    }
    requestAnimationFrame(animateRegression);
  }

  /* ---------------- Lab 2: decision boundary ---------------- */
  var boundary = { points: [], classIndex: 0, algorithm: "knn", param: 5, model: null };

  function sigmoid(z) { return 1 / (1 + Math.exp(-Math.max(-30, Math.min(30, z)))); }
  function normXY(p) { return [p.x / 360 - 1, 1 - p.y / 215]; }
  function trainLogistic(points) {
    var w = [0, 0, 0], lambda = (Number($("#boundaryParam").value) - 1) / 100;
    for (var epoch = 0; epoch < 250; epoch++) {
      var g = [0, 0, 0];
      points.forEach(function (p) { var q = normXY(p), diff = sigmoid(w[0] + w[1] * q[0] + w[2] * q[1]) - p.classIndex; g[0] += diff; g[1] += diff * q[0]; g[2] += diff * q[1]; });
      for (var j = 0; j < 3; j++) w[j] -= 0.7 * (g[j] / points.length + (j ? lambda * w[j] : 0));
    }
    return w;
  }
  function neuralPredict(model, x, y) {
    var z = model.b;
    for (var i = 0; i < model.hidden; i++) { var h = Math.tanh(model.w1[i][0] * x + model.w1[i][1] * y + model.b1[i]); z += h * model.w2[i]; }
    return sigmoid(z);
  }
  function trainNeural(points, hidden) {
    var model = { hidden: hidden, w1: [], b1: [], w2: [], b: 0 }, i;
    for (i = 0; i < hidden; i++) { model.w1.push([rand(-1, 1), rand(-1, 1)]); model.b1.push(rand(-0.3, 0.3)); model.w2.push(rand(-1, 1)); }
    for (var epoch = 0; epoch < 320; epoch++) {
      points.forEach(function (p) {
        var q = normXY(p), x = q[0], y = q[1];
        var hs = model.w1.map(function (w, k) { return Math.tanh(w[0] * x + w[1] * y + model.b1[k]); });
        var output = sigmoid(model.b + hs.reduce(function (s, h, k) { return s + h * model.w2[k]; }, 0));
        var dz = output - p.classIndex, oldW2 = model.w2.slice();
        model.b -= 0.14 * dz;
        for (var k = 0; k < hidden; k++) {
          model.w2[k] -= 0.14 * dz * hs[k];
          var dh = dz * oldW2[k] * (1 - hs[k] * hs[k]);
          model.w1[k][0] -= 0.14 * dh * x; model.w1[k][1] -= 0.14 * dh * y; model.b1[k] -= 0.14 * dh;
        }
      });
    }
    return model;
  }
  function predictClass(x, y) {
    if (!boundary.points.length) return 0.5;
    if (boundary.algorithm === "knn") {
      var k = Math.min(boundary.param, boundary.points.length);
      var nearest = boundary.points.map(function (p) { var q = normXY(p); return { d: Math.pow(q[0] - x, 2) + Math.pow(q[1] - y, 2), c: p.classIndex }; })
        .sort(function (a, b) { return a.d - b.d; }).slice(0, k);
      return nearest.reduce(function (s, p) { return s + p.c; }, 0) / k;
    }
    if (boundary.algorithm === "logistic") { var w = boundary.model; return sigmoid(w[0] + w[1] * x + w[2] * y); }
    return neuralPredict(boundary.model, x, y);
  }
  function rebuildBoundary() {
    boundary.algorithm = $("#boundaryAlgorithm").value;
    boundary.param = Number($("#boundaryParam").value);
    if (boundary.points.length) {
      boundary.model = boundary.algorithm === "logistic" ? trainLogistic(boundary.points) : boundary.algorithm === "neural" ? trainNeural(boundary.points, boundary.param) : null;
    }
    drawBoundary();
  }
  function drawBoundary() {
    var c = $("#boundaryCanvas"), ctx = c.getContext("2d");
    plotGrid(ctx, c.width, c.height);
    if (boundary.points.length) {
      var cell = 12;
      for (var y = 0; y < c.height; y += cell) for (var x = 0; x < c.width; x += cell) {
        var p = predictClass((x + cell / 2) / 360 - 1, 1 - (y + cell / 2) / 215);
        ctx.fillStyle = p >= 0.5 ? "rgba(255,154,171,.20)" : "rgba(170,149,255,.22)";
        ctx.fillRect(x, y, cell, cell);
      }
    }
    boundary.points.forEach(function (p) { dot(ctx, p.x, p.y, palette[p.classIndex], 8); });
    $("#boundaryPoints").textContent = String(boundary.points.length);
    var accurate = boundary.points.filter(function (p) { var q = normXY(p); return Number(predictClass(q[0], q[1]) >= 0.5) === p.classIndex; }).length;
    $("#boundaryAccuracy").textContent = boundary.points.length ? Math.round(accurate / boundary.points.length * 100) + "%" : "—";
    $("#boundaryInsight").textContent = boundary.algorithm === "knn"
      ? "KNN votes with the nearest examples. Raise K to smooth the boundary."
      : boundary.algorithm === "logistic" ? "Logistic regression learns one straight dividing line, so it cannot solve XOR."
      : "A small neural network combines nonlinear hidden units to bend the boundary.";
  }
  function boundaryPreset(type) {
    boundary.points = [];
    var i;
    if (type === "diagonal") for (i = 0; i < 30; i++) { var cls = i % 2; boundary.points.push({ x: cls ? rand(390, 640) : rand(75, 320), y: cls ? rand(80, 340) : rand(90, 360), classIndex: cls }); }
    if (type === "xor") for (i = 0; i < 40; i++) { var corner = i % 4; boundary.points.push({ x: (corner % 2 ? 500 : 200) + normal() * 75, y: (corner < 2 ? 115 : 315) + normal() * 55, classIndex: (corner === 1 || corner === 2) ? 1 : 0 }); }
    rebuildBoundary();
  }
  function setupBoundary() {
    var c = $("#boundaryCanvas");
    c.addEventListener("pointerdown", function (e) { noteInteraction("decision-boundary"); var p = canvasPoint(c, e); boundary.points.push({ x: p.x, y: p.y, classIndex: boundary.classIndex }); rebuildBoundary(); });
    $("#boundaryAlgorithm").addEventListener("change", function () {
      noteInteraction("decision-boundary");
      var alg = $("#boundaryAlgorithm").value, slider = $("#boundaryParam");
      slider.max = alg === "knn" ? "15" : alg === "logistic" ? "10" : "12";
      slider.min = alg === "neural" ? "2" : "1";
      slider.step = alg === "knn" ? "2" : "1";
      slider.value = alg === "knn" ? "5" : alg === "logistic" ? "3" : "6";
      $("#boundaryParamLabel").firstChild.textContent = alg === "knn" ? "Neighbours (K) " : alg === "logistic" ? "Regularization " : "Hidden units ";
      $("#boundaryParamValue").textContent = slider.value;
      rebuildBoundary();
    });
    $("#boundaryParam").addEventListener("input", function () { noteInteraction("decision-boundary"); $("#boundaryParamValue").textContent = $("#boundaryParam").value; rebuildBoundary(); });
    $$("[data-class]").forEach(function (b) {
      b.addEventListener("click", function () {
        boundary.classIndex = Number(b.getAttribute("data-class"));
        $$("[data-class]").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      });
    });
    $$("[data-boundary-preset]").forEach(function (b) { b.addEventListener("click", function () { noteInteraction("decision-boundary"); boundaryPreset(b.getAttribute("data-boundary-preset")); }); });
    boundaryPreset("diagonal");
  }

  /* ---------------- Lab 3: k-means ---------------- */
  var clusters = { points: [], centroids: [], k: 3, iteration: 0, auto: null, dataset: "blobs" };

  function datasetPoints(type) {
    var pts = [];
    for (var i = 0; i < 90; i++) {
      var x, y;
      if (type === "blobs") { var centers = [[175, 130], [520, 125], [350, 320]], center = centers[i % 3]; x = center[0] + normal() * 115; y = center[1] + normal() * 90; }
      else if (type === "rings") { var ring = i % 2, r = ring ? 155 : 70, a = rand(0, Math.PI * 2); x = 360 + Math.cos(a) * (r + normal() * 24); y = 215 + Math.sin(a) * (r + normal() * 24); }
      else { x = rand(35, 685); y = rand(35, 395); }
      pts.push({ x: Math.max(15, Math.min(705, x)), y: Math.max(15, Math.min(415, y)), cluster: -1 });
    }
    return pts;
  }
  function nearestCentroid(p) {
    var best = 0, bestDist = Infinity;
    clusters.centroids.forEach(function (c, i) { var d = Math.pow(p.x - c.x, 2) + Math.pow(p.y - c.y, 2); if (d < bestDist) { bestDist = d; best = i; } });
    return best;
  }
  function clusterInertia() {
    return clusters.points.reduce(function (sum, p) { var c = clusters.centroids[p.cluster < 0 ? nearestCentroid(p) : p.cluster]; return sum + Math.pow(p.x - c.x, 2) + Math.pow(p.y - c.y, 2); }, 0) / clusters.points.length;
  }
  function clusterStep() {
    clusters.points.forEach(function (p) { p.cluster = nearestCentroid(p); });
    clusters.centroids.forEach(function (c, i) {
      var group = clusters.points.filter(function (p) { return p.cluster === i; });
      if (group.length) { c.x = group.reduce(function (s, p) { return s + p.x; }, 0) / group.length; c.y = group.reduce(function (s, p) { return s + p.y; }, 0) / group.length; }
    });
    clusters.iteration++;
    drawClusters();
  }
  function drawClusters() {
    var c = $("#clusterCanvas"), ctx = c.getContext("2d");
    plotGrid(ctx, c.width, c.height);
    if (clusters.centroids.length) for (var y = 0; y < c.height; y += 18) for (var x = 0; x < c.width; x += 18) { var i = nearestCentroid({ x: x + 9, y: y + 9 }); ctx.fillStyle = palette[i] + "12"; ctx.fillRect(x, y, 18, 18); }
    clusters.points.forEach(function (p) { dot(ctx, p.x, p.y, p.cluster < 0 ? "#9ba3b9" : palette[p.cluster], 5); });
    clusters.centroids.forEach(function (p, i) { ctx.fillStyle = palette[i]; ctx.font = "bold 30px system-ui, sans-serif"; ctx.fillText("✦", p.x - 14, p.y + 10); });
    $("#clusterIteration").textContent = String(clusters.iteration);
    $("#clusterInertia").textContent = clusterInertia().toFixed(0);
    $("#clusterInsight").textContent = clusters.iteration > 5
      ? "The centroids have usually settled by now. Regenerate the data or change K to find another solution."
      : "Each step assigns points to the nearest centroid, then moves each centroid to the middle of its group.";
  }
  function stopClusterAuto() {
    if (clusters.auto) { clearInterval(clusters.auto); clusters.auto = null; $("#clusterAuto").textContent = "Auto-run"; }
  }
  function resetClusters() {
    stopClusterAuto();
    clusters.dataset = $("#clusterDataset").value;
    clusters.k = Number($("#clusterK").value);
    clusters.points = datasetPoints(clusters.dataset);
    clusters.centroids = Array.from({ length: clusters.k }, function () { return { x: rand(80, 640), y: rand(70, 360) }; });
    clusters.iteration = 0;
    drawClusters();
  }
  function setupClusters() {
    $("#clusterK").addEventListener("input", function () { noteInteraction("k-means"); $("#clusterKValue").textContent = $("#clusterK").value; resetClusters(); });
    $("#clusterDataset").addEventListener("change", function () { noteInteraction("k-means"); resetClusters(); });
    $("#clusterStep").addEventListener("click", function () { noteInteraction("k-means"); clusterStep(); });
    $("#clusterAuto").addEventListener("click", function () {
      noteInteraction("k-means");
      if (clusters.auto) stopClusterAuto();
      else { clusters.auto = setInterval(clusterStep, 650); $("#clusterAuto").textContent = "Pause"; }
    });
    $("#clusterReset").addEventListener("click", function () { noteInteraction("k-means"); resetClusters(); });
    resetClusters();
  }

  /* ---------------- Lab 4: attention ---------------- */
  var attention = { selected: 0 };

  function tokenFeatures(token) {
    var t = token.toLowerCase(), v = [], i;
    for (i = 0; i < 12; i++) v.push(0);
    for (i = 0; i < t.length; i++) { var code = t.charCodeAt(i); v[code % 12] += 1; v[(code + i * 3) % 12] += 0.45; }
    var norm = Math.hypot.apply(Math, v) || 1;
    return v.map(function (x) { return x / norm; });
  }
  function similarity(a, b) { return a.reduce(function (s, x, i) { return s + x * b[i]; }, 0); }
  function renderAttention() {
    var tokens = $("#attentionText").value.trim().split(/\s+/).filter(Boolean).slice(0, 12);
    attention.selected = Math.min(attention.selected, Math.max(0, tokens.length - 1));
    var list = $("#tokenList");
    list.replaceChildren();
    tokens.forEach(function (token, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = token;
      b.setAttribute("aria-pressed", String(i === attention.selected));
      b.addEventListener("click", function () { noteInteraction("attention"); attention.selected = i; renderAttention(); });
      list.append(b);
    });
    var bars = $("#attentionBars");
    bars.replaceChildren();
    var features = tokens.map(tokenFeatures), query = features[attention.selected] || [], sharpness = Number($("#attentionSharpness").value);
    var raw = features.map(function (f) { return Math.exp(sharpness * similarity(query, f)); });
    var total = raw.reduce(function (a, b) { return a + b; }, 0) || 1;
    var weights = raw.map(function (x) { return x / total; });
    weights.forEach(function (weight, i) {
      var row = document.createElement("div"); row.className = "attention-row";
      var name = document.createElement("span"); name.textContent = tokens[i];
      var bar = document.createElement("div"); bar.className = "bar";
      var fill = document.createElement("span"); fill.style.width = (weight * 100) + "%";
      bar.append(fill);
      var val = document.createElement("strong"); val.textContent = Math.round(weight * 100) + "%";
      row.append(name, bar, val);
      bars.append(row);
    });
    $("#attentionCount").textContent = String(tokens.length);
    var highest = weights.length ? weights.indexOf(Math.max.apply(Math, weights)) : -1;
    $("#attentionTop").textContent = highest >= 0 ? tokens[highest] : "—";
  }
  function setupAttention() {
    $("#attentionText").addEventListener("input", function () { noteInteraction("attention"); renderAttention(); });
    $("#attentionSharpness").addEventListener("input", function () { noteInteraction("attention"); $("#attentionSharpnessValue").textContent = $("#attentionSharpness").value; renderAttention(); });
    var phrases = { robot: "the curious robot learns from data", animals: "the cat watches the small kitten play", code: "python model learns patterns from python data" };
    $$("[data-attention-preset]").forEach(function (b) {
      b.addEventListener("click", function () { noteInteraction("attention"); $("#attentionText").value = phrases[b.getAttribute("data-attention-preset")]; attention.selected = 0; renderAttention(); });
    });
    renderAttention();
  }

  var LABS = { regression: setupRegression, boundary: setupBoundary, clusters: setupClusters, attention: setupAttention };
  var started = {};
  function init(name) {
    if (started[name] || !LABS[name]) return;
    started[name] = true;
    LABS[name]();
  }
  window.OSPlayground = { init: init };
  var lab = document.body.getAttribute("data-lab");
  if (lab) init(lab);
})();
