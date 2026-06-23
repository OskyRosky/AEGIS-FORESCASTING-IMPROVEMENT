// TESSERACT v2 | custom.js | dashboard shell interactions (Block 7.0C)
// Pure client-side: collapsible groups, section switching, dark mode, help.
// No Shiny inputs are set -> the app stays read-only (no recompute).
(function () {
  function closest(el, sel) {
    return el && el.closest ? el.closest(sel) : null;
  }

  // Find the sidebar sub-link that owns a given section.
  function sectionSublink(section) {
    return document.querySelector('.sidebar-sublink[data-section="' + section + '"]');
  }

  // Sync the central header button (label + icon) with the active section,
  // pulling the exact label text and icon markup from the sidebar.
  function updateGuideButton(section) {
    var link = sectionSublink(section);
    if (!link) return;
    var labelEl = document.getElementById("hdr-guide-label");
    var iconEl = document.getElementById("hdr-guide-icon");
    var srcLabel = link.querySelector(".sidebar-sublink-label");
    var srcIcon = link.querySelector(".sidebar-sublink-icon");
    if (labelEl && srcLabel) labelEl.textContent = srcLabel.textContent.trim() + " Guide";
    if (iconEl && srcIcon) iconEl.innerHTML = srcIcon.innerHTML;
  }

  document.addEventListener("click", function (event) {
    var target = event.target;

    // 0) Sidebar collapse / expand (hamburger) -> mini icon rail
    if (closest(target, "#hdr-collapse-btn")) {
      var appRoot = document.querySelector(".tess-app");
      if (appRoot) appRoot.classList.toggle("sidebar-mini");
      return;
    }

    // 1) Group expand / collapse
    var groupHeader = closest(target, ".sidebar-group-header");
    if (groupHeader) {
      var group = groupHeader.parentElement;
      if (group) group.classList.toggle("expanded");
      return;
    }

    // 2) Sidebar sub-link -> switch active section
    var link = closest(target, ".sidebar-sublink");
    if (link) {
      event.preventDefault();
      document.querySelectorAll(".sidebar-sublink").forEach(function (l) {
        l.classList.remove("active");
      });
      link.classList.add("active");

      var section = link.getAttribute("data-section");
      document.querySelectorAll(".content-section").forEach(function (s) {
        s.classList.toggle("is-active", s.getAttribute("data-section") === section);
      });

      var grp = closest(link, ".sidebar-group");
      if (grp) grp.classList.add("expanded");

      updateGuideButton(section);

      var content = document.querySelector(".app-content");
      if (content) content.scrollTop = 0;

      // Reflow any chart in the newly shown section (Highcharts sizes to 0
      // while hidden; a resize event makes it fill its container).
      setTimeout(function () {
        window.dispatchEvent(new Event("resize"));
      }, 60);
      return;
    }

    // 3) Help overlay open
    if (closest(target, "#hdr-help-btn")) {
      var overlay = document.getElementById("tess-help-overlay");
      if (overlay) overlay.classList.add("open");
      return;
    }


    // 4) Help overlay close (button or backdrop)
    if (closest(target, "#tess-help-close") || target.id === "tess-help-overlay") {
      var overlay2 = document.getElementById("tess-help-overlay");
      if (overlay2) overlay2.classList.remove("open");
      return;
    }

    // 4b) Section guide open (central header button) -> show active section's guide
    if (closest(target, "#hdr-guide-btn")) {
      var activeSec = document.querySelector(".content-section.is-active");
      var secName = activeSec ? activeSec.getAttribute("data-section") : "home";
      var guideOverlay = document.getElementById("tess-guide-overlay");
      if (!guideOverlay) return;
      var titleEl = document.getElementById("tess-guide-title-text");
      var matched = false;
      guideOverlay.querySelectorAll(".guide-entry").forEach(function (entry) {
        var isMatch = entry.getAttribute("data-guide") === secName;
        entry.classList.toggle("is-shown", isMatch);
        if (isMatch) {
          matched = true;
          if (titleEl) titleEl.textContent = entry.getAttribute("data-title");
        }
      });
      // Vary the modal head icon to match the active section.
      var headIcon = document.getElementById("tess-guide-head-icon");
      var headSrc = sectionSublink(secName);
      headSrc = headSrc ? headSrc.querySelector(".sidebar-sublink-icon") : null;
      if (headIcon && headSrc) headIcon.innerHTML = headSrc.innerHTML;
      // Fallback to the dashboard guide if no section is active yet
      if (!matched) {
        var first = guideOverlay.querySelector('.guide-entry[data-guide="home"]');
        if (first) {
          first.classList.add("is-shown");
          if (titleEl) titleEl.textContent = first.getAttribute("data-title");
        }
      }
      guideOverlay.classList.add("open");
      var guideBody = guideOverlay.querySelector(".tess-guide-body");
      if (guideBody) guideBody.scrollTop = 0;
      return;
    }

    // 4c) Section guide close (button or backdrop)
    if (closest(target, "#tess-guide-close") || target.id === "tess-guide-overlay") {
      var guideOverlay2 = document.getElementById("tess-guide-overlay");
      if (guideOverlay2) guideOverlay2.classList.remove("open");
      return;
    }

    // 5) Dark mode toggle
    if (closest(target, "#hdr-theme-btn")) {
      var app = document.querySelector(".tess-app");
      if (app) app.classList.toggle("theme-dark");
      return;
    }
  });

  // Initialize the central guide button from the section active on load.
  function initGuideButton() {
    var active = document.querySelector(".content-section.is-active");
    updateGuideButton(active ? active.getAttribute("data-section") : "home");
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initGuideButton);
  } else {
    initGuideButton();
  }
})();
