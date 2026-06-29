// TESSERACT v2 | custom.js | governed sidebar navigation
document.addEventListener("click", function(event) {
  const link = event.target.closest(".sidebar-link");
  if (!link) return;

  event.preventDefault();
  document.querySelectorAll(".sidebar-link").forEach(function(item) {
    item.classList.remove("active");
  });
  link.classList.add("active");

  if (window.Shiny) {
    Shiny.setInputValue("stage07_section", link.dataset.section, { priority: "event" });
  }
});
