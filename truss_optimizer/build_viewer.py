"""
Generate a self-contained HTML truss viewer with all test trusses embedded.

Run: python -m truss_optimizer.build_viewer
Output: truss_optimizer/viewer.html
"""

import json
from pathlib import Path


def build_viewer():
    data_dir = Path("truss_optimizer/data/test_trusses")
    manifest_path = data_dir / "manifest.json"

    with open(manifest_path) as f:
        manifest = json.load(f)

    # Load all truss files
    trusses = {}
    for entry in manifest:
        with open(data_dir / entry["file"]) as f:
            trusses[entry["file"]] = json.load(f)

    html = generate_html(manifest, trusses)

    out_path = Path("truss_optimizer/viewer.html")
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Viewer written to {out_path}")
    print(f"Open in browser: file://{out_path.resolve()}")


def generate_html(manifest, trusses):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Truss Optimizer - Test Truss Viewer</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #e0e0e0; display: flex; height: 100vh; overflow: hidden; }}

/* Sidebar */
.sidebar {{ width: 320px; background: #16213e; border-right: 1px solid #0f3460; display: flex; flex-direction: column; flex-shrink: 0; }}
.sidebar-header {{ padding: 16px; background: #0f3460; border-bottom: 1px solid #533483; }}
.sidebar-header h1 {{ font-size: 18px; color: #e94560; margin-bottom: 8px; }}
.sidebar-header p {{ font-size: 12px; color: #888; }}

.filters {{ padding: 12px 16px; border-bottom: 1px solid #0f3460; display: flex; gap: 8px; flex-wrap: wrap; }}
.filter-btn {{ padding: 4px 10px; font-size: 11px; border: 1px solid #533483; background: transparent; color: #e0e0e0; border-radius: 12px; cursor: pointer; transition: all 0.2s; }}
.filter-btn:hover, .filter-btn.active {{ background: #533483; color: white; }}

.search-box {{ padding: 8px 16px; border-bottom: 1px solid #0f3460; }}
.search-box input {{ width: 100%; padding: 6px 10px; background: #1a1a2e; border: 1px solid #0f3460; color: #e0e0e0; border-radius: 4px; font-size: 13px; }}
.search-box input::placeholder {{ color: #666; }}

.truss-list {{ flex: 1; overflow-y: auto; }}
.truss-item {{ padding: 10px 16px; border-bottom: 1px solid #1a1a2e; cursor: pointer; transition: background 0.15s; }}
.truss-item:hover {{ background: #1a1a2e; }}
.truss-item.selected {{ background: #0f3460; border-left: 3px solid #e94560; }}
.truss-item .name {{ font-size: 13px; font-weight: 600; color: #e0e0e0; }}
.truss-item .meta {{ font-size: 11px; color: #888; margin-top: 2px; }}
.truss-item .tags {{ display: flex; gap: 4px; margin-top: 4px; }}
.tag {{ font-size: 10px; padding: 1px 6px; border-radius: 8px; }}
.tag-warren {{ background: #1b4332; color: #95d5b2; }}
.tag-pratt {{ background: #3c1642; color: #c77dff; }}
.tag-howe {{ background: #462c1a; color: #e9c46a; }}
.tag-mixed {{ background: #1a3c5e; color: #72b4d9; }}
.tag-roof {{ background: #5c1a1a; color: #e07a5f; }}
.tag-triangle {{ background: #1a4a4a; color: #76c8c8; }}
.tag-industrial {{ background: #4a3c1a; color: #d4a574; }}

/* Main content */
.main {{ flex: 1; display: flex; flex-direction: column; }}
.toolbar {{ padding: 10px 20px; background: #16213e; border-bottom: 1px solid #0f3460; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }}
.toolbar label {{ font-size: 12px; color: #888; display: flex; align-items: center; gap: 6px; }}
.toolbar input[type="checkbox"] {{ accent-color: #e94560; }}
.toolbar .nav-btns {{ display: flex; gap: 6px; margin-left: auto; }}
.toolbar button {{ padding: 4px 12px; font-size: 12px; background: #0f3460; border: 1px solid #533483; color: #e0e0e0; border-radius: 4px; cursor: pointer; }}
.toolbar button:hover {{ background: #533483; }}

.canvas-container {{ flex: 1; position: relative; overflow: hidden; background: #1a1a2e; }}
canvas {{ display: block; width: 100%; height: 100%; }}

/* Info panel */
.info-panel {{ padding: 12px 20px; background: #16213e; border-top: 1px solid #0f3460; display: flex; gap: 24px; flex-wrap: wrap; }}
.info-group {{ }}
.info-group .label {{ font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }}
.info-group .value {{ font-size: 14px; font-weight: 600; color: #e0e0e0; }}
.info-group .value.highlight {{ color: #e94560; }}

.truss-list::-webkit-scrollbar {{ width: 6px; }}
.truss-list::-webkit-scrollbar-track {{ background: #16213e; }}
.truss-list::-webkit-scrollbar-thumb {{ background: #533483; border-radius: 3px; }}
</style>
</head>
<body>

<div class="sidebar">
  <div class="sidebar-header">
    <h1>Truss Viewer</h1>
    <p>100 test trusses &middot; 7 topologies</p>
  </div>
  <div class="filters" id="filters"></div>
  <div class="search-box">
    <input type="text" id="search" placeholder="Search trusses...">
  </div>
  <div class="truss-list" id="truss-list"></div>
</div>

<div class="main">
  <div class="toolbar">
    <label><input type="checkbox" id="showNodeIds" checked> Node IDs</label>
    <label><input type="checkbox" id="showElemIds"> Element IDs</label>
    <label><input type="checkbox" id="showLoads" checked> Loads</label>
    <label><input type="checkbox" id="showAreas"> Areas</label>
    <label><input type="checkbox" id="showMaterials" checked> Materials</label>
    <div class="nav-btns">
      <button id="prevBtn">Prev</button>
      <button id="nextBtn">Next</button>
      <button id="resetZoom">Reset View</button>
    </div>
  </div>
  <div class="canvas-container">
    <canvas id="canvas"></canvas>
  </div>
  <div class="info-panel" id="info-panel"></div>
</div>

<script>
const MANIFEST = {json.dumps(manifest)};
const TRUSSES = {json.dumps(trusses)};

const TOPOLOGY_COLORS = {{
  warren: {{ bg: '#1b4332', fg: '#95d5b2', elem: '#40916c' }},
  pratt: {{ bg: '#3c1642', fg: '#c77dff', elem: '#9d4edd' }},
  howe: {{ bg: '#462c1a', fg: '#e9c46a', elem: '#d4a574' }},
  mixed_material: {{ bg: '#1a3c5e', fg: '#72b4d9', elem: '#4895ef' }},
  roof_truss: {{ bg: '#5c1a1a', fg: '#e07a5f', elem: '#e07a5f' }},
  simple_triangle: {{ bg: '#1a4a4a', fg: '#76c8c8', elem: '#52b69a' }},
  heavy_industrial: {{ bg: '#4a3c1a', fg: '#d4a574', elem: '#dda15e' }},
}};

const MATERIAL_COLORS = {{
  Steel: '#4895ef',
  Aluminum: '#f77f00',
  Timber: '#95d5b2',
}};

let currentIndex = 0;
let activeFilter = 'all';
let filteredManifest = [...MANIFEST];
let pan = {{ x: 0, y: 0 }};
let zoom = 1;
let isDragging = false;
let dragStart = {{ x: 0, y: 0 }};

// --- Sidebar ---
function buildFilters() {{
  const container = document.getElementById('filters');
  const topologies = ['all', ...new Set(MANIFEST.map(m => m.topology))];
  topologies.forEach(t => {{
    const btn = document.createElement('button');
    btn.className = 'filter-btn' + (t === 'all' ? ' active' : '');
    btn.textContent = t === 'all' ? 'All (100)' : `${{t}} (${{MANIFEST.filter(m => m.topology === t).length}})`;
    btn.onclick = () => {{
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeFilter = t;
      applyFilter();
    }};
    container.appendChild(btn);
  }});
}}

function applyFilter() {{
  const search = document.getElementById('search').value.toLowerCase();
  filteredManifest = MANIFEST.filter(m => {{
    const matchesFilter = activeFilter === 'all' || m.topology === activeFilter;
    const matchesSearch = !search || m.name.toLowerCase().includes(search) || m.topology.includes(search);
    return matchesFilter && matchesSearch;
  }});
  buildList();
  if (filteredManifest.length > 0) {{
    currentIndex = 0;
    selectTruss(0);
  }}
}}

function buildList() {{
  const container = document.getElementById('truss-list');
  container.innerHTML = '';
  filteredManifest.forEach((entry, idx) => {{
    const div = document.createElement('div');
    div.className = 'truss-item' + (idx === currentIndex ? ' selected' : '');
    const tc = TOPOLOGY_COLORS[entry.topology] || {{ bg: '#333', fg: '#aaa' }};
    div.innerHTML = `
      <div class="name">${{entry.name}}</div>
      <div class="meta">${{entry.nodes}} nodes &middot; ${{entry.elements}} elem &middot; ${{entry.weight_kg.toFixed(0)}} kg &middot; $${{entry.cost_usd.toFixed(0)}}</div>
      <div class="tags"><span class="tag tag-${{entry.topology}}">${{entry.topology}}</span></div>
    `;
    div.onclick = () => selectTruss(idx);
    container.appendChild(div);
  }});
}}

function selectTruss(idx) {{
  currentIndex = idx;
  buildList();
  drawTruss();
  updateInfoPanel();
}}

// --- Canvas drawing ---
function getCanvas() {{
  const canvas = document.getElementById('canvas');
  const container = canvas.parentElement;
  canvas.width = container.clientWidth * window.devicePixelRatio;
  canvas.height = container.clientHeight * window.devicePixelRatio;
  canvas.style.width = container.clientWidth + 'px';
  canvas.style.height = container.clientHeight + 'px';
  return canvas;
}}

function drawTruss() {{
  const canvas = getCanvas();
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (filteredManifest.length === 0) {{
    ctx.fillStyle = '#666';
    ctx.font = `${{16 * dpr}}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText('No trusses match filter', canvas.width / 2, canvas.height / 2);
    return;
  }}

  const entry = filteredManifest[currentIndex];
  const truss = TRUSSES[entry.file];
  if (!truss) return;

  const nodes = truss.nodes;
  const elements = truss.elements;
  const loads = truss.loads;
  const tc = TOPOLOGY_COLORS[entry.topology] || {{ elem: '#888' }};

  // Compute bounds
  const xs = nodes.map(n => n.x);
  const ys = nodes.map(n => n.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const spanX = maxX - minX || 1;
  const spanY = maxY - minY || 1;

  const pad = 80 * dpr;
  const scaleX = (canvas.width - 2 * pad) / spanX;
  const scaleY = (canvas.height - 2 * pad) / spanY;
  const scale = Math.min(scaleX, scaleY) * zoom;

  const cx = canvas.width / 2 + pan.x * dpr;
  const cy = canvas.height / 2 + pan.y * dpr;
  const ox = cx - ((minX + maxX) / 2) * scale;
  const oy = cy + ((minY + maxY) / 2) * scale;

  function tx(x) {{ return ox + x * scale; }}
  function ty(y) {{ return oy - y * scale; }}

  const showNodeIds = document.getElementById('showNodeIds').checked;
  const showElemIds = document.getElementById('showElemIds').checked;
  const showLoads = document.getElementById('showLoads').checked;
  const showAreas = document.getElementById('showAreas').checked;
  const showMaterials = document.getElementById('showMaterials').checked;

  const nodeMap = {{}};
  nodes.forEach(n => {{ nodeMap[n.id] = n; }});

  // Grid
  ctx.strokeStyle = '#ffffff08';
  ctx.lineWidth = 1;
  const gridStep = Math.pow(10, Math.floor(Math.log10(spanX)));
  for (let gx = Math.floor(minX / gridStep) * gridStep; gx <= maxX + gridStep; gx += gridStep) {{
    ctx.beginPath(); ctx.moveTo(tx(gx), 0); ctx.lineTo(tx(gx), canvas.height); ctx.stroke();
  }}
  for (let gy = Math.floor(minY / gridStep) * gridStep; gy <= maxY + gridStep; gy += gridStep) {{
    ctx.beginPath(); ctx.moveTo(0, ty(gy)); ctx.lineTo(canvas.width, ty(gy)); ctx.stroke();
  }}

  // Elements
  elements.forEach(elem => {{
    const ni = nodeMap[elem.node_i];
    const nj = nodeMap[elem.node_j];
    if (!ni || !nj) return;

    const color = showMaterials ? (MATERIAL_COLORS[elem.material.name] || tc.elem) : tc.elem;
    const areaScale = showAreas ? Math.max(1, Math.sqrt(elem.area * 1e4) * 0.8) : 2;

    ctx.strokeStyle = color;
    ctx.lineWidth = areaScale * dpr;
    ctx.beginPath();
    ctx.moveTo(tx(ni.x), ty(ni.y));
    ctx.lineTo(tx(nj.x), ty(nj.y));
    ctx.stroke();

    if (showElemIds) {{
      const mx = (tx(ni.x) + tx(nj.x)) / 2;
      const my = (ty(ni.y) + ty(nj.y)) / 2;
      ctx.fillStyle = '#ffffff88';
      ctx.font = `${{10 * dpr}}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(elem.id, mx, my - 8 * dpr);
    }}

    if (showAreas) {{
      const mx = (tx(ni.x) + tx(nj.x)) / 2;
      const my = (ty(ni.y) + ty(nj.y)) / 2;
      ctx.fillStyle = '#ffffff55';
      ctx.font = `${{9 * dpr}}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.fillText((elem.area * 1e4).toFixed(1) + ' cm\u00B2', mx, my + 10 * dpr);
    }}
  }});

  // Loads
  if (showLoads) {{
    loads.forEach(load => {{
      const node = nodeMap[load.node_id];
      if (!node) return;
      const mag = Math.sqrt(load.fx * load.fx + load.fy * load.fy);
      if (mag === 0) return;
      const arrowLen = Math.min(40 * dpr, Math.max(20 * dpr, mag / 5000 * dpr));

      ctx.strokeStyle = '#ef476f';
      ctx.fillStyle = '#ef476f';
      ctx.lineWidth = 2 * dpr;

      const nx = tx(node.x);
      const ny = ty(node.y);

      if (Math.abs(load.fy) > 0) {{
        const dir = load.fy > 0 ? -1 : 1;
        ctx.beginPath();
        ctx.moveTo(nx, ny - dir * 4 * dpr);
        ctx.lineTo(nx, ny - dir * arrowLen);
        ctx.stroke();
        // Arrowhead
        ctx.beginPath();
        ctx.moveTo(nx, ny - dir * 4 * dpr);
        ctx.lineTo(nx - 4 * dpr, ny - dir * (4 + 8) * dpr);
        ctx.lineTo(nx + 4 * dpr, ny - dir * (4 + 8) * dpr);
        ctx.closePath();
        ctx.fill();
      }}
      if (Math.abs(load.fx) > 0) {{
        const dir = load.fx > 0 ? 1 : -1;
        ctx.beginPath();
        ctx.moveTo(nx + dir * 4 * dpr, ny);
        ctx.lineTo(nx + dir * arrowLen, ny);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(nx + dir * 4 * dpr, ny);
        ctx.lineTo(nx + dir * (4 + 8) * dpr, ny - 4 * dpr);
        ctx.lineTo(nx + dir * (4 + 8) * dpr, ny + 4 * dpr);
        ctx.closePath();
        ctx.fill();
      }}
    }});
  }}

  // Nodes
  nodes.forEach(node => {{
    const nx = tx(node.x);
    const ny = ty(node.y);
    const r = 5 * dpr;

    if (node.support === 'pin') {{
      // Triangle
      ctx.fillStyle = '#e94560';
      ctx.beginPath();
      ctx.moveTo(nx, ny);
      ctx.lineTo(nx - 8 * dpr, ny + 12 * dpr);
      ctx.lineTo(nx + 8 * dpr, ny + 12 * dpr);
      ctx.closePath();
      ctx.fill();
      // Ground line
      ctx.strokeStyle = '#e94560';
      ctx.lineWidth = 2 * dpr;
      ctx.beginPath();
      ctx.moveTo(nx - 10 * dpr, ny + 14 * dpr);
      ctx.lineTo(nx + 10 * dpr, ny + 14 * dpr);
      ctx.stroke();
    }} else if (node.support === 'roller_x') {{
      // Triangle
      ctx.fillStyle = '#06d6a0';
      ctx.beginPath();
      ctx.moveTo(nx, ny);
      ctx.lineTo(nx - 8 * dpr, ny + 12 * dpr);
      ctx.lineTo(nx + 8 * dpr, ny + 12 * dpr);
      ctx.closePath();
      ctx.fill();
      // Circles (rollers)
      ctx.beginPath();
      ctx.arc(nx - 4 * dpr, ny + 16 * dpr, 3 * dpr, 0, Math.PI * 2);
      ctx.arc(nx + 4 * dpr, ny + 16 * dpr, 3 * dpr, 0, Math.PI * 2);
      ctx.fill();
    }} else if (node.support === 'roller_y') {{
      ctx.fillStyle = '#06d6a0';
      ctx.beginPath();
      ctx.moveTo(nx, ny);
      ctx.lineTo(nx - 12 * dpr, ny - 8 * dpr);
      ctx.lineTo(nx - 12 * dpr, ny + 8 * dpr);
      ctx.closePath();
      ctx.fill();
    }}

    // Node dot
    ctx.fillStyle = node.support === 'free' ? '#ffffff' : '#ffdd00';
    ctx.beginPath();
    ctx.arc(nx, ny, r, 0, Math.PI * 2);
    ctx.fill();

    if (showNodeIds) {{
      ctx.fillStyle = '#ffffffcc';
      ctx.font = `bold ${{11 * dpr}}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(node.id, nx, ny - 8 * dpr);
    }}
  }});

  // Title
  ctx.fillStyle = '#e0e0e0';
  ctx.font = `bold ${{16 * dpr}}px sans-serif`;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'top';
  ctx.fillText(entry.name, 16 * dpr, 16 * dpr);

  ctx.fillStyle = '#888';
  ctx.font = `${{12 * dpr}}px sans-serif`;
  ctx.fillText(`#${{entry.id}} / ${{entry.topology}}`, 16 * dpr, 36 * dpr);

  // Material legend
  if (showMaterials) {{
    const mats = new Set(elements.map(e => e.material.name));
    let ly = 60 * dpr;
    mats.forEach(mat => {{
      ctx.fillStyle = MATERIAL_COLORS[mat] || '#888';
      ctx.fillRect(16 * dpr, ly, 12 * dpr, 12 * dpr);
      ctx.fillStyle = '#ccc';
      ctx.font = `${{11 * dpr}}px sans-serif`;
      ctx.textBaseline = 'middle';
      ctx.fillText(mat, 34 * dpr, ly + 6 * dpr);
      ly += 18 * dpr;
    }});
  }}

  // Scale bar
  const barWorld = gridStep;
  const barPx = barWorld * scale;
  const bx = canvas.width - 20 * dpr - barPx;
  const by = canvas.height - 20 * dpr;
  ctx.strokeStyle = '#666';
  ctx.lineWidth = 2 * dpr;
  ctx.beginPath();
  ctx.moveTo(bx, by); ctx.lineTo(bx + barPx, by);
  ctx.moveTo(bx, by - 4 * dpr); ctx.lineTo(bx, by + 4 * dpr);
  ctx.moveTo(bx + barPx, by - 4 * dpr); ctx.lineTo(bx + barPx, by + 4 * dpr);
  ctx.stroke();
  ctx.fillStyle = '#888';
  ctx.font = `${{11 * dpr}}px sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText(barWorld + ' m', bx + barPx / 2, by - 6 * dpr);
}}

function updateInfoPanel() {{
  const panel = document.getElementById('info-panel');
  if (filteredManifest.length === 0) {{
    panel.innerHTML = '<div class="info-group"><div class="value">No truss selected</div></div>';
    return;
  }}
  const entry = filteredManifest[currentIndex];
  const truss = TRUSSES[entry.file];
  const mats = [...new Set(truss.elements.map(e => e.material.name))].join(', ');
  const totalLoad = truss.loads.reduce((s, l) => s + Math.sqrt(l.fx*l.fx + l.fy*l.fy), 0);
  const xs = truss.nodes.map(n => n.x);
  const ys = truss.nodes.map(n => n.y);
  const span = (Math.max(...xs) - Math.min(...xs)).toFixed(1);
  const height = (Math.max(...ys) - Math.min(...ys)).toFixed(1);

  panel.innerHTML = `
    <div class="info-group"><div class="label">Topology</div><div class="value">${{entry.topology}}</div></div>
    <div class="info-group"><div class="label">Span</div><div class="value">${{span}} m</div></div>
    <div class="info-group"><div class="label">Height</div><div class="value">${{height}} m</div></div>
    <div class="info-group"><div class="label">Nodes</div><div class="value">${{entry.nodes}}</div></div>
    <div class="info-group"><div class="label">Elements</div><div class="value">${{entry.elements}}</div></div>
    <div class="info-group"><div class="label">Materials</div><div class="value">${{mats}}</div></div>
    <div class="info-group"><div class="label">Total Load</div><div class="value">${{(totalLoad/1e3).toFixed(1)}} kN</div></div>
    <div class="info-group"><div class="label">Weight</div><div class="value highlight">${{entry.weight_kg.toFixed(1)}} kg</div></div>
    <div class="info-group"><div class="label">Cost</div><div class="value highlight">$${{entry.cost_usd.toFixed(2)}}</div></div>
  `;
}}

// --- Interaction ---
function setupInteraction() {{
  const canvas = document.getElementById('canvas');

  canvas.addEventListener('wheel', e => {{
    e.preventDefault();
    const factor = e.deltaY > 0 ? 0.9 : 1.1;
    zoom *= factor;
    zoom = Math.max(0.2, Math.min(10, zoom));
    drawTruss();
  }});

  canvas.addEventListener('mousedown', e => {{
    isDragging = true;
    dragStart = {{ x: e.clientX - pan.x, y: e.clientY - pan.y }};
    canvas.style.cursor = 'grabbing';
  }});

  canvas.addEventListener('mousemove', e => {{
    if (!isDragging) return;
    pan.x = e.clientX - dragStart.x;
    pan.y = e.clientY - dragStart.y;
    drawTruss();
  }});

  canvas.addEventListener('mouseup', () => {{
    isDragging = false;
    canvas.style.cursor = 'default';
  }});

  canvas.addEventListener('mouseleave', () => {{
    isDragging = false;
    canvas.style.cursor = 'default';
  }});

  document.getElementById('resetZoom').onclick = () => {{
    zoom = 1; pan = {{ x: 0, y: 0 }}; drawTruss();
  }};

  document.getElementById('prevBtn').onclick = () => {{
    if (filteredManifest.length === 0) return;
    currentIndex = (currentIndex - 1 + filteredManifest.length) % filteredManifest.length;
    selectTruss(currentIndex);
    document.querySelector('.truss-item.selected')?.scrollIntoView({{ block: 'nearest' }});
  }};

  document.getElementById('nextBtn').onclick = () => {{
    if (filteredManifest.length === 0) return;
    currentIndex = (currentIndex + 1) % filteredManifest.length;
    selectTruss(currentIndex);
    document.querySelector('.truss-item.selected')?.scrollIntoView({{ block: 'nearest' }});
  }};

  document.addEventListener('keydown', e => {{
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {{
      e.preventDefault(); document.getElementById('prevBtn').click();
    }} else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {{
      e.preventDefault(); document.getElementById('nextBtn').click();
    }}
  }});

  document.getElementById('search').addEventListener('input', applyFilter);

  ['showNodeIds', 'showElemIds', 'showLoads', 'showAreas', 'showMaterials'].forEach(id => {{
    document.getElementById(id).addEventListener('change', drawTruss);
  }});

  window.addEventListener('resize', drawTruss);
}}

// --- Init ---
buildFilters();
buildList();
selectTruss(0);
setupInteraction();
</script>
</body>
</html>"""


if __name__ == "__main__":
    build_viewer()
