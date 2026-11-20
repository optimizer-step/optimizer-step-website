/* Optimizer Step — /welcome/ (thank-you page): personalise the page and record the sign-up conversion once. */
(function () {
  "use strict";
  var OS = window.OS;
  if (!OS) return;
  function $(s) { return document.querySelector(s); }

  var info = OS.store.get("sessionStorage", OS.keys.signup);
  var personal = $("[data-welcome-personal]");
  var generic = $("[data-welcome-generic]");

  if (!info) {
    if (personal) personal.hidden = true;
    if (generic) generic.hidden = false;
    return;
  }

  var name = info.first || "there";
  var trackName = OS.trackNames[info.track] || "Not sure yet";
  var waitlist = info.status === "waitlist";
  var heading = $("[data-welcome-heading]");
  var lead = $("[data-welcome-lead]");
  var badge = $("[data-welcome-badge]");

  if (heading) {
    heading.textContent = info.duplicate
      ? "You're already in, " + name + "!"
      : waitlist ? "You're on the waitlist, " + name + "." : "You're in, " + name + "!";
  }
  if (badge) {
    badge.textContent = info.pending
      ? "Seat request received"
      : waitlist ? "Waitlist place #" + info.seat : "Founding seat #" + info.seat;
  }
  if (lead) {
    var trackText = info.track && info.track !== "undecided" ? " for " + trackName : "";
    lead.textContent = info.pending
      ? "We've received your details. Your confirmation email with your seat number will arrive shortly."
      : info.duplicate
        ? "This email already has a seat" + trackText + ". We didn't create a second one, and your original confirmation email still applies."
        : waitlist
          ? "All founding seats were taken, so you're on the waitlist" + trackText + ". We'll email you as soon as more seats open."
          : "Your free founding seat" + trackText + " is reserved. We've emailed your confirmation. It comes from admin@optimizerstep.com.";
  }

  if (!info.tracked && !info.duplicate) {
    OS.trackConversion(info);
    info.tracked = true;
    OS.store.set("sessionStorage", OS.keys.signup, info);
  }

  // Share buttons
  var shareUrl = "https://www.optimizerstep.com/?utm_source=referral&utm_medium=share&utm_campaign=founding100";
  var shareText = "I just claimed a free founding seat for Optimizer Step's hands-on AI and machine learning courses. The first 100 students join free:";
  var wa = $("[data-share='whatsapp']");
  var x = $("[data-share='x']");
  var li = $("[data-share='linkedin']");
  var copy = $("[data-share='copy']");
  var native = $("[data-share='native']");
  if (wa) wa.href = "https://wa.me/?text=" + encodeURIComponent(shareText + " " + shareUrl);
  if (x) x.href = "https://twitter.com/intent/tweet?text=" + encodeURIComponent(shareText) + "&url=" + encodeURIComponent(shareUrl);
  if (li) li.href = "https://www.linkedin.com/sharing/share-offsite/?url=" + encodeURIComponent(shareUrl);
  [wa, x, li].forEach(function (a) {
    if (a) a.addEventListener("click", function () { OS.track("share", { method: a.getAttribute("data-share") }); });
  });
  if (copy) {
    copy.addEventListener("click", function () {
      var done = function () { copy.textContent = "Link copied"; setTimeout(function () { copy.textContent = "Copy link"; }, 2200); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(shareUrl).then(done, function () { window.prompt("Copy this link:", shareUrl); });
      else window.prompt("Copy this link:", shareUrl);
      OS.track("share", { method: "copy" });
    });
  }
  if (native && navigator.share) {
    native.hidden = false;
    native.addEventListener("click", function () {
      navigator.share({ title: "Optimizer Step: free founding seats", text: shareText, url: shareUrl }).catch(function () {});
      OS.track("share", { method: "native" });
    });
  }
})();
