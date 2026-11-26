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

/* Search key: no combining marks (dot-below, macron, tilde, ...), no "~", no trailing "-", lowercase. */
function fold(s) {
  return String(s == null ? "" : s).normalize("NFD").replace(/\p{M}/gu, "").replace(/~/g, "").replace(/-+$/, "").toLowerCase();
}

/* Roots matching `query`, best first: exact name, name prefix, code prefix, then substring of name,
   upadeśa or meaning. Within a group featured roots come first, then list order. */
function searchRoots(query, roots, featured, limit) {
  var q = fold(String(query == null ? "" : query).trim());
  var feat = {};
  (featured || []).forEach(function (c) { feat[c] = true; });
  var hits = [];
  roots.forEach(function (r, i) {
    var name = fold(r.name), group = 4;
    if (!q) group = 0;
    else if (name === q) group = 0;
    else if (name.indexOf(q) === 0) group = 1;
    else if (r.key.indexOf(q) === 0) group = 2;
    else if (name.indexOf(q) >= 0 || fold(r.upadesha_iast).indexOf(q) >= 0 || fold(r.meaning).indexOf(q) >= 0) group = 3;
    else return;
    hits.push({ r: r, group: group, feat: feat[r.key] ? 0 : 1, i: i });
  });
  hits.sort(function (x, y) { return x.group - y.group || x.feat - y.feat || x.i - y.i; });
  return hits.slice(0, limit || 50).map(function (h) { return h.r; });
}

/* Parse "#<code>/laṭ/P/3/sg" (or just "#<code>"); old links may name the root instead, which
   counts if the name is unique or one of the matches is featured. Anything invalid falls back to
   the first root and no selection. On a server page whose root isn't loaded yet, a well-formed
   key is kept (the caller checks it once the forms arrive). Pure: no DOM access. */
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
  if (!data.roots.some(function (r) { return r.key === root; })) {
    var named = data.roots.filter(function (r) { return r.name && r.name.normalize("NFC") === root; });
    var feat = named.filter(function (r) { return (data.featured || []).indexOf(r.key) >= 0; });
    if (named.length === 1) root = named[0].key;
    else if (feat.length) root = feat[0].key;
    else return fallback;
  }
  if (parts.length < 5) return { root: root, key: null };
  var key = keyOf(root, parts[1], parts[2], parts[3], parts[4]);
  var prefix = root + "|";
  var loaded = Object.keys(data.derivations).some(function (k) { return k.indexOf(prefix) === 0; });
  if (!loaded && data.source === "server") {
    var ok = LAKARAS.some(function (l) { return l[0] === parts[1]; }) && VOICES.some(function (v) { return v[0] === parts[2]; })
      && PERSONS.some(function (p) { return p[0] === parts[3]; }) && NUMBERS.some(function (n) { return n[0] === parts[4]; });
    return { root: root, key: ok ? key : null };
  }
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

/* Split "{modern|traditional}" markup into [text, traditional|null] pairs. */
function splitTerms(text) {
  var out = [], re = /\{([^{}|]+)\|([^{}]+)\}/g, last = 0, m;
  text = String(text);
  while ((m = re.exec(text))) {
    if (m.index > last) out.push([text.slice(last, m.index), null]);
    out.push([m[1], m[2]]);
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push([text.slice(last), null]);
  return out;
}

/* Split text so that glossary words (whole words only) become [word, explanation] pairs. */
function splitGlossary(text, glossary) {
  var words = Object.keys(glossary || {});
  text = String(text);
  if (!words.length) return [[text, null]];
  var re = new RegExp("(?<![\\p{L}\\p{M}])(" + words.join("|") + ")(?![\\p{L}\\p{M}])", "gu");
  var out = [], last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push([text.slice(last, m.index), null]);
    out.push([m[1], glossary[m[1]]]);
    last = m.index + m[1].length;
  }
  if (last < text.length) out.push([text.slice(last), null]);
  return out;
}

/* Tooltip for a marker: what it does, if known, else the generic one. */
function markerTip(upadesha, ch, notes) {
  var note = notes && (notes[upadesha + "|" + ch] || notes["*|" + ch]);
  return note ? "marker (it) · " + note : "marker (it): deleted by 1.3.9";
}

/* Tooltip for a sūtra: number and text, then the gloss on the next line. */
function sutraTitle(id, sutras) {
  var s = sutras[id];
  return s ? id + " " + s.text + "\n" + splitTerms(s.gloss).map(function (p) { return p[0]; }).join("") : id;
}

/* Where to put a tooltip: just below the word, kept 8px inside the viewport; above it if
   there's no room below. rect: the word's box; size: the tooltip's; view: the viewport's. */
