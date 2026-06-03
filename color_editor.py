#!/usr/bin/env python3
"""color_editor.py
Fixed: Picker opens downward, manual color input added, hint text removed.
Usage: python3 color_editor.py [path/to/config.py]
"""

import http.server
import json
import urllib.parse
import re
import ast
import random
import os
import sys
from typing import Dict, List, Tuple

# ─── Core CSP Solver ────────────────────────────────────────────────────────
PALETTE = [
    "#f5e0dc", "#f2cdcd", "#f5c2e7", "#cba6f7", "#f38ba8", "#eba0ac",
    "#fab387", "#f9e2af", "#a6e3a1", "#94e2d5", "#89b4fa", "#b4befe",
    "#ffd6a5", "#ffe8d6", "#cdeac0", "#bfefff", "#e0c8ff", "#ffd1dc",
    "#d9e2f3", "#fffbdb", "#d0f4de", "#e6e6ff", "#f0d9ff", "#cdd6f4",
]

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

PALETTE_RGB = [hex_to_rgb(c) for c in PALETTE]

def dist_rgb(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)**0.5

def build_neighbors(rows: int, cols: int):
    def neighbors(idx: int):
        r, c = divmod(idx, cols)
        n = []
        if c > 0: n.append(idx - 1)
        if c < cols - 1: n.append(idx + 1)
        if r > 0: n.append(idx - cols)
        if r < rows - 1: n.append(idx + cols)
        if r > 0 and c > 0: n.append(idx - cols - 1)
        if r > 0 and c < cols - 1: n.append(idx - cols + 1)
        if r < rows - 1 and c > 0: n.append(idx + cols - 1)
        if r < rows - 1 and c < cols - 1: n.append(idx + cols + 1)
        return n
    return neighbors

def generate_assignment(rows: int, cols: int, max_tries: int = 5000) -> List[str]:
    if rows <= 0 or cols <= 0:
        raise ValueError("Rows and cols must be positive")
    n = rows * cols
    neigh_fn = build_neighbors(rows, cols)
    incompatible = {
        i: set(j for j in range(len(PALETTE)) if dist_rgb(PALETTE_RGB[i], PALETTE_RGB[j]) < 70.0)
        for i in range(len(PALETTE))
    }
    solution = [None] * n
    domains = [list(range(len(PALETTE))) for _ in range(n)]
    attempts = 0

    def backtrack(pos: int) -> bool:
        nonlocal attempts
        attempts += 1
        if attempts > max_tries: return False
        if pos >= n: return True
        idx = pos
        assigned_neighbors = [solution[nb] for nb in neigh_fn(idx) if solution[nb] is not None]
        choices = domains[idx].copy()
        random.shuffle(choices)
        for color_i in choices:
            if any(nb_c in incompatible[color_i] for nb_c in assigned_neighbors): continue
            solution[idx] = color_i
            saved, fail = [], False
            for nb in neigh_fn(idx):
                if solution[nb] is None:
                    saved.append((nb, domains[nb].copy()))
                    domains[nb] = [d for d in domains[nb] if d not in incompatible[color_i]]
                    if not domains[nb]: fail = True; break
            if not fail and backtrack(pos + 1): return True
            for nb, dom in saved: domains[nb] = dom
            solution[idx] = None
        return False

    if not backtrack(0):
        raise RuntimeError("Solver failed: try relaxing threshold or using fewer colors.")
    return [PALETTE[i] for i in solution]

# ─── Config Parser & Writer ────────────────────────────────────────────────
def find_matching_bracket(txt, start_idx):
    depth, in_str, escaped, i = 0, None, False, start_idx
    while i < len(txt):
        c = txt[i]
        if escaped: escaped = False; i += 1; continue
        if c == '\\': escaped = True; i += 1; continue
        if in_str:
            if c == in_str: in_str = None
        elif c in ('"', "'"): in_str = c
        elif c == '#':
            next_nl = txt.find('\n', i)
            i = next_nl if next_nl != -1 else len(txt) - 1; continue
        elif c == '[': depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0: return i
        i += 1
    return -1

