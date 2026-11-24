/* Prakriyā explorer: renders the embedded derivation data. Derives nothing itself. */

/* Plain labels on the page; Pāṇini's terms appear as tooltips. */
var LAKARAS = [["laṭ", "Present imperfective", "laṭ"], ["laṅ", "Past imperfective", "laṅ (past, not of today)"]];
var VOICES = [["P", "Active", "parasmaipada"], ["Ā", "Middle", "ātmanepada"]];
var PERSONS = [["3", "prathama puruṣa"], ["2", "madhyama puruṣa"], ["1", "uttama puruṣa"]];
var NUMBERS = [["sg", "ekavacana"], ["du", "dvivacana"], ["pl", "bahuvacana"]];
var PADA_CLASS = { P: ["active", "parasmaipada"], A: ["middle", "ātmanepada"], U: ["active and middle", "ubhayapada"] };

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

/* Split text into [segment, sūtraId|null] pairs, marking every known sūtra number. */
function splitCitations(text, sutras) {
  var out = [], re = /\b\d+\.\d+\.\d+\b/g, last = 0, m, plain = "";
  text = String(text);
  while ((m = re.exec(text))) {
    if (!Object.prototype.hasOwnProperty.call(sutras, m[0])) continue;
    plain = text.slice(last, m.index);
    if (plain) out.push([plain, null]);
    out.push([m[0], m[0]]);
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push([text.slice(last), null]);
  return out;
}

/* Tooltip for a sūtra: number and text, then the gloss on the next line. */
function sutraTitle(id, sutras) {
  var s = sutras[id];
  return s ? id + " " + s.text + "\n" + s.gloss : id;
}

/* Where to put a tooltip: just below the word, kept 8px inside the viewport; above it if
   there's no room below. rect: the word's box; size: the tooltip's; view: the viewport's. */
function tipPosition(rect, size, view) {
  var left = Math.max(8, Math.min(rect.left, view.width - size.width - 8));
  var top = rect.bottom + 6;
  if (top + size.height > view.height - 8) top = rect.top - size.height - 6;
  return { left: left, top: top };
}

if (typeof module !== "undefined") module.exports = { parseHash: parseHash, keyOf: keyOf, splitCitations: splitCitations, sutraTitle: sutraTitle, tipPosition: tipPosition };

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
        if (marker) span.appendChild(el("span", { class: "it", "data-tip": "marker (it): deleted by 1.3.9", text: c.charAt(0).toUpperCase() + c.slice(1) }));
        else span.appendChild(document.createTextNode(c));
      });
    });
    return span;
  }

  /* A plain word with a dotted underline whose tooltip gives Pāṇini's term. */
  function term(text, tip) { return el("span", { class: "term", "data-tip": tip, tabindex: "0", text: text }); }

  /* Text with every sūtra number given a tooltip showing the rule. */
  function cite(text) {
    var span = el("span", {});
    splitCitations(text, data.sutras || {}).forEach(function (part) {
      span.appendChild(part[1] ? term(part[0], sutraTitle(part[1], data.sutras)) : document.createTextNode(part[0]));
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
    var pc = PADA_CLASS[r.pada];
    var info = document.getElementById("root-info");
    info.innerHTML = "";
    [term("Recited as", "upadeśa: the root as taught in the Dhātupāṭha, with its markers"), " " + r.upadesha_iast,
     " · “" + r.meaning + "” · ", term(r.class_label, r.gana + " (the bhū class, first gaṇa of the Dhātupāṭha)"),
     " · ", term(pc[0], pc[1]), r.pada === "U" ? "" : " only"].forEach(function (c) {
      info.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
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
      var m = (probe.message || "").match(/\((\d+\.\d+\.\d+)\)$/);
      var pc = PADA_CLASS[rootByKey(state.root).pada];
      return el("div", { class: "unavailable" }, [state.root + " is ", term(pc[0], pc[1]), " only",
        m ? el("span", {}, [" (", term(m[1], sutraTitle(m[1], data.sutras || {})), ")"]) : null]);
    }
    var head = el("tr", {}, [el("th", { scope: "col" }, [""])].concat(NUMBERS.map(function (n) {
      return el("th", { scope: "col" }, [term(n[0], n[1])]);
    })));
    var rows = PERSONS.map(function (p) {
      return el("tr", {}, [el("th", { scope: "row" }, [term(p[0], p[1])])]
        .concat(NUMBERS.map(function (n) { return cell(keyOf(state.root, lakara, pada, p[0], n[0])); })));
    });
    return el("table", {}, [el("thead", {}, [head]), el("tbody", {}, rows)]);
  }

  function renderParadigm() {
    paradigm.innerHTML = "";
    paradigm.appendChild(el("div", { class: "axis corner" }));
    VOICES.forEach(function (v) {
      paradigm.appendChild(el("div", { class: "axis col" }, [term(v[1], v[2])]));
    });
    LAKARAS.forEach(function (l) {
      paradigm.appendChild(el("div", { class: "axis row" }, [term(l[1], l[2])]));
      VOICES.forEach(function (v) {
        paradigm.appendChild(el("div", {}, [el("p", { class: "voice-label" }, [term(v[1], v[2])]), table(l[0], v[0])]));
      });
    });
  }

  function step(s) {
    var rule = el("div", { class: "rule" });
    s.sutras.forEach(function (su) {
      rule.appendChild(el("div", {}, [el("span", { class: "sid", "data-tip": sutraTitle(su.id, data.sutras || {}), tabindex: "0", text: su.id }),
                                      el("span", { class: "stext", text: su.text })]));
    });
    if (s.kind === "category" || s.kind === "prohibition") {
      rule.appendChild(el("p", { class: "kind", text: s.kind === "category"
        ? "Form unchanged: this rule assigns a category that later rules use."
        : "Form unchanged: this rule prevents another rule from applying." }));
    }
    if (s.note) rule.appendChild(el("p", { class: "snote" }, [cite(s.note)]));
    s.sutras.forEach(function (su) { if (su.gloss) rule.appendChild(el("p", { class: "gloss" }, [cite(su.gloss)])); });
    var li = el("li", {}, [renderTerms(s.after), rule]);
    s.near_misses.forEach(function (n) { li.appendChild(el("p", { class: "near" }, ["↳ ", cite(n)])); });
    s.warnings.forEach(function (w) { li.appendChild(el("p", { class: "warn" }, [cite(w)])); });
    if (s.losers.length) {
      li.appendChild(el("details", {}, [
        el("summary", { text: "competitors" }),
        el("ul", {}, s.losers.map(function (l) {
          return el("li", {}, [el("span", { class: "sid", "data-tip": sutraTitle(l.rule_id, data.sutras || {}), tabindex: "0", text: l.rule_id }), cite(l.reason)]);
        })),
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
    var k = state.key.split("|");   // root, lakāra, pada, person, number
    var lak = LAKARAS.filter(function (l) { return l[0] === k[1]; })[0];
    var voice = VOICES.filter(function (v) { return v[0] === k[2]; })[0];
    var person = PERSONS.filter(function (p) { return p[0] === k[3]; })[0];
    var number = NUMBERS.filter(function (n) { return n[0] === k[4]; })[0];
    panel.appendChild(el("p", { class: "desc" }, [
      d.request.root + " · ", term(k[3] + k[4], person[1] + " " + number[1]), " ",
      term(lak[1].toLowerCase(), lak[2]), " ", term(voice[1].toLowerCase(), voice[2])]));
    if (d.alternatives && d.alternatives.length) panel.appendChild(el("p", { class: "also", text: "Also correct: " + d.alternatives.join(", ") }));
    if (d.status !== "ok") {
      panel.appendChild(el("p", { class: "message banner-warn" }, [cite(d.message || d.status)]));
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

  /* One shared tooltip, shown at once on hover or keyboard focus (native title tooltips
     carry a browser delay the page cannot change). */
  var tip = el("div", { class: "tip", role: "tooltip", id: "tip" });
  document.body.appendChild(tip);
  function showTip(target) {
    tip.textContent = target.getAttribute("data-tip");
    tip.classList.add("on");
    var pos = tipPosition(target.getBoundingClientRect(), tip.getBoundingClientRect(),
                          { width: window.innerWidth, height: window.innerHeight });
    tip.style.left = pos.left + "px";
    tip.style.top = pos.top + "px";
    target.setAttribute("aria-describedby", "tip");
  }
  function hideTip(target) { tip.classList.remove("on"); if (target) target.removeAttribute("aria-describedby"); }
  ["mouseover", "focusin"].forEach(function (ev) {
    document.addEventListener(ev, function (e) {
      var t = e.target.closest && e.target.closest("[data-tip]");
      if (t) showTip(t);
    });
  });
  ["mouseout", "focusout"].forEach(function (ev) {
    document.addEventListener(ev, function (e) {
      var t = e.target.closest && e.target.closest("[data-tip]");
      if (t && !(e.relatedTarget && t.contains(e.relatedTarget))) hideTip(t);
    });
  });
  window.addEventListener("scroll", function () { hideTip(null); }, { passive: true });

  render();
})();
