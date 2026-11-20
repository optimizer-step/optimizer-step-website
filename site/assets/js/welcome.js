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
    badge.textContent = info.duplicate
      ? "Seat already reserved"
      : info.pending
      ? "Seat request received"
      : waitlist ? "Waitlist place #" + info.seat : "Founding seat #" + info.seat;
  }
  if (lead) {
    var trackText = info.track && info.track !== "undecided" ? " for " + trackName : "";
    lead.textContent = info.pending
      ? "We've received your details. Your confirmation email with your seat number will arrive shortly."
      : info.duplicate
        ? "This email already has a seat. We didn't create a second one: your seat number is in your original confirmation email from admin@optimizerstep.com."
        : waitlist
          ? "All founding seats were taken, so you're on the waitlist" + trackText + ". We'll email you as soon as more seats open."
          : "Your free founding seat" + trackText + " is reserved. We've emailed your confirmation. It comes from admin@optimizerstep.com.";
  }

  // First lesson: switch to the first video of the track the student picked.
  var lessonBox = $("[data-first-lesson]");
  if (lessonBox && info.track && info.track !== "undecided") {
    try {
      var lesson = JSON.parse(lessonBox.getAttribute("data-first-lesson"))[info.track];
      var facade = lessonBox.querySelector("[data-youtube]");
      if (lesson && facade) {
        var label = "Watch: " + lesson.title + (lesson.hindi ? " (in Hindi)" : "");
        facade.setAttribute("data-youtube", lesson.id);
        facade.setAttribute("data-title", label);
        facade.href = "https://www.youtube.com/watch?v=" + encodeURIComponent(lesson.id);
        var thumb = facade.querySelector("img");
        if (thumb) thumb.src = "https://i.ytimg.com/vi/" + encodeURIComponent(lesson.id) + "/hqdefault.jpg";
        var caption = facade.querySelector(".video-label");
        if (caption) caption.textContent = label;
        var text = lessonBox.querySelector("[data-lesson-text]");
        if (text) text.textContent = "Start with this free lesson for " + trackName + " while your track gets ready.";
      }
    } catch (err) { /* keep the default lesson */ }
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
  if (x) {
    var via = x.getAttribute("data-via");
    x.href = "https://twitter.com/intent/tweet?text=" + encodeURIComponent(shareText) + "&url=" + encodeURIComponent(shareUrl) + (via ? "&via=" + encodeURIComponent(via) : "");
  }
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