def parse_config(path: str) -> Dict:
    with open(path, 'r') as f: text = f.read()
    pages = {}
    for m in re.finditer(r'PAGE(\d+)_MACRO_ROWS\s*=\s*(\d+)', text):
        pid = int(m.group(1)); pages.setdefault(pid, {})['rows'] = int(m.group(2))
    for m in re.finditer(r'PAGE(\d+)_MACRO_COLS\s*=\s*(\d+)', text):
        pid = int(m.group(1)); pages.setdefault(pid, {})['cols'] = int(m.group(2))
    for m in re.finditer(r'PAGE(\d+)_MACROS\s*=', text):
        pid = int(m.group(1))
        start_search = m.end()
        bracket_start = text.find('[', start_search)
        if bracket_start != -1:
            bracket_end = find_matching_bracket(text, bracket_start)
            if bracket_end != -1:
                list_text = text[bracket_start:bracket_end+1]
                try:
                    macros = ast.literal_eval(list_text)
                    if all(isinstance(item, list) and len(item) == 4 for item in macros):
                        pages[pid]['macros'] = macros
                except Exception as e: print(f"⚠️ PAGE{pid}: Parse error: {e}")
    pages = {pid: p for pid, p in pages.items() if 'rows' in p and 'cols' in p and 'macros' in p}
    return pages

def format_macros_list(macros):
    lines = ['[']
    for item in macros:
        lines.append('    ' + repr(item) + ',')
    lines.append(']')
    return '\n'.join(lines)

def update_config_file(path: str, pages: Dict) -> str:
    with open(path, 'r') as f: text = f.read()
    for pid in sorted(pages.keys(), reverse=True):
        if 'macros' not in pages[pid]: continue
        macros_str = format_macros_list(pages[pid]['macros'])
        pattern = re.compile(r'(PAGE' + str(pid) + r'_MACROS\s*=\s*)')
        for m in pattern.finditer(text):
            bracket_start = text.find('[', m.end())
            if bracket_start != -1:
                bracket_end = find_matching_bracket(text, bracket_start)
                if bracket_end != -1:
                    text = text[:bracket_start] + macros_str + text[bracket_end+1:]
    tmp = path + '.tmp'
    with open(tmp, 'w') as f: f.write(text)
    os.replace(tmp, path)
    return "Saved successfully"

