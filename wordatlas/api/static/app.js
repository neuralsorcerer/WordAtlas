const cy = cytoscape({
  container: document.getElementById("cy"),
  layout: { name: "cose", animate: true },
  style: [
    {
      selector: "node",
      style: {
        label: "data(label)",
        "background-color": (el) => {
          const pos = el.data("pos");
          if (pos === "v") return "#86efac";
          if (pos === "a" || pos === "s") return "#fde68a";
          if (pos === "r") return "#d8b4fe";
          return "#93c5fd";
        },
        "border-width": 1,
        "border-color": "#1f2937",
        "font-size": 12,
        color: "#111827",
        "text-wrap": "wrap",
        "text-max-width": 160,
        "text-halign": "center",
        "text-valign": "center",
        "text-background-color": "rgba(255,255,255,0.95)",
        "text-background-opacity": 1,
        "text-background-padding": 3,
        "text-background-shape": "roundrectangle",
        "text-border-width": 1,
        "text-border-color": "#e5e7eb",
        "text-border-opacity": 1,
        "text-margin-y": 0,
        "min-zoomed-font-size": 6,
      },
    },
    {
      selector: 'node[center = "true"]',
      style: { "border-width": 3, "border-color": "#111827" },
    },
    {
      selector: "edge",
      style: {
        "line-color": "#94a3b8",
        width: 1,
        "curve-style": "bezier",
      },
    },
    {
      selector: 'edge[relation = "antonym"]',
      style: { "line-color": "#ef4444", width: 2 },
    },
    {
      selector: 'edge[relation = "hypernym"]',
      style: { "line-style": "solid" },
    },
    {
      selector: 'edge[relation = "hyponym"]',
      style: { "line-style": "dashed" },
    },
    {
      selector: 'edge[relation = "similar_to"]',
      style: { "line-style": "dotted", "line-color": "#60a5fa" },
    },
  ],
});

const status = document.getElementById("status");
const loading = document.getElementById("loading");
const buildBtn = document.getElementById("buildBtn");
const wordInput = document.getElementById("word");
const depthInput = document.getElementById("depth");

function setStatus(t) {
  status.textContent = t;
}
function setLoading(b) {
  loading.classList.toggle("show", !!b);
  buildBtn.disabled = !!b || !canSubmit();
  buildBtn.classList.toggle("button--ready", !buildBtn.disabled);
}

function canSubmit() {
  const w = (wordInput.value || "").trim();
  const d = parseInt(depthInput.value || "", 10);
  const dOk = Number.isFinite(d) && d >= 0 && d <= 5;
  return w.length > 0 && dOk;
}
function updateBuildButton() {
  const ready = canSubmit();
  buildBtn.disabled = !ready;
  buildBtn.classList.toggle("button--ready", ready);
}

function applyRelationVisibility() {
  const enabled = new Set(
    Array.from(document.querySelectorAll(".relToggle:checked")).map((c) =>
      c.getAttribute("data-rel")
    )
  );
  cy.$("edge").style("display", "none");
  enabled.forEach((rel) => {
    cy.$(`edge[relation = "${rel}"]`).style("display", "element");
  });
}

document.addEventListener("change", (e) => {
  if (e.target && e.target.classList.contains("relToggle")) {
    applyRelationVisibility();
  }
  if (e.target === depthInput) updateBuildButton();
});

const labelWidth = document.getElementById("labelWidth");
labelWidth.addEventListener("input", () => {
  const w = parseInt(labelWidth.value, 10);
  cy.style().selector("node").style("text-max-width", w).update();
});

const fontSize = document.getElementById("fontSize");
fontSize.addEventListener("input", () => {
  const s = parseInt(fontSize.value, 10);
  cy.style().selector("node").style("font-size", s).update();
});

const layoutSel = document.getElementById("layout");
function applyLayout() {
  const name = layoutSel.value;
  cy.layout({ name, animate: true }).run();
}
layoutSel.addEventListener("change", applyLayout);

function getEnabledRelations() {
  return Array.from(document.querySelectorAll(".relToggle:checked")).map((c) =>
    c.getAttribute("data-rel")
  );
}
function buildQuery(word, depth) {
  const rels = getEnabledRelations();
  const params = new URLSearchParams({ word, depth: String(depth) });
  for (const r of rels) params.append("relation", r);
  return `/api/graph?${params.toString()}`;
}
async function loadGraph(word, depth) {
  setLoading(true);
  setStatus(`Loading “${word}” (depth=${depth})…`);
  try {
    const url = buildQuery(word, depth);
    const r = await fetch(url);
    if (!r.ok) throw new Error(await r.text());
    const g = await r.json();
    const nodes = g.nodes.map((n) => ({
      data: {
        id: n.id,
        label: n.label,
        pos: n.pos,
        center: n.id === g.center,
      },
    }));
    const edges = g.edges.map((e) => ({
      data: {
        id: e.source + "->" + e.target + ":" + e.relation,
        source: e.source,
        target: e.target,
        relation: e.relation,
      },
    }));
    cy.elements().remove();
    cy.add(nodes);
    cy.add(edges);
    cy.center(cy.$('node[center = "true"]'));
    cy.layout({ name: layoutSel.value || "cose", animate: true }).run();
    setStatus(`Nodes: ${nodes.length}  Edges: ${edges.length}`);
    afterGraphLoad();
  } catch (err) {
    alert("Failed: " + (err && err.message ? err.message : err));
    setStatus("Error.");
  } finally {
    setLoading(false);
  }
}

function afterGraphLoad() {
  applyRelationVisibility();
  const w = parseInt(labelWidth.value, 10);
  cy.style().selector("node").style("text-max-width", w).update();
  const s = parseInt(fontSize.value, 10);
  cy.style().selector("node").style("font-size", s).update();
}

document.getElementById("searchForm").addEventListener("submit", (ev) => {
  ev.preventDefault();
  if (!canSubmit()) return;
  const w = wordInput.value.trim();
  const d = parseInt(depthInput.value || "1", 10);
  if (w) loadGraph(w, d);
});

wordInput.addEventListener("input", updateBuildButton);

document.getElementById("examples").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  const w = chip.getAttribute("data-word");
  wordInput.value = w;
  depthInput.value = 1;
  updateBuildButton();
  loadGraph(w, 1);
});

cy.on("tap", "node", (evt) => {
  const id = evt.target.id();
  wordInput.value = id;
  updateBuildButton();
  loadGraph(id, parseInt(depthInput.value || "1", 10));
});

updateBuildButton();
loadGraph("happiness", 1);
