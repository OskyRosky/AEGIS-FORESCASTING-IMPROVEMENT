// TESSERACT v2 | custom.js | dashboard shell interactions (Block 7.0C)
// Pure client-side: collapsible groups, section switching, dark mode, help.
// No Shiny inputs are set -> the app stays read-only (no recompute).
(function () {
  function closest(el, sel) {
    return el && el.closest ? el.closest(sel) : null;
  }

  document.addEventListener("click", function (event) {
    var target = event.target;

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

      var content = document.querySelector(".app-content");
      if (content) content.scrollTop = 0;
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

    // 5) Dark mode toggle
    if (closest(target, "#hdr-theme-btn")) {
      var app = document.querySelector(".tess-app");
      if (app) app.classList.toggle("theme-dark");
      return;
    }
  });
})();
