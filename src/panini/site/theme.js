(function () {
  var root = document.documentElement;
  var preference = matchMedia("(prefers-color-scheme: dark)");
  function savedTheme() {
    try { return localStorage.getItem("theme"); } catch (e) { return null; }
  }
  var saved = savedTheme();
  root.dataset.theme = (saved ? saved === "dark" : preference.matches) ? "dark" : "light";
  root.dataset.dark = "glass";

  document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("theme").addEventListener("click", function () {
      var next = root.dataset.theme === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      try { localStorage.setItem("theme", next); } catch (e) {}
    });
  });
  preference.addEventListener("change", function (e) {
    if (!savedTheme()) root.dataset.theme = e.matches ? "dark" : "light";
  });
})();
