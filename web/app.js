// Sheldon site. Replays recorded CLI output from fixtures/ and draws the seed graph.
// Nothing here writes to a database or invents output: every line comes from a fixture.

(() => {
  "use strict";

  const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)");
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  /* ---------------- Nav, copy, install tabs ---------------- */

  const nav = $("#nav");
  const onScroll = () => nav.classList.toggle("is-scrolled", window.scrollY > 8);
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.cssText = "position:fixed;opacity:0";
      document.body.appendChild(ta);
      ta.select();
      let ok = false;
      try { ok = document.execCommand("copy"); } catch { ok = false; }
      ta.remove();
      return ok;
    }
  }
  document.addEventListener("click", async (ev) => {
    const btn = ev.target.closest(".copy");
    if (!btn) return;
    if (await copyText(btn.dataset.copy)) {
      btn.classList.add("is-copied");
      clearTimeout(btn._t);
      btn._t = setTimeout(() => btn.classList.remove("is-copied"), 1600);
    }
  });

  const toggle = $("[data-theme-toggle]");
  const syncToggle = () => {
    const dark = document.documentElement.dataset.theme === "dark";
    toggle.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
  };
  toggle.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("theme", next); } catch { /* private mode */ }
    syncToggle();
  });
  syncToggle();
  // Until someone picks a theme, keep following the OS if it changes.
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (ev) => {
    let saved = null;
    try { saved = localStorage.getItem("theme"); } catch { /* private mode */ }
    if (saved) return;
    document.documentElement.dataset.theme = ev.matches ? "dark" : "light";
    syncToggle();
  });

  /* ---------------- Data ---------------- */

  const load = (name) => fetch(`fixtures/${name}`, { cache: "no-cache" }).then((r) => {
    if (!r.ok) throw new Error(`${name}: ${r.status}`);
    return r.json();
  });

  Promise.all([load("graph.json"), load("graph-after.json"), load("evidence-gate-run.json"), load("refute.json")])
    .then(([before, after, gate, refute]) => {
      const graph = initGraph(before, after);
      initTerminals(before.moments, gate, refute, graph);
    })
    .catch((err) => {
      console.error(err);
      $$("[data-body]").forEach((body) => {
        body.innerHTML = `<div class="tl t-dim">Could not load the recordings (${esc(err.message)}). Serve this folder over HTTP, for example <span class="t-id">python -m http.server -d web</span>, or read web/fixtures directly.</div>`;
      });
    });

  /* ---------------- Terminals ---------------- */

  const shellArg = (a) => (/^[\w@%+=:,./-]+$/.test(a) ? a : `"${a.replace(/(["\\$`])/g, "\\$1")}"`);
  const shellLine = (exe, argv) => [exe, ...argv.map(shellArg)].join(" ");
  const lines = (s) => (s || "").replace(/\n$/, "").split("\n").filter((l, i, all) => l !== "" || i < all.length - 1);

  function shellFrame(exe, rec) {
    const out = [
      ...lines(rec.stdout).map((text) => ({ text, stream: "stdout" })),
      ...lines(rec.stderr).map((text) => ({ text, stream: "stderr" })),
    ];
    return { kind: "cmd", ps: "$", cmd: shellLine(exe, rec.argv), out, exit: rec.exit_code };
  }

  function buildFrames(moments, gate, refute) {
    return {
      retry: [shellFrame("python", moments.retry_block)],
      gate: [
        shellFrame("python", gate.frames[0]),
        shellFrame("sheldon", gate.frames[1]),
        shellFrame("python", gate.frames[2]),
      ],
      cascade: [
        { kind: "py", ps: ">>>", cmd: refute.call, out: [{ text: refute.returned ? "True" : "False", stream: "stdout" }], exit: null },
        shellFrame("python", refute.check),
      ],
    };
  }

  // Color the status token at the start of a recorded line; never reword it.
  function paint(text, known) {
    let h = esc(text);
    h = h
      .replace(/^(sheldon:) (blocked \(failure\))/, '<span class="t-dim">$1</span> <span class="t-block">$2</span>')
      .replace(/^(sheldon:) (clear \(success\))/, '<span class="t-dim">$1</span> <span class="t-pass">$2</span>')
      .replace(/^(blocked:)/, '<span class="t-block">$1</span>')
      .replace(/^(stale:)/, '<span class="t-stale">$1</span>')
      .replace(/^(refuted:)/, '<span class="t-refuted">$1</span>')
      .replace(/^(recorded evidence) (E-[0-9a-f]+)( exit 0)$/, '$1 <span class="t-pass">$2</span>$3')
      .replace(/^True$/, '<span class="t-pass">True</span>');
    // Ids that exist in the snapshot become links to the graph. Skip inside tags.
    return h.replace(/(<[^>]+>)|\b(INC-\d+|ACT-\d+|E-\d+|C-\d+|A-\d+|T-\d+)\b/g, (m, tag, id) =>
      tag ? tag : known.has(id) ? `<span class="t-id" data-node="${id}" tabindex="0" role="link">${id}</span>` : id,
    );
  }

  function renderTerm(term, frames, known) {
    const body = $("[data-body]", term);
    body.innerHTML = "";
    const steps = [];
    for (const f of frames) {
      const cmd = document.createElement("div");
      cmd.className = `tl tl--${f.kind}`;
      cmd.innerHTML = `<span class="tl__ps">${esc(f.ps)}</span><span class="tl__typed"></span><span class="tl__ghost">${esc(f.cmd)}</span>`;
      body.appendChild(cmd);
      steps.push({ type: "type", el: cmd, text: f.cmd });
      for (const o of f.out) {
        const line = document.createElement("div");
        line.className = `tl${o.stream === "stderr" ? " tl--stderr" : ""}`;
        line.innerHTML = (o.stream === "stderr" ? '<span class="tl__stream">stderr</span>' : "") + paint(o.text, known);
        body.appendChild(line);
        steps.push({ type: "line", el: line });
      }
      if (f.exit !== null && f.exit !== undefined) {
        const ex = document.createElement("div");
        ex.className = "tl tl--exit";
        ex.textContent = `# exit ${f.exit}`;
        body.appendChild(ex);
        steps.push({ type: "line", el: ex, exit: f.exit });
      }
    }
    return steps;
  }

  function setExit(term, code) {
    const badge = $("[data-exit]", term);
    term.classList.remove("is-running", "is-exit-0", "is-exit-bad");
    if (code === null) { badge.hidden = true; return; }
    badge.hidden = false;
    badge.textContent = `exit ${code}`;
    badge.className = `term__exit ${code === 0 ? "is-0" : "is-bad"}`;
    term.classList.add(code === 0 ? "is-exit-0" : "is-exit-bad");
  }

  function showAll(term, steps) {
    for (const s of steps) {
      s.el.classList.remove("is-pending", "is-shown");
      if (s.type === "type") {
        $(".tl__typed", s.el).textContent = s.text;
        $(".tl__ghost", s.el).textContent = "";
      }
    }
    const last = [...steps].reverse().find((s) => "exit" in s);
    setExit(term, last ? last.exit : null);
  }

  async function play(term, steps, token) {
    const alive = () => term._token === token;
    for (const s of steps) {
      s.el.classList.add("is-pending");
      s.el.classList.remove("is-shown");
      if (s.type === "type") { $(".tl__typed", s.el).textContent = ""; $(".tl__ghost", s.el).textContent = s.text; }
    }
    setExit(term, null);
    term.classList.add("is-running");
    const caret = document.createElement("span");
    caret.className = "tl__caret";
    caret.setAttribute("aria-hidden", "true");
    let lastExit = null;
    for (const s of steps) {
      if (!alive()) return;
      s.el.classList.remove("is-pending");
      if (s.type === "type") {
        const typed = $(".tl__typed", s.el);
        const ghost = $(".tl__ghost", s.el);
        typed.after(caret);
        await wait(260);
        const total = Math.min(1500, Math.max(500, s.text.length * 13));
        const t0 = performance.now();
        await new Promise((done) => {
          const tick = (now) => {
            if (!alive()) return done();
            const n = Math.round(Math.min(1, (now - t0) / total) * s.text.length);
            typed.textContent = s.text.slice(0, n);
            ghost.textContent = s.text.slice(n);
            if (n < s.text.length) requestAnimationFrame(tick); else done();
          };
          requestAnimationFrame(tick);
        });
        await wait(420);
        caret.remove();
      } else {
        s.el.classList.add("is-shown");
        if ("exit" in s) lastExit = s.exit;
        await wait("exit" in s ? 160 : 110);
      }
    }
    if (alive()) setExit(term, lastExit);
  }

  function initTerminals(moments, gate, refute, graph) {
    const frames = buildFrames(moments, gate, refute);
    const known = graph.known;
    $$("[data-term]").forEach((term) => {
      const steps = renderTerm(term, frames[term.dataset.term], known);
      term._steps = steps;
      if (REDUCED.matches) showAll(term, steps);
      else steps.forEach((s) => s.el.classList.add("is-pending"));
      $("[data-replay]", term).addEventListener("click", () => {
        const token = Symbol("run");
        term._token = token;
        if (REDUCED.matches) showAll(term, steps); else play(term, steps, token);
      });
    });

    if (!REDUCED.matches && "IntersectionObserver" in window) {
      const io = new IntersectionObserver((entries) => {
        for (const e of entries) {
          if (!e.isIntersecting) continue;
          io.unobserve(e.target);
          const token = Symbol("run");
          e.target._token = token;
          play(e.target, e.target._steps, token);
        }
      }, { threshold: 0.45 });
      $$("[data-term]").forEach((t) => io.observe(t));
    } else if (!REDUCED.matches) {
      $$("[data-term]").forEach((t) => showAll(t, t._steps));
    }

    // Clicking an id in a recording or a path opens it in the graph, in the state that moment shows.
    const jump = (el) => {
      const id = el.dataset.node;
      if (!id) return;
      const inCascade = !!el.closest("#cascade");
      graph.setState(inCascade ? "after" : "before");
      graph.select(id);
      $("#graph").scrollIntoView({ behavior: REDUCED.matches ? "auto" : "smooth", block: "start" });
    };
    document.addEventListener("click", (ev) => {
      const el = ev.target.closest(".t-id[data-node], a.ref[data-node]");
      if (!el) return;
      ev.preventDefault();
      jump(el);
    });
    document.addEventListener("keydown", (ev) => {
      if (ev.key !== "Enter") return;
      const el = ev.target.closest && ev.target.closest(".t-id[data-node]");
      if (el) jump(el);
    });
  }

  /* ---------------- Graph ---------------- */

  // Hand-placed so edges do not cross nodes. Code layer left, claims center, dependents right.
  const POS = {
    "INC-12": [520, 62],
    "checkout/session.py": [140, 205],
    "C-5": [385, 205],
    "C-7": [700, 205],
    "T-9": [965, 120],
    "ACT-1": [470, 360],
    "E-41": [295, 360],
    "E-30": [625, 360],
    "E-60": [800, 360],
    "A-3": [965, 300],
    "E-31": [965, 470],
    "checkout/cache.py": [140, 530],
    "PR-7": [560, 530],
    "E-52": [800, 555],
  };
  const LABEL_AT = { "ATTEMPTED_FIX_FOR|ACT-1|C-5": 0.28, "REFUTED_BY|C-5|E-41": 0.36 };
  const SKIP_EDGES = new Set(["BELONGS_TO", "MODIFIED", "AUTHORED"]);
  const NS = "http://www.w3.org/2000/svg";
  const svgEl = (tag, attrs = {}) => {
    const el = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
    return el;
  };

  function describe(node) {
    const p = node.properties;
    const label = node.labels[0];
    const out = { title: node.key, meta: label.toLowerCase(), cls: [], dot: null, pill: null, sub: "" };
    switch (label) {
      case "Incident":
        out.meta = `incident · ${p.severity}`;
        out.sub = p.title;
        break;
      case "Claim":
        out.meta = `${p.kind} · ${p.status}`;
        out.pill = p.status;
        out.sub = p.text;
        if (p.status === "refuted") out.cls.push("n--refuted");
        break;
      case "Evidence":
        if (p.executed) {
          out.meta = `${p.kind} · exit ${p.exit_code}`;
          out.dot = p.exit_code === 0 ? "pass" : "fail";
          out.pill = p.exit_code === 0 ? "pass" : "fail";
        } else {
          out.meta = `${p.kind} · not executed`;
          out.cls.push("n--unexecuted");
          out.dot = "none";
          out.pill = "unexecuted";
        }
        out.sub = `${p.kind} on sha ${p.sha}${p.executed ? `, exit ${p.exit_code}` : ", never executed"}`;
        break;
      case "Approval":
        out.meta = `approval · ${p.status}`;
        out.pill = p.status;
        out.sub = `by ${p.by} on sha ${p.sha}`;
        if (p.status === "stale") out.cls.push("n--stale");
        break;
      case "Task":
        out.meta = `task · ${p.status}${p.stale ? " · stale" : ""}`;
        out.pill = p.stale ? "stale" : p.status;
        out.sub = p.title;
        if (p.stale) out.cls.push("n--stale");
        break;
      case "Action":
        out.meta = "action · fingerprint";
        out.sub = p.cmd;
        break;
      case "PR":
        out.title = `PR ${p.number}`;
        out.meta = `pr · head ${p.head_sha}`;
        break;
      case "File":
        out.meta = "file";
        break;
    }
    return out;
  }
  const pillLabel = (p) => ({ pass: "exit 0", fail: "exit 1", unexecuted: "not executed" })[p] || p;

  function initGraph(before, after) {
    const section = $("#graph");
    const svg = $("[data-svg]", section);
    const gEdges = $("[data-edges]", svg);
    const gNodes = $("[data-nodes]", svg);
    const inspector = $("[data-inspector]", section);
    const recordsEl = $("[data-records]", section);

    const states = {
      before: new Map(before.nodes.map((n) => [n.key, n])),
      after: new Map(after.nodes.map((n) => [n.key, n])),
    };
    const known = new Set([...states.before.keys()]);
    const edgeId = (e) => `${e.type}|${e.from}|${e.to}`;
    const beforeEdges = new Set(before.edges.map(edgeId));
    const edges = new Map();
    for (const e of [...before.edges, ...after.edges]) {
      if (SKIP_EDGES.has(e.type) || !POS[e.from] || !POS[e.to]) continue;
      edges.set(edgeId(e), { ...e, onlyAfter: !beforeEdges.has(edgeId(e)) });
    }

    let state = "before";
    let selected = "C-7";
    let picked = false; // Fade the rest of the graph only after someone picks a node.

    // Sizes come from the longer of the two lines. Geist Mono widths, measured at 13px and 10px.
    const size = (d) => {
      const w = Math.max(d.title.length * 7.85, d.meta.length * 6.05) + (d.dot ? 40 : 28);
      return [Math.round(Math.max(w, 92)), 50];
    };
    const boxes = {};

    // Nodes
    for (const key of Object.keys(POS)) {
      const node = states.before.get(key);
      if (!node) continue;
      const d0 = describe(node);
      const d1 = describe(states.after.get(key) || node);
      const [w0] = size(d0);
      const [w1, h] = size(d1);
      const w = Math.max(w0, w1);
      const [cx, cy] = POS[key];
      boxes[key] = { cx, cy, w, h };
      const g = svgEl("g", { class: "n", "data-key": key, transform: `translate(${cx - w / 2} ${cy - h / 2})`, tabindex: "0", role: "button", "aria-label": `${d0.title}, ${d0.meta}` });
      g.appendChild(svgEl("rect", { class: "n__box", width: w, height: h, rx: 10 }));
      const x = 14;
      const id = svgEl("text", { class: "n__id", x, y: 22 });
      id.textContent = d0.title;
      const meta = svgEl("text", { class: "n__meta", x, y: 38 });
      g.append(id, meta);
      if (d0.dot) g.appendChild(svgEl("circle", { class: "n__dot", cx: w - 16, cy: 17, r: 4 }));
      g.addEventListener("click", () => select(key));
      g.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); select(key); } });
      gNodes.appendChild(g);
    }

    // Edges, clipped to the node boxes.
    const clip = (b, dx, dy) => {
      const tx = dx ? (b.w / 2 + 4) / Math.abs(dx) : Infinity;
      const ty = dy ? (b.h / 2 + 4) / Math.abs(dy) : Infinity;
      const t = Math.min(tx, ty);
      return [b.cx + dx * t, b.cy + dy * t];
    };
    const markerFor = (t) => (t === "REFUTED_BY" ? "arrow-refuted" : t === "SUPPORTED_BY" ? "arrow-support" : t === "RELIES_ON" || t === "DEPENDS_ON" ? "arrow-dep" : "arrow");
    for (const e of edges.values()) {
      const a = boxes[e.from], b = boxes[e.to];
      if (!a || !b) continue;
      const dx = b.cx - a.cx, dy = b.cy - a.cy;
      const len = Math.hypot(dx, dy);
      const [x1, y1] = clip(a, dx / len, dy / len);
      const [x2, y2] = clip(b, -dx / len, -dy / len);
      const g = svgEl("g", { class: `e${e.onlyAfter ? " only-after" : ""}`, "data-from": e.from, "data-to": e.to });
      const path = svgEl("path", { class: `edge edge--${e.type}`, d: `M${x1.toFixed(1)} ${y1.toFixed(1)} L${x2.toFixed(1)} ${y2.toFixed(1)}`, "marker-end": `url(#${markerFor(e.type)})` });
      g.appendChild(path);
      // Two edges meet C-5 at the same height, so their labels sit at different points along the line.
      const t = LABEL_AT[edgeId(e)] ?? 0.5;
      const lx = x1 + (x2 - x1) * t, ly = y1 + (y2 - y1) * t;
      const vertical = Math.abs(dx) < 30;
      const left = a.cx < 550;
      const label = svgEl("text", { class: `edge-label edge-label--${e.type}`, x: vertical ? lx + (left ? -8 : 8) : lx, y: ly + 3, "text-anchor": vertical ? (left ? "end" : "start") : "middle" });
      label.textContent = e.type;
      g.appendChild(label);
      gEdges.appendChild(g);
      g.style.setProperty("--len", Math.ceil(Math.hypot(x2 - x1, y2 - y1)));
    }

    function nodeFor(key) { return states[state].get(key) || states.before.get(key); }

    function paintNodes(animate) {
      section.dataset.state = state;
      for (const g of $$(".n", gNodes)) {
        const key = g.dataset.key;
        const d = describe(nodeFor(key));
        g.setAttribute("class", ["n", ...d.cls, key === selected ? "is-selected" : ""].filter(Boolean).join(" "));
        $(".n__meta", g).textContent = d.meta;
        g.setAttribute("aria-label", `${d.title}, ${d.meta}`);
        const dot = $(".n__dot", g);
        if (dot) dot.setAttribute("class", `n__dot dot--${d.dot}`);
        if (animate && state === "after" && changedKeys().has(key)) {
          const order = { "C-7": 0, "A-3": 520, "T-9": 640 };
          g.style.setProperty("--delay", `${order[key] ?? 0}ms`);
          g.classList.add("n--changed");
        }
      }
      // Restart the edge draw each time the after state is shown.
      if (animate) for (const e of $$(".e.only-after", gEdges)) { const p = $("path", e); p.style.animation = "none"; void p.getBBox(); p.style.animation = ""; }
      focusNeighbors();
    }

    function changedKeys() {
      const out = new Set();
      for (const [k, n] of states.after) {
        const b = states.before.get(k);
        if (b && JSON.stringify(b.properties) !== JSON.stringify(n.properties)) out.add(k);
      }
      return out;
    }

    function focusNeighbors() {
      const near = new Set([selected]);
      for (const g of $$(".e", gEdges)) {
        const visible = !g.classList.contains("only-after") || state === "after";
        if (visible && (g.dataset.from === selected || g.dataset.to === selected)) { near.add(g.dataset.from); near.add(g.dataset.to); }
      }
      const hasNode = picked && !!$(`.n[data-key="${CSS.escape(selected)}"]`, gNodes);
      for (const g of $$(".n", gNodes)) g.classList.toggle("is-dim", hasNode && !near.has(g.dataset.key));
      for (const g of $$(".e", gEdges)) g.classList.toggle("is-dim", hasNode && !(g.dataset.from === selected || g.dataset.to === selected));
    }

    const fmt = (k, v) => {
      if (Array.isArray(v)) return v.join(", ");
      if ((k === "at" || k === "refuted_at" || k === "timestamp") && typeof v === "number") {
        return `${v} <span class="t-dim">(${new Date(v).toISOString().replace("T", " ").slice(0, 16)} UTC)</span>`;
      }
      return esc(JSON.stringify(v));
    };

    function renderInspector() {
      const node = nodeFor(selected);
      if (!node) return;
      const d = describe(node);
      const prev = states.before.get(selected);
      const props = Object.entries(node.properties);
      const rows = props.map(([k, v]) => {
        const was = state === "after" && prev && JSON.stringify(prev.properties[k]) !== JSON.stringify(v);
        const old = was ? (k in prev.properties ? `<span class="was">${fmt(k, prev.properties[k])}</span>` : `<span class="was">unset</span>`) : "";
        return `<div class="${was ? "is-changed" : ""}"><dt>${esc(k)}</dt><dd>${old}${fmt(k, v)}</dd></div>`;
      }).join("");
      const rels = [...edges.values()].filter((e) => (state === "after" || !e.onlyAfter) && (e.from === selected || e.to === selected))
        .map((e) => `${e.from} -[${e.type}]-> ${e.to}`);
      inspector.innerHTML = `
        <div class="insp__head">
          <span class="insp__label">${esc(node.labels.join(" · "))}</span>
          <span class="insp__key">${esc(d.title)}</span>
          ${d.sub ? `<p class="insp__text">${esc(d.sub)}</p>` : ""}
          ${rels.length ? `<p class="insp__text" style="font:400 12px/1.6 var(--mono);color:var(--dim)">${rels.map(esc).join("<br>")}</p>` : ""}
        </div>
        <dl class="insp__props">${rows}</dl>`;
    }

    const GROUPS = [
      ["Claims", "Claim"],
      ["Evidence", "Evidence"],
      ["Approvals", "Approval"],
      ["Tasks", "Task"],
    ];
    function renderRecords() {
      const all = [...states[state].values()];
      recordsEl.innerHTML = GROUPS.map(([title, label]) => {
        const items = all.filter((n) => n.labels.includes(label));
        return `<section class="rec"><header class="rec__head">${title}<span>${items.length}</span></header><ul>${items.map((n) => {
          const d = describe(n);
          return `<li><button type="button" data-pick="${esc(n.key)}" class="${n.key === selected ? "is-selected" : ""}">
            <span class="rec__id">${esc(d.title)}</span>${d.pill ? `<span class="pill pill--${esc(d.pill)}">${esc(pillLabel(d.pill))}</span>` : ""}
            <span class="rec__sub">${esc(d.sub)}</span></button></li>`;
        }).join("")}</ul></section>`;
      }).join("");
    }
    recordsEl.addEventListener("click", (ev) => {
      const b = ev.target.closest("[data-pick]");
      if (b) select(b.dataset.pick);
    });

    function select(key) {
      if (!nodeFor(key)) return;
      selected = key;
      picked = true;
      for (const g of $$(".n", gNodes)) g.classList.toggle("is-selected", g.dataset.key === key);
      focusNeighbors();
      renderInspector();
      for (const b of $$("[data-pick]", recordsEl)) b.classList.toggle("is-selected", b.dataset.pick === key);
    }

    // State toggle
    const seg = $(".seg", section);
    const thumb = $(".seg__thumb", seg);
    const placeThumb = () => {
      const on = $('[aria-checked="true"]', seg);
      thumb.style.width = `${on.offsetWidth}px`;
      thumb.style.transform = `translateX(${on.offsetLeft}px)`;
    };
    function setState(next) {
      if (next === state) return;
      state = next;
      $$("[data-state]", seg).forEach((b) => b.setAttribute("aria-checked", String(b.dataset.state === state)));
      placeThumb();
      paintNodes(true);
      renderInspector();
      renderRecords();
    }
    $$("[data-state]", seg).forEach((b) => b.addEventListener("click", () => setState(b.dataset.state)));
    seg.addEventListener("keydown", (ev) => {
      if (ev.key === "ArrowRight" || ev.key === "ArrowLeft") {
        setState(state === "before" ? "after" : "before");
        $('[aria-checked="true"]', seg).focus();
      }
    });
    window.addEventListener("resize", placeThumb);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(placeThumb);

    paintNodes(false);
    renderInspector();
    renderRecords();
    placeThumb();

    return { known, select, setState };
  }
})();
