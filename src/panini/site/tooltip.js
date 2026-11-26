/* Place the tooltip next to its trigger, inside the viewport. */
function tipPosition(rect, size, view) {
  var left = Math.max(8, Math.min(rect.left, view.width - size.width - 8));
  var top = rect.bottom + 6;
  if (top + size.height > view.height - 8) top = rect.top - size.height - 6;
  return { left: left, top: top };
}

function installTooltips() {
  var tip = document.createElement("div");
  tip.className = "tip";
  tip.id = "tip";
  tip.setAttribute("role", "tooltip");
  tip.hidden = true;
  document.body.appendChild(tip);
  var trigger = null;

  function hide() {
    if (!trigger) return;
    trigger.removeAttribute("aria-describedby");
    trigger = null;
    tip.classList.remove("on");
    tip.hidden = true;
  }
  function show(target) {
    if (target === trigger) return;
    hide();
    trigger = target;
    tip.textContent = target.getAttribute("data-tip");
    tip.hidden = false;
    var pos = tipPosition(target.getBoundingClientRect(), tip.getBoundingClientRect(),
                          { width: window.innerWidth, height: window.innerHeight });
    tip.style.left = pos.left + "px";
    tip.style.top = pos.top + "px";
    tip.classList.add("on");
    target.setAttribute("aria-describedby", tip.id);
  }
  ["mouseover", "focusin"].forEach(function (ev) {
    document.addEventListener(ev, function (e) {
      var target = e.target.closest && e.target.closest("[data-tip]");
      if (target) show(target);
    });
  });
  ["mouseout", "focusout"].forEach(function (ev) {
    document.addEventListener(ev, function (e) {
      if (trigger && trigger.contains(e.target) && !trigger.contains(e.relatedTarget)) hide();
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") hide();
  });
  window.addEventListener("scroll", hide, { passive: true });
  window.addEventListener("resize", hide);
  return hide;
}

if (typeof module !== "undefined") module.exports = { tipPosition: tipPosition };
if (typeof document !== "undefined") var hideTooltip = installTooltips();