function tipPosition(rect, size, view) {
  var left = Math.max(8, Math.min(rect.left, view.width - size.width - 8));
  var top = rect.bottom + 6;
  if (top + size.height > view.height - 8) top = rect.top - size.height - 6;
  return { left: left, top: top };
}

if (typeof module !== "undefined") module.exports = { parseHash: parseHash, fold: fold, searchRoots: searchRoots, keyOf: keyOf, splitCitations: splitCitations, splitTerms: splitTerms, splitGlossary: splitGlossary, sutraTitle: sutraTitle, markerTip: markerTip, tipPosition: tipPosition };

if (typeof document !== "undefined") (function () {
  var data = JSON.parse(document.getElementById("data").textContent);
  var rootInput = document.getElementById("root");
  var rootList = document.getElementById("root-list");
  var paradigm = document.getElementById("paradigm");
  var panel = document.getElementById("derivation");
  var state = { root: null, key: null };

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
        if (marker) span.appendChild(el("span", { class: "it", "data-tip": markerTip(v.upadesha, c, data.markers), text: c.charAt(0).toUpperCase() + c.slice(1) }));
        else span.appendChild(document.createTextNode(c));
      });
    });
    return span;
  }

  /* A plain word with a dotted underline whose tooltip gives Pāṇini's term. */
  function term(text, tip) { return el("span", { class: "term", "data-tip": tip, tabindex: "0", text: text }); }

  /* Text with {modern|traditional} terms and sūtra numbers given tooltips. */
  function cite(text) {
    var span = el("span", {});
    splitTerms(text).forEach(function (seg) {
      if (seg[1]) { span.appendChild(term(seg[0], seg[1])); return; }
      splitCitations(seg[0], data.sutras || {}).forEach(function (part) {
        if (part[1]) { span.appendChild(term(part[0], sutraTitle(part[1], data.sutras))); return; }
        splitGlossary(part[0], data.glossary).forEach(function (g) {
          span.appendChild(g[1] ? term(g[0], g[1]) : document.createTextNode(g[0]));
        });
      });
    });
    return span;
  }

  function rootByKey(k) { return data.roots.filter(function (r) { return r.key === k; })[0]; }

  function writeHash() {
    var h = state.key ? state.key.split("|").join("/") : state.root;
    history.replaceState(null, "", "#" + encodeURIComponent(h).replace(/%2F/g, "/"));
  }

  /* The root search box: a combobox over data.roots. */
  var matches = [], active = -1;
  function openList(on) {
    rootList.hidden = !on;
    rootInput.setAttribute("aria-expanded", on ? "true" : "false");
    if (!on) { active = -1; rootInput.removeAttribute("aria-activedescendant"); }
  }
  function pickRoot(key) {
    openList(false);
    hideTip(null);
    rootInput.blur();
    state = { root: key, key: null };
    writeHash();
    ensureForms(key);
    render();
  }
  function setActive(i) {
    active = i;
    Array.prototype.forEach.call(rootList.children, function (li, j) {
      li.setAttribute("aria-selected", j === i ? "true" : "false");
      if (j === i) { rootInput.setAttribute("aria-activedescendant", li.id); li.scrollIntoView({ block: "nearest" }); }
    });
  }
  function showMatches(query) {
    matches = searchRoots(query, data.roots, data.featured, 50);
    rootList.innerHTML = "";
    matches.forEach(function (r, i) {
      var attrs = { role: "option", id: "root-opt-" + i, "aria-selected": "false" };
      if (r.unavailable) { attrs["aria-disabled"] = "true"; attrs["data-tip"] = r.unavailable; attrs.class = "out"; }
      var gloss = el("span", { class: "gloss" }, [r.meaning_kind === "traditional" ? el("em", { text: r.meaning }) : r.meaning]);
      var li = el("li", attrs, [el("span", { class: "rname", text: r.name }), el("span", { class: "rup", text: r.upadesha_iast }), gloss,
                                el("span", { class: "rvoice", text: PADA_CLASS[r.pada][0] })]);
      li.addEventListener("mousedown", function (e) { e.preventDefault(); });
      li.addEventListener("click", function () { pickRoot(r.key); });
      rootList.appendChild(li);
    });
    if (!matches.length) rootList.appendChild(el("li", { class: "none", role: "presentation", text: "No root matches." }));
    openList(true);
    if (matches.length && query) setActive(0);
  }
  rootInput.addEventListener("focus", function () { rootInput.select(); showMatches(""); });
  rootInput.addEventListener("input", function () { showMatches(rootInput.value); });
  rootInput.addEventListener("blur", function () { openList(false); rootInput.value = rootByKey(state.root).name; });
  rootInput.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (rootList.hidden) showMatches(rootInput.value === rootByKey(state.root).name ? "" : rootInput.value);
      if (matches.length) setActive((active + (e.key === "ArrowDown" ? 1 : matches.length - 1)) % matches.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      var pick = matches[active < 0 ? 0 : active];
      if (!rootList.hidden && pick) pickRoot(pick.key);
    } else if (e.key === "Escape") {
      openList(false); rootInput.value = rootByKey(state.root).name; rootInput.select();
    }
  });

  function renderPicker() {
    var r = rootByKey(state.root);
    if (document.activeElement !== rootInput) rootInput.value = r.name;
    var pc = PADA_CLASS[r.pada];
    var info = document.getElementById("root-info");
    info.innerHTML = "";
    var gloss = r.meaning_kind === "traditional"
      ? el("em", { class: "term", "data-tip": "traditional gloss from the root list", tabindex: "0", text: r.meaning })
      : document.createTextNode(r.meaning);
    [el("strong", { class: "rname", text: r.name }), " · ",
     term("Recited as", "upadeśa: the root as taught in the Dhātupāṭha, with its markers"), " " + r.upadesha_iast,
     " · “", gloss, "” · ", term(r.class_label, r.gana + " (the bhū class, first gaṇa of the Dhātupāṭha)"),
     " · ", term(pc[0], pc[1]), r.pada === "U" ? "" : " only"].forEach(function (c) {
      info.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
  }

  /* Forms of the selected root: already here (static page, or fetched before), else fetched from the server. */
  var loading = null, loadError = null;
  function hasForms(code) { return Object.prototype.hasOwnProperty.call(data.derivations, keyOf(code, "laṭ", "P", "3", "sg")); }
  function ensureForms(code) {
    loadError = null;
    if (hasForms(code) || data.source !== "server") { loading = null; return; }
    loading = code;
    fetch("/api/root/" + encodeURIComponent(code))
      .then(function (res) { if (!res.ok) throw new Error("HTTP " + res.status); return res.json(); })
      .then(function (body) {
        Object.keys(body.derivations).forEach(function (k) { data.derivations[k] = body.derivations[k]; });
        if (loading === code) { loading = null; if (state.key && !data.derivations[state.key]) state.key = null; render(); }
      })
      .catch(function (e) {
        if (loading === code) { loading = null; loadError = "Couldn’t load " + rootByKey(code).name + " (" + e.message + ")."; render(); }
      });
  }
  function retry() { ensureForms(state.root); render(); }

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
      return el("div", { class: "unavailable" }, [rootByKey(state.root).name + " is ", term(pc[0], pc[1]), " only",
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

  /* A historical aside: the listed words (Latin, Greek) in italics; asterisks stay as written. */
  function historyLine(s) {
    var parts = [s.history], italic = s.history_italic || [];
    italic.forEach(function (w) {
      parts = parts.reduce(function (acc, p) {
        if (typeof p !== "string") return acc.concat([p]);
        var bits = p.split(w);
        bits.forEach(function (b, i) { if (i) acc.push(el("em", { text: w })); if (b) acc.push(b); });
        return acc;
      }, []);
    });
    return el("p", { class: "history" }, [el("span", { class: "hlabel", text: "Historically" }), " "].concat(parts));
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
    if (s.history) rule.appendChild(historyLine(s));
    s.sutras.forEach(function (su) { if (su.gloss) rule.appendChild(el("p", { class: "gloss" }, [cite(su.gloss)])); });
    if (s.reads && s.reads.length) {
      var reads = el("p", { class: "reads" }, ["Read via "]);
      s.reads.forEach(function (r, i) {
        if (i) reads.appendChild(document.createTextNode(" · "));
        reads.appendChild(term(r.id, sutraTitle(r.id, data.sutras || {})));
        reads.appendChild(document.createTextNode(": "));
        reads.appendChild(cite(r.note));
      });
      rule.appendChild(reads);
    }
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

  function render() {
    renderPicker();
    if (!hasForms(state.root) && data.source === "server") {
      paradigm.innerHTML = "";
      panel.innerHTML = "";
      if (loadError) {
        var btn = el("button", { class: "retry", type: "button", text: "Retry" });
        btn.addEventListener("click", retry);
        paradigm.appendChild(el("p", { class: "note loadmsg", role: "alert" }, [loadError + " ", btn]));
      } else {
        paradigm.appendChild(el("p", { class: "note loadmsg", text: "deriving…" }));
      }
      return;
    }
    renderParadigm();
    renderDerivation();
  }

  function applyHash() { state = parseHash(location.hash, data); ensureForms(state.root); render(); }
  window.addEventListener("hashchange", applyHash);
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

  applyHash();
})();
