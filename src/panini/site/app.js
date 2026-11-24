/* Prakriyā explorer: renders the embedded derivation data. Derives nothing itself. */

var LAKARAS = [["laṭ", "Present imperfective"], ["laṅ", "Past imperfective"]];
var VOICES = [["P", "Active", "parasmaipada"], ["Ā", "Middle", "ātmanepada"]];
var PERSONS = [["3", "prathama"], ["2", "madhyama"], ["1", "uttama"]];
var NUMBERS = ["sg", "du", "pl"];

function keyOf(root, lakara, pada, person, number) {
  return [root, lakara, pada, person, number].join("|");
}

/* Parse "#root/laṭ/P/3/sg" (or just "#root"). Anything invalid falls back to the
   first root and no selection. Pure: no DOM access. */
function parseHash(hash, data) {
  var first = data.roots.length ? data.roots[0].key : null;
  var fallback = { root: first, key: null };
  var raw = String(hash || "").replace(/^#/, "");
  if (!raw) return fallback;
  var text;
  try { text = decodeURIComponent(raw); } catch (e) { return fallback; }
  text = text.normalize("NFC");
  var parts = text.split("/");
  var root = parts[0];
  if (!data.roots.some(function (r) { return r.key === root; })) return fallback;
  if (parts.length < 5) return { root: root, key: null };
  var key = keyOf(root, parts[1], parts[2], parts[3], parts[4]);
  return { root: root, key: Object.prototype.hasOwnProperty.call(data.derivations, key) ? key : null };
}

if (typeof module !== "undefined") module.exports = { parseHash: parseHash, keyOf: keyOf };

if (typeof document !== "undefined") (function () {
  var data = JSON.parse(document.getElementById("data").textContent);
  var rootSelect = document.getElementById("root");
  var paradigm = document.getElementById("paradigm");
  var panel = document.getElementById("derivation");
  var state = parseHash(location.hash, data);

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "class") node.className = attrs[k];
      else if (k === "text") node.textContent = attrs[k];
      else node.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) {
      if (c == null) return;
      node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return node;
  }

  /* A form as displayed: markers in capitals, term boundaries as + */
  function renderTerms(views) {
    var span = el("span", { class: "after" });
    views.forEach(function (v, i) {
      if (i) span.appendChild(el("span", { class: "plus", text: "+" }));
      v.chars.forEach(function (pair) {
        var c = pair[0], marker = pair[1];
        if (marker) span.appendChild(el("span", { class: "it", title: "marker (it)", text: c.charAt(0).toUpperCase() + c.slice(1) }));
        else span.appendChild(document.createTextNode(c));
      });
    });
    return span;
  }

  function rootByKey(k) { return data.roots.filter(function (r) { return r.key === k; })[0]; }

  function writeHash() {
    var h = state.key ? state.key.split("|").join("/") : state.root;
    history.replaceState(null, "", "#" + encodeURIComponent(h).replace(/%2F/g, "/"));
  }

  function renderPicker() {
    rootSelect.innerHTML = "";
    data.roots.forEach(function (r) {
      var o = el("option", { value: r.key, text: r.key + " — " + r.meaning });
      if (r.key === state.root) o.selected = true;
      rootSelect.appendChild(o);
    });
    var r = rootByKey(state.root);
    var pada = { P: "parasmaipada (active) only", A: "ātmanepada (middle) only", U: "both voices (ubhayapada)" }[r.pada];
    document.getElementById("root-info").textContent =
      "Recited as " + r.upadesha_iast + " · “" + r.meaning + "” · " + r.gana + " · " + pada;
  }

  function cell(key) {
    var d = data.derivations[key];
    var td = el("td", {});
    var ok = d.status === "ok";
    var refs = d.reference || [];
    var bad = !ok || (refs.length && refs.indexOf(d.result) < 0);
    if (bad) td.classList.add("bad");
    if (key === state.key) td.classList.add("selected");
    var btn = el("button", { class: "form", type: "button" }, [ok ? d.result : d.status === "error" ? "error" : "?"]);
    if (d.alternatives && d.alternatives.length) btn.appendChild(el("span", { class: "alt", text: "· " + d.alternatives.join(" · ") }));
    btn.addEventListener("click", function () { state.key = key; writeHash(); render(); panel.scrollIntoView({ behavior: "smooth", block: "start" }); });
    td.appendChild(btn);
    if (bad && refs.length) td.appendChild(el("span", { class: "ref", text: "expected " + refs.join(" / ") }));
    return td;
  }

  function table(lakara, pada) {
    var probe = data.derivations[keyOf(state.root, lakara, pada, "3", "sg")];
    if (probe.status === "unavailable") {
      var msg = probe.message || "";
      var m = msg.match(/^(.*) \((\d+\.\d+\.\d+)\)$/);
      return el("div", { class: "unavailable" }, m ? [m[1] + " ", el("span", { class: "rule", text: "(" + m[2] + ")" })] : [msg]);
    }
    var head = el("tr", {}, [el("th", { scope: "col" }, [""])].concat(NUMBERS.map(function (n) { return el("th", { scope: "col", text: n }); })));
    var rows = PERSONS.map(function (p) {
      return el("tr", {}, [el("th", { scope: "row" }, [p[0], el("span", { class: "sub", text: p[1] })])]
        .concat(NUMBERS.map(function (n) { return cell(keyOf(state.root, lakara, pada, p[0], n)); })));
    });
    return el("table", {}, [el("thead", {}, [head]), el("tbody", {}, rows)]);
  }

  function renderParadigm() {
    paradigm.innerHTML = "";
    paradigm.appendChild(el("div", { class: "axis corner" }));
    VOICES.forEach(function (v) {
      paradigm.appendChild(el("div", { class: "axis col" }, [v[1], el("span", { class: "sub", text: v[2] })]));
    });
    LAKARAS.forEach(function (l) {
      paradigm.appendChild(el("div", { class: "axis row" }, [l[1], el("span", { class: "sub", text: l[0] })]));
      VOICES.forEach(function (v) {
        paradigm.appendChild(el("div", {}, [el("p", { class: "voice-label", text: v[1] + " · " + v[2] }), table(l[0], v[0])]));
      });
    });
  }

  function step(s) {
    var rule = el("div", { class: "rule" });
    s.sutras.forEach(function (su) {
      rule.appendChild(el("div", {}, [el("span", { class: "sid", text: su.id }), el("span", { class: "stext", text: su.text })]));
    });
    if (s.note) rule.appendChild(el("p", { class: "snote", text: s.note }));
    s.sutras.forEach(function (su) { if (su.gloss) rule.appendChild(el("p", { class: "gloss", text: su.gloss })); });
    var li = el("li", {}, [renderTerms(s.after), rule]);
    s.near_misses.forEach(function (n) { li.appendChild(el("p", { class: "near", text: "↳ " + n })); });
    s.warnings.forEach(function (w) { li.appendChild(el("p", { class: "warn", text: w })); });
    if (s.losers.length) {
      li.appendChild(el("details", {}, [
        el("summary", { text: "competitors" }),
        el("ul", {}, s.losers.map(function (l) { return el("li", {}, [el("span", { class: "sid", text: l.rule_id }), l.reason]); })),
      ]));
    }
    return li;
  }

  function renderDerivation() {
    panel.innerHTML = "";
    if (!state.key) {
      panel.appendChild(el("p", { class: "note empty", text: "Pick a form above to see how Pāṇini’s rules derive it." }));
      return;
    }
    var d = data.derivations[state.key];
    panel.appendChild(el("h2", { text: d.result || "—" }));
    panel.appendChild(el("p", { class: "desc" }, [el("span", { class: "pan", text: d.request.root + " · " + d.request.panini }), el("br"), d.request.pie]));
    if (d.alternatives && d.alternatives.length) panel.appendChild(el("p", { class: "also", text: "Also correct: " + d.alternatives.join(", ") }));
    if (d.status !== "ok") {
      panel.appendChild(el("p", { class: "message banner-warn", text: d.message || d.status }));
      return;
    }
    panel.appendChild(el("ol", { class: "steps" }, d.steps.map(step)));
  }

  function render() { renderPicker(); renderParadigm(); renderDerivation(); }

  rootSelect.addEventListener("change", function () { state = { root: rootSelect.value, key: null }; writeHash(); render(); });
  window.addEventListener("hashchange", function () { state = parseHash(location.hash, data); render(); });
  document.getElementById("theme").addEventListener("click", function () {
    var next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("theme", next); } catch (e) {}
  });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function (e) {
    var saved; try { saved = localStorage.getItem("theme"); } catch (err) {}
    if (!saved) document.documentElement.dataset.theme = e.matches ? "dark" : "light";
  });

  render();
})();