# ─── Web UI Template ────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ProxPad Macro Color Editor</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
<style>
  :root { --bg: #0f172a; --card: #1e293b; --accent: #818cf8; --text: #f8fafc; --muted: #94a3b8; --border: #334155; }
  * { box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }
  .container { max-width: 900px; margin: 0 auto; }
  header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
  h1 { margin: 0; font-size: 1.6rem; }
  .controls { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; background: var(--card); padding: 12px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  button, input { padding: 10px 14px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; }
  button { background: var(--accent); color: white; border: none; cursor: pointer; font-weight: 500; }
  button:hover { filter: brightness(1.1); }
  button.secondary { background: var(--border); color: var(--text); }
  .tabs { display: flex; gap: 8px; margin-bottom: 15px; overflow-x: auto; padding-bottom: 5px; }
  .tab { padding: 8px 16px; border-radius: 20px; border: 1px solid var(--border); background: var(--card); cursor: pointer; white-space: nowrap; }
  .tab.active { background: var(--accent); color: white; border-color: var(--accent); }
  .grid-wrap { background: var(--card); padding: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); min-height: 300px; overflow: visible !important; }
  #grid { display: grid; gap: 12px; }
  .cell { aspect-ratio: 1; border-radius: 12px; cursor: pointer; position: relative; border: 2px solid transparent; transition: all 0.2s; display: grid; place-items: center; overflow: visible !important; pointer-events: auto; z-index: 1; }
  .cell:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.15); border-color: var(--accent); }
  .cell.active { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(99,102,241,0.3); transform: scale(0.98); z-index: 1000; }
  .cell-content { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; height: 100%; pointer-events: none; padding: 6px; }
  .cell-icon { display: flex; align-items: center; justify-content: center; margin-bottom: 6px; background: transparent !important; }
  .cell-icon img { width: 32px; height: 32px; background: transparent !important; image-rendering: auto; object-fit: contain; border-radius: 6px; pointer-events: none; }
  .cell-icon i { font-size: 28px; color: #0f172a; pointer-events: none; }
  .cell-label { font-size: 0.75rem; font-weight: 600; color: #0f172a; text-align: center; line-height: 1.2; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; pointer-events: none; }
  .picker { position: absolute; top: 110%; left: 50%; transform: translateX(-50%); background: white; border: 1px solid var(--border); border-radius: 10px; padding: 10px; display: none; z-index: 1000; box-shadow: 0 8px 24px rgba(0,0,0,0.15); width: 260px; pointer-events: auto; margin-top: 10px; }
  .picker.show { display: block; }
  .swatch-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; justify-items: center; }
  .swatch { width: 40px; height: 40px; border-radius: 8px; cursor: pointer; border: 2px solid transparent; pointer-events: auto !important; }
  .swatch:hover { transform: scale(1.1); border-color: var(--accent); }
  .cp-divider { height: 1px; background: var(--border); margin: 10px 0 6px; }
  .cp { display: flex; flex-direction: column; gap: 8px; }
  .cp-sv {
    position: relative; width: 100%; aspect-ratio: 16 / 9;
    border-radius: 6px; background-color: #ff0000;
    cursor: crosshair; user-select: none; touch-action: none;
  }
  .cp-sv::before, .cp-sv::after { content: ''; position: absolute; inset: 0; border-radius: inherit; pointer-events: none; }
  .cp-sv::before { background: linear-gradient(to right, #fff, transparent); }
  .cp-sv::after { background: linear-gradient(to top, #000, transparent); }
  .cp-hue {
    position: relative; height: 12px; border-radius: 6px;
    background: linear-gradient(to right, #ff0000 0%, #ffff00 17%, #00ff00 33%, #00ffff 50%, #0000ff 67%, #ff00ff 83%, #ff0000 100%);
    cursor: pointer; user-select: none; touch-action: none;
  }
  .cp-rgb { display: flex; flex-direction: column; gap: 6px; }
  .cp-slider { position: relative; height: 10px; border-radius: 5px; cursor: pointer; user-select: none; touch-action: none; }
  .cp-slider-track { position: absolute; inset: 0; border-radius: inherit; }
  .cp-slider-r .cp-slider-track { background: linear-gradient(to right, #000, #ff0000); }
  .cp-slider-g .cp-slider-track { background: linear-gradient(to right, #000, #00ff00); }
  .cp-slider-b .cp-slider-track { background: linear-gradient(to right, #000, #0000ff); }
  .cp-cursor {
    position: absolute; top: 50%; width: 12px; height: 12px;
    background: #fff; border: 2px solid #fff; border-radius: 50%;
    box-shadow: 0 0 0 1px rgba(0,0,0,0.4);
    transform: translate(-50%, -50%); pointer-events: none; z-index: 2;
  }
  .cp-hex-row { display: flex; align-items: center; gap: 4px; }
  .cp-hash { font-family: monospace; color: var(--muted); font-size: 0.9rem; }
  .cp-hex {
    flex: 1; font-family: monospace; text-transform: uppercase;
    padding: 6px; border: 1px solid var(--border); border-radius: 4px; font-size: 0.85rem;
  }
  .cp-randomize {
    padding: 6px 10px; font-size: 0.8rem; cursor: pointer;
    background: var(--accent); color: white; border: none; border-radius: 5px;
    font-weight: 500; text-align: center;
  }
  .cp-randomize:hover { filter: brightness(1.15); }
  .status { margin-top: 10px; font-size: 0.9rem; color: var(--muted); min-height: 20px; }
  .hint { font-size: 0.85rem; color: var(--accent); margin-bottom: 12px; text-align: center; font-weight: 500; }
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>⌨️ ProxPad Macro Color Editor</h1>
    <div style="text-align:right">
      <span id="config-path" style="font-size:0.85rem;color:var(--muted)">config.py</span>
    </div>
  </header>

  <div class="controls">
    <input type="text" id="config-path-input" value="config.py" style="width:180px" placeholder="config.py path">
    <button onclick="loadConfig()">📂 Load Config</button>
    <button onclick="randomizePage()" class="secondary">🎲 Randomize Page</button>
    <button onclick="saveConfig()" class="secondary">💾 Save to Config</button>
    <button onclick="exportPage()" class="secondary">📋 Copy List</button>
  </div>

  <p class="hint">👆 Click any button to pick a color manually.</p>

  <div class="tabs" id="tabs"></div>
  <div class="grid-wrap">
    <div id="grid"></div>
  </div>

  <div class="status" id="status">Select a config path and click "Load Config" to begin.</div>
</div>

<script>
const palette = [
  "#f5e0dc","#f2cdcd","#f5c2e7","#cba6f7","#f38ba8","#eba0ac","#fab387","#f9e2af",
  "#a6e3a1","#94e2d5","#89b4fa","#b4befe","#ffd6a5","#ffe8d6","#cdeac0","#bfefff",
  "#e0c8ff","#ffd1dc","#d9e2f3","#fffbdb","#d0f4de","#e6e6ff","#f0d9ff","#cdd6f4"
];

let pagesData = {};
let activePage = 1;
let activeCell = null;
const pickers = {};

function componentToHex(c) { const h = Math.round(c).toString(16); return h.length === 1 ? '0' + h : h; }
function rgbToHex(r, g, b) { return '#' + componentToHex(r) + componentToHex(g) + componentToHex(b); }
function hexToRgb(hex) {
  const h = hex.replace('#', '');
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}
function rgbToHsv(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
  let h = 0;
  const s = max === 0 ? 0 : d / max;
  const v = max;
  if (d !== 0) {
    if (max === r) h = ((g - b) / d) % 6;
    else if (max === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    h *= 60;
    if (h < 0) h += 360;
  }
  return [h, s * 100, v * 100];
}
function hsvToRgb(h, s, v) {
  s /= 100; v /= 100;
  const c = v * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = v - c;
  let r, g, b;
  if (h < 60)       [r, g, b] = [c, x, 0];
  else if (h < 120) [r, g, b] = [x, c, 0];
  else if (h < 180) [r, g, b] = [0, c, x];
  else if (h < 240) [r, g, b] = [0, x, c];
  else if (h < 300) [r, g, b] = [x, 0, c];
  else              [r, g, b] = [c, 0, x];
  return [Math.round((r + m) * 255), Math.round((g + m) * 255), Math.round((b + m) * 255)];
}
function randomHex() {
  const h = Math.floor(Math.random() * 360);
  const s = 60 + Math.floor(Math.random() * 40);
  const v = 70 + Math.floor(Math.random() * 30);
  const [r, g, b] = hsvToRgb(h, s, v);
  return rgbToHex(r, g, b);
}

function setStatus(msg) { document.getElementById('status').textContent = msg; }

async function loadConfig() {
  const path = document.getElementById('config-path-input').value.trim() || 'config.py';
  document.getElementById('config-path').textContent = path;
  setStatus('Loading config...');
  try {
    const res = await fetch('/api/load', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({config_path: path})
    });
    if(!res.ok) throw new Error(await res.text());
    const data = await res.json();
    if(!data.pages || Object.keys(data.pages).length === 0) {
      setStatus('❌ No PAGE#_MACROS blocks found.'); return;
    }
    pagesData = data.pages;
    renderTabs();
    renderPage(activePage);
    setStatus(`✅ Loaded ${Object.keys(pagesData).length} page(s).`);
  } catch(e) {
    setStatus(`❌ ${e.message}`); console.error(e);
  }
}

function renderTabs() {
  const tabsEl = document.getElementById('tabs');
  tabsEl.innerHTML = '';
  Object.keys(pagesData).sort((a,b)=>a-b).forEach(pid => {
    const btn = document.createElement('div');
    btn.className = `tab ${pid == activePage ? 'active' : ''}`;
    btn.textContent = `PAGE ${pid}`;
    btn.onclick = () => { activePage = parseInt(pid); renderTabs(); renderPage(pid); };
    tabsEl.appendChild(btn);
  });
}

function renderPage(pid) {
  for (const k in pickers) delete pickers[k];
  const page = pagesData[pid];
  if (!page || !page.macros || !page.rows || !page.cols) {
    setStatus('❌ Invalid page data. Please reload config.'); return;
  }
  const grid = document.getElementById('grid');
  grid.style.gridTemplateColumns = `repeat(${page.cols}, 1fr)`;
  grid.innerHTML = '';
  page.macros.forEach((macro, i) => {
    const cell = document.createElement('div');
    cell.className = 'cell';
    cell.dataset.index = i;
    cell.style.backgroundColor = macro[0];
    cell.title = macro[1];
    const iconStr = macro[2] || '';
    let iconHTML = '';
    if (iconStr.startsWith('bi bi-')) iconHTML = `<i class="bi ${iconStr}"></i>`;
    else if (iconStr.startsWith('http')) iconHTML = `<img src="${iconStr}" alt="icon" loading="lazy" onerror="this.style.display='none'">`;
    
    cell.innerHTML = `
      <div class="cell-content">
        <div class="cell-icon">${iconHTML}</div>
        <div class="cell-label">${macro[1].length > 8 ? macro[1].slice(0,6)+'..' : macro[1]}</div>
      </div>
      <div class="picker" id="picker-${i}"></div>
    `;

    cell.addEventListener('click', (e) => {
      if (e.target.closest('.picker')) return;
      e.preventDefault();
      e.stopPropagation();
      if (activeCell === i) { closeAllPickers(); return; }
      closeAllPickers();
      cell.classList.add('active');
      buildPicker(i, cell.querySelector('.picker'), pid);
      cell.querySelector('.picker').classList.add('show');
      activeCell = i;
    });
    grid.appendChild(cell);
  });
}

function closeAllPickers() {
  document.querySelectorAll('.picker').forEach(p => p.classList.remove('show'));
  document.querySelectorAll('.cell').forEach(c => c.classList.remove('active'));
  activeCell = null;
}
document.addEventListener('click', (e) => {
  if (!e.target.closest('.cell') && !e.target.closest('.picker')) closeAllPickers();
});

function buildPicker(idx, el, pid) {
  el.innerHTML = '';

  const sg = document.createElement('div');
  sg.className = 'swatch-grid';
  palette.forEach(c => {
    const s = document.createElement('div');
    s.className = 'swatch';
    s.style.background = c;
    s.onclick = (e) => {
      e.stopPropagation();
      e.preventDefault();
      setColor(idx, c, pid);
      closeAllPickers();
    };
    sg.appendChild(s);
  });
  el.appendChild(sg);

  const div = document.createElement('div');
  div.className = 'cp-divider';
  el.appendChild(div);

  const cp = document.createElement('div');
  cp.className = 'cp';

  const sv = document.createElement('div');
  sv.className = 'cp-sv';
  const svCursor = document.createElement('div');
  svCursor.className = 'cp-cursor';
  sv.appendChild(svCursor);
  cp.appendChild(sv);

  const hue = document.createElement('div');
  hue.className = 'cp-hue';
  const hueCursor = document.createElement('div');
  hueCursor.className = 'cp-cursor';
  hue.appendChild(hueCursor);
  cp.appendChild(hue);

  function makeSlider(cls) {
    const w = document.createElement('div');
    w.className = 'cp-slider ' + cls;
    const t = document.createElement('div');
    t.className = 'cp-slider-track';
    w.appendChild(t);
    const c = document.createElement('div');
    c.className = 'cp-cursor';
    w.appendChild(c);
    return { wrap: w, cursor: c };
  }
  const rSlider = makeSlider('cp-slider-r');
  const gSlider = makeSlider('cp-slider-g');
  const bSlider = makeSlider('cp-slider-b');
  const rgb = document.createElement('div');
  rgb.className = 'cp-rgb';
  rgb.appendChild(rSlider.wrap);
  rgb.appendChild(gSlider.wrap);
  rgb.appendChild(bSlider.wrap);
  cp.appendChild(rgb);

  const hexRow = document.createElement('div');
  hexRow.className = 'cp-hex-row';
  const hash = document.createElement('span');
  hash.className = 'cp-hash';
  hash.textContent = '#';
  hexRow.appendChild(hash);
  const hexInput = document.createElement('input');
  hexInput.type = 'text';
  hexInput.className = 'cp-hex';
  hexInput.maxLength = 7;
  hexInput.spellcheck = false;
  hexRow.appendChild(hexInput);
  cp.appendChild(hexRow);

  const randBtn = document.createElement('div');
  randBtn.className = 'cp-randomize';
  randBtn.textContent = '🎲 Randomize';
  randBtn.onclick = (e) => {
    e.stopPropagation();
    const hex = randomHex();
    setFromHexSilent(hex);
    render();
    setColor(idx, hex, pid);
  };
  cp.appendChild(randBtn);

  el.appendChild(cp);

  const initialHex = pagesData[pid] && pagesData[pid].macros[idx] ? pagesData[pid].macros[idx][0] : '#ffffff';
  const [ir, ig, ib] = hexToRgb(initialHex);
  const [ih, is, iv] = rgbToHsv(ir, ig, ib);
  const state = { h: ih, s: is, v: iv, r: ir, g: ig, b: ib, hex: initialHex.toLowerCase() };

  function render() {
    const [hr, hg, hb] = hsvToRgb(state.h, 100, 100);
    sv.style.backgroundColor = rgbToHex(hr, hg, hb);
    svCursor.style.left = state.s + '%';
    svCursor.style.top = (100 - state.v) + '%';
    hueCursor.style.left = (state.h / 360) * 100 + '%';
    rSlider.cursor.style.left = (state.r / 255) * 100 + '%';
    gSlider.cursor.style.left = (state.g / 255) * 100 + '%';
    bSlider.cursor.style.left = (state.b / 255) * 100 + '%';
    const targetHex = state.hex.toUpperCase();
    if (document.activeElement !== hexInput) hexInput.value = targetHex;
  }

  function setHsv(h, s, v) {
    state.h = Math.max(0, Math.min(360, h));
    state.s = Math.max(0, Math.min(100, s));
    state.v = Math.max(0, Math.min(100, v));
    const [r, g, b] = hsvToRgb(state.h, state.s, state.v);
    state.r = r; state.g = g; state.b = b;
    state.hex = rgbToHex(r, g, b);
    render();
    setColor(idx, state.hex, pid);
  }

  function setRgb(r, g, b) {
    state.r = Math.max(0, Math.min(255, r));
    state.g = Math.max(0, Math.min(255, g));
    state.b = Math.max(0, Math.min(255, b));
    const [h, s, v] = rgbToHsv(state.r, state.g, state.b);
    state.h = h; state.s = s; state.v = v;
    state.hex = rgbToHex(state.r, state.g, state.b);
    render();
    setColor(idx, state.hex, pid);
  }

  function setFromHexSilent(hex) {
    const norm = hex.toLowerCase();
    if (norm === state.hex) return;
    const [r, g, b] = hexToRgb(hex);
    const [h, s, v] = rgbToHsv(r, g, b);
    state.r = r; state.g = g; state.b = b;
    state.h = h; state.s = s; state.v = v;
    state.hex = norm;
    render();
  }

  function dragHandler(target, onMove) {
    function start(e) {
      e.preventDefault();
      e.stopPropagation();
      const move = (ev) => {
        const p = ev.touches ? ev.touches[0] : ev;
        onMove(p);
      };
      const up = () => {
        document.removeEventListener('mousemove', move);
        document.removeEventListener('mouseup', up);
        document.removeEventListener('touchmove', move);
        document.removeEventListener('touchend', up);
      };
      document.addEventListener('mousemove', move);
      document.addEventListener('mouseup', up);
      document.addEventListener('touchmove', move, { passive: false });
      document.addEventListener('touchend', up);
      move(e);
    }
    target.addEventListener('mousedown', start);
    target.addEventListener('touchstart', start, { passive: false });
  }

  dragHandler(sv, (p) => {
    const r = sv.getBoundingClientRect();
    const x = Math.max(0, Math.min(r.width, p.clientX - r.left));
    const y = Math.max(0, Math.min(r.height, p.clientY - r.top));
    setHsv(state.h, (x / r.width) * 100, (1 - y / r.height) * 100);
  });
  dragHandler(hue, (p) => {
    const r = hue.getBoundingClientRect();
    const x = Math.max(0, Math.min(r.width, p.clientX - r.left));
    setHsv((x / r.width) * 360, state.s, state.v);
  });
  dragHandler(rSlider.wrap, (p) => {
    const r = rSlider.wrap.getBoundingClientRect();
    const x = Math.max(0, Math.min(r.width, p.clientX - r.left));
    setRgb(Math.round((x / r.width) * 255), state.g, state.b);
  });
  dragHandler(gSlider.wrap, (p) => {
    const r = gSlider.wrap.getBoundingClientRect();
    const x = Math.max(0, Math.min(r.width, p.clientX - r.left));
    setRgb(state.r, Math.round((x / r.width) * 255), state.b);
  });
  dragHandler(bSlider.wrap, (p) => {
    const r = bSlider.wrap.getBoundingClientRect();
    const x = Math.max(0, Math.min(r.width, p.clientX - r.left));
    setRgb(state.r, state.g, Math.round((x / r.width) * 255));
  });

  hexInput.addEventListener('input', () => {
    let v = hexInput.value.trim();
    if (v && !v.startsWith('#')) v = '#' + v;
    if (/^#[0-9a-fA-F]{6}$/.test(v)) {
      setFromHexSilent(v);
      setColor(idx, v, pid);
    }
  });
  hexInput.addEventListener('mousedown', (e) => e.stopPropagation());
  hexInput.addEventListener('click', (e) => e.stopPropagation());
  hexInput.addEventListener('keydown', (e) => e.stopPropagation());

  render();

  pickers[idx] = { state, setFromHexSilent };
}

function setColor(idx, color, pid) {
  pagesData[pid].macros[idx][0] = color;
  const cells = document.querySelectorAll('.cell');
  if(cells[idx]) cells[idx].style.backgroundColor = color;
  const p = pickers[idx];
  if (p && p.state.hex.toLowerCase() !== color.toLowerCase()) {
    p.setFromHexSilent(color);
  }
}

async function randomizePage() {
  const page = pagesData[activePage];
  if(!page) return setStatus('❌ Load config first.');
  setStatus('Generating non-adjacent layout...');
  try {
    const res = await fetch('/api/generate', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({rows: page.rows, cols: page.cols})
    });
    if(!res.ok) throw new Error(await res.text());
    const colors = await res.json();
    if(!Array.isArray(colors)) throw new Error('Invalid response format from server');
    colors.forEach((c, i) => {
      if(pagesData[activePage].macros[i]) setColor(i, c, activePage);
    });
    setStatus(`✅ Randomized PAGE ${activePage} (${page.rows}×${page.cols})`);
  } catch(e) {
    setStatus(`❌ ${e.message}`);
  }
}

async function saveConfig() {
  setStatus('Saving config...');
  try {
    const path = document.getElementById('config-path-input').value.trim() || 'config.py';
    const res = await fetch('/api/save', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({config_path: path, pages: pagesData})
    });
    if(!res.ok) throw new Error(await res.text());
    const data = await res.json();
    setStatus(`✅ ${data.status}`);
  } catch(e) {
    setStatus(`❌ ${e.message}`);
  }
}

async function exportPage() {
  const page = pagesData[activePage];
  if(!page) return setStatus('❌ Load config first.');
  const list = page.macros.map(m => `'${m[0]}'`).join(', ');
  const snippet = `[${list}]`;
  try {
    await navigator.clipboard.writeText(snippet);
    setStatus('📋 Color list copied to clipboard');
  } catch {
    setStatus('❌ Copy failed (use dev console)');
  }
}
</script>
</body>
</html>
"""

# ─── HTTP Server ────────────────────────────────────────────────────────────
class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length).decode()) if content_length else {}
        
        if parsed.path == '/api/load':
            try:
                pages = parse_config(body.get('config_path', 'config.py'))
                self._json(200, {"pages": pages})
            except Exception as e: self._json(500, {"error": str(e)})
        elif parsed.path == '/api/generate':
            try:
                rows, cols = body.get('rows'), body.get('cols')
                colors = generate_assignment(rows, cols)
                self._json(200, colors)
            except Exception as e: self._json(500, {"error": str(e)})
        elif parsed.path == '/api/save':
            try:
                status = update_config_file(body.get('config_path', 'config.py'), body.get('pages', {}))
                self._json(200, {"status": status})
            except Exception as e: self._json(500, {"error": str(e)})
        else: self._html(404, "Not Found")

    def do_GET(self):
        if urllib.parse.urlparse(self.path).path == '/': self._html(200, HTML)
        else: self._html(404, "Not Found")

    def _json(self, code, data):
        self.send_response(code); self.send_header('Content-Type', 'application/json'); self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _html(self, code, html):
        self.send_response(code); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args): pass

def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.py"
    port = 9999
    if not os.path.exists(config_path): print(f"⚠️ Config not found: {config_path}. Server will start, but load will fail.")
    server = http.server.HTTPServer(('0.0.0.0', port), Handler)
    print(f"✅ ProxPad Macro Color Editor running at http://localhost:{port}")
    print(f"   Config target: {os.path.abspath(config_path)}")
    print("Press Ctrl+C to stop.\n")
    try: server.serve_forever()
    except KeyboardInterrupt: print("\n🛑 Server stopped."); server.server_close()

if __name__ == "__main__":
    main()
