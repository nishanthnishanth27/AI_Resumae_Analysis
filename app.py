"""
Flask web server for the Resume Screening AI System.
Run:  python app.py
Then open http://localhost:5000
"""

from flask import Flask, request, jsonify, render_template_string
import json
import os

from resume_screener import ResumeScreener

app = Flask(__name__)

# ──────────────────────────────────────────────
# HTML template (inline, no separate files needed)
# ──────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>ResumeAI — Smart Resume Screening</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Syne+Mono&family=Nunito:wght@300;400;500;600&display=swap" rel="stylesheet"/>
<style>
  :root {
    --bg: #07080f;
    --surface: #0d0e1a;
    --card: #111220;
    --card2: #161728;
    --border: #1e2035;
    --accent: #6c63ff;
    --accent2: #00d4ff;
    --green: #00e5a0;
    --gold: #ffd166;
    --red: #ff4d6d;
    --orange: #ff9a3c;
    --text: #e2e4f0;
    --muted: #5c6080;
    --serif: 'Syne', sans-serif;
    --mono: 'Syne Mono', monospace;
    --body: 'Nunito', sans-serif;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body {
    background: var(--bg); color: var(--text);
    font-family: var(--body); min-height: 100vh; overflow-x: hidden;
  }
  body::before {
    content: ''; position: fixed; inset: 0;
    background-image:
      linear-gradient(rgba(108,99,255,.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(108,99,255,.03) 1px, transparent 1px);
    background-size: 44px 44px;
    pointer-events: none; z-index: 0;
  }
  .orb { position: fixed; border-radius: 50%; filter: blur(130px); pointer-events: none; z-index: 0; }
  .orb-1 { width: 550px; height: 550px; background: #6c63ff; top: -200px; left: -180px; opacity: .25; }
  .orb-2 { width: 450px; height: 450px; background: #00d4ff; bottom: -160px; right: -120px; opacity: .18; }
  .wrap { position: relative; z-index: 1; max-width: 1100px; margin: 0 auto; padding: 0 20px; }

  /* Header */
  header { padding: 36px 0 28px; display: flex; align-items: center; gap: 14px; }
  .logo {
    width: 46px; height: 46px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 13px; display: flex; align-items: center; justify-content: center;
    font-size: 22px; box-shadow: 0 0 24px rgba(108,99,255,.4);
  }
  .logo-name { font-family: var(--serif); font-size: 26px; font-weight: 800; letter-spacing: -1px; }
  .logo-name span { color: var(--accent2); }
  .pill {
    margin-left: auto;
    background: rgba(0,229,160,.1); border: 1px solid rgba(0,229,160,.2);
    color: var(--green); font-family: var(--mono); font-size: 11px;
    padding: 4px 12px; border-radius: 20px;
  }

  /* Hero */
  .hero { padding: 8px 0 36px; }
  .hero h1 {
    font-family: var(--serif); font-size: clamp(30px, 5vw, 52px);
    font-weight: 800; line-height: 1.1; letter-spacing: -1px; margin-bottom: 12px;
  }
  .hero h1 .hi { color: var(--accent); }
  .hero h1 .hi2 { color: var(--accent2); }
  .hero p { color: var(--muted); font-size: 15px; max-width: 500px; }

  /* Feature chips */
  .chips { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 28px; }
  .chip {
    background: rgba(255,255,255,.04); border: 1px solid var(--border);
    border-radius: 30px; padding: 7px 14px; font-size: 12px; color: var(--muted);
    display: flex; align-items: center; gap: 6px;
  }
  .chip .dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }

  /* Grid */
  .main-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; }
  @media(max-width: 740px) { .main-grid { grid-template-columns: 1fr; } }

  /* Cards */
  .card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 20px; padding: 24px; transition: border-color .25s;
  }
  .card:focus-within { border-color: rgba(108,99,255,.4); }
  .sec-label {
    font-family: var(--mono); font-size: 10px; color: var(--accent);
    letter-spacing: 2.5px; text-transform: uppercase; margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
  }
  .sec-label::before { content: ''; display: block; width: 6px; height: 6px; background: var(--accent); border-radius: 50%; }

  label.fl { font-size: 12px; color: var(--muted); margin-bottom: 6px; display: block; font-weight: 600; }
  textarea, input[type="text"], input[type="number"] {
    width: 100%; background: rgba(255,255,255,.04); border: 1px solid var(--border);
    border-radius: 10px; padding: 11px 13px; color: var(--text);
    font-family: var(--body); font-size: 13.5px; outline: none; resize: vertical;
    transition: border-color .2s, background .2s;
  }
  textarea:focus, input:focus {
    border-color: rgba(108,99,255,.45); background: rgba(108,99,255,.04);
  }
  textarea { min-height: 120px; }

  /* Resume entries */
  .resume-list { display: flex; flex-direction: column; gap: 12px; }
  .resume-entry {
    background: rgba(255,255,255,.025); border: 1px solid var(--border);
    border-radius: 14px; padding: 14px;
    animation: fadeUp .3s ease both;
  }
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(-6px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .entry-top { display: flex; gap: 8px; align-items: center; margin-bottom: 10px; }
  .entry-num {
    width: 26px; height: 26px; background: var(--border); border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    font-family: var(--mono); font-size: 10px; color: var(--muted); flex-shrink: 0;
  }
  .entry-top input { flex: 1; }
  .btn-rm {
    background: none; border: none; color: var(--muted); cursor: pointer;
    font-size: 17px; padding: 2px 6px; border-radius: 6px;
    transition: color .2s, background .2s;
  }
  .btn-rm:hover { color: var(--red); background: rgba(255,77,109,.1); }

  /* Upload zone */
  .upload-zone {
    border: 2px dashed var(--border); border-radius: 12px;
    padding: 16px 14px; text-align: center; cursor: pointer;
    transition: border-color .2s, background .2s;
    background: rgba(108,99,255,.03); margin-bottom: 8px; position: relative;
  }
  .upload-zone:hover, .upload-zone.dragover {
    border-color: var(--accent); background: rgba(108,99,255,.09);
  }
  .upload-zone input[type="file"] {
    position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%; height: 100%;
  }
  .uz-icon { font-size: 24px; margin-bottom: 5px; }
  .uz-text { font-size: 12px; color: var(--muted); }
  .uz-text strong { color: var(--accent); }
  .img-prev {
    width: 100%; max-height: 110px; object-fit: cover; border-radius: 8px;
    margin-bottom: 6px; display: none; border: 1px solid var(--border);
  }
  .ocr-status {
    font-size: 11px; font-family: var(--mono);
    padding: 5px 10px; border-radius: 6px; margin-top: 6px; display: none;
  }
  .ocr-loading { background: rgba(108,99,255,.15); color: var(--accent); }
  .ocr-done    { background: rgba(0,229,160,.12); color: var(--green); }
  .ocr-error   { background: rgba(255,77,109,.12); color: var(--red); }
  .or-row {
    display: flex; align-items: center; gap: 10px; margin: 10px 0;
    font-size: 11px; color: var(--muted); font-family: var(--mono);
  }
  .or-row::before, .or-row::after { content: ''; flex: 1; height: 1px; background: var(--border); }

  /* Buttons */
  .btn-add {
    width: 100%; margin-top: 12px;
    background: rgba(108,99,255,.1); border: 1px dashed rgba(108,99,255,.35);
    border-radius: 10px; padding: 10px; color: var(--accent);
    font-family: var(--body); font-size: 13px; cursor: pointer;
    transition: background .2s, border-color .2s;
  }
  .btn-add:hover { background: rgba(108,99,255,.18); border-color: rgba(108,99,255,.6); }
  .btn-screen {
    width: 100%; padding: 15px;
    background: linear-gradient(135deg, var(--accent), #5046d6);
    border: none; border-radius: 14px; color: #fff;
    font-family: var(--serif); font-size: 17px; font-weight: 700;
    cursor: pointer; margin-top: 18px; letter-spacing: -.2px;
    transition: transform .15s, box-shadow .2s, opacity .2s;
    box-shadow: 0 8px 30px rgba(108,99,255,.35); position: relative; overflow: hidden;
  }
  .btn-screen::after { content: ''; position: absolute; inset: 0; background: linear-gradient(135deg,rgba(255,255,255,.1),transparent); }
  .btn-screen:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 14px 40px rgba(108,99,255,.5); }
  .btn-screen:disabled { opacity: .5; cursor: not-allowed; }
  .settings-row { display: flex; align-items: center; gap: 10px; margin-top: 14px; }
  .settings-row label { margin: 0; white-space: nowrap; color: var(--muted); font-size: 13px; }
  .settings-row input { width: 70px; min-height: unset; }
  .err-box {
    background: rgba(255,77,109,.1); border: 1px solid rgba(255,77,109,.3);
    border-radius: 10px; padding: 12px 16px; color: var(--red);
    font-size: 13px; margin-top: 14px;
  }

  /* Results */
  #results { display: none; margin-top: 48px; padding-top: 32px; border-top: 1px solid var(--border); }
  .res-header { margin-bottom: 24px; }
  .res-title {
    font-family: var(--serif); font-size: 28px; font-weight: 700;
    margin-bottom: 4px;
  }
  #res-meta { font-size: 13px; color: var(--muted); }
  #res-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
  .res-card {
    background: var(--card2); border: 1px solid var(--border); border-radius: 16px;
    padding: 18px; display: flex; gap: 14px; position: relative;
    transition: border-color .2s, box-shadow .2s;
  }
  .res-card:hover { border-color: var(--accent); box-shadow: 0 8px 24px rgba(108,99,255,.12); }
  .rank-badge {
    position: absolute; top: -8px; left: 16px;
    width: 32px; height: 32px;
    background: var(--card); border: 1px solid var(--border);
    border-radius: 8px; display: flex; align-items: center; justify-content: center;
    font-family: var(--mono); font-size: 12px; font-weight: 700;
  }
  .rank-badge.r1 { background: rgba(0,229,160,.15); border-color: var(--green); color: var(--green); }
  .rank-badge.r2 { background: rgba(255,212,102,.15); border-color: var(--gold); color: var(--gold); }
  .rank-badge.r3 { background: rgba(255,154,60,.15); border-color: var(--orange); color: var(--orange); }
  .rank-badge.rN { background: rgba(108,99,255,.1); border-color: var(--accent); color: var(--accent); }
  .res-card > div { flex: 1; margin-top: 8px; }
  .c-name {
    font-weight: 600; font-size: 15px; margin-bottom: 10px;
    display: flex; align-items: center; gap: 8px;
  }
  .grade {
    font-family: var(--mono); font-size: 9px; padding: 3px 7px;
    border-radius: 4px; font-weight: 700; text-transform: uppercase;
  }
  .grade.gE { background: rgba(0,229,160,.15); color: var(--green); }
  .grade.gG { background: rgba(255,212,102,.15); color: var(--gold); }
  .grade.gF { background: rgba(255,154,60,.15); color: var(--orange); }
  .grade.gP { background: rgba(255,77,109,.15); color: var(--red); }
  .bar-bg { height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; margin-bottom: 10px; }
  .bar-fill { height: 100%; background: var(--accent); transition: width .5s ease; }
  .kws { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
  .kw {
    font-size: 11px; background: rgba(108,99,255,.1); color: var(--accent);
    padding: 3px 8px; border-radius: 4px; font-family: var(--mono);
  }
  .score-wrap {
    flex: 0 0 auto; display: flex; flex-direction: column;
    align-items: center; justify-content: center; position: relative;
  }
  .score-pct {
    position: absolute; font-family: var(--serif); font-size: 18px;
    font-weight: 700; color: var(--text);
  }
  .score-lbl {
    position: absolute; bottom: -18px; font-family: var(--mono);
    font-size: 10px; color: var(--muted);
  }
  .spin {
    display: inline-block; width: 14px; height: 14px;
    border: 2px solid rgba(255,255,255,.3); border-top-color: #fff;
    border-radius: 50%; animation: spin .8s linear infinite; margin-right: 6px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="wrap">
  <header>
    <div class="logo">⚡</div>
    <div class="logo-name">Resume<span>AI</span></div>
    <div class="pill">SCREENING ENGINE</div>
  </header>

  <section class="hero">
    <h1>Rank Your <span class="hi">Talent</span> with <span class="hi2">AI</span></h1>
    <p>Upload resume images or paste text. Smart NLP matching ranks candidates by job fit.</p>
    <div class="chips">
      <span class="chip"><span class="dot" style="background:var(--accent);"></span>AI-Powered</span>
      <span class="chip"><span class="dot" style="background:var(--green);"></span>Zero-Config</span>
      <span class="chip"><span class="dot" style="background:var(--accent2);"></span>Instant Results</span>
    </div>
  </section>

  <div class="main-grid">
    <!-- Job Description -->
    <div class="card">
      <div class="sec-label">Job Description</div>
      <label class="fl">Paste the full job posting here</label>
      <textarea id="job-desc" placeholder="Senior Python Developer with ML/NLP experience..."></textarea>
    </div>

    <!-- Resumes -->
    <div class="card">
      <div class="sec-label">Resumes</div>
      <div class="resume-list" id="resume-list"></div>
      <button class="btn-add" onclick="addResume()">+ Add Candidate</button>
      <div class="settings-row">
        <label class="fl">Show top</label>
        <input type="number" id="top-n" value="5" min="1">
        <label class="fl">candidates</label>
      </div>
      <button id="screen-btn" class="btn-screen" onclick="runScreen()">⚡ Screen Candidates</button>
      <div id="err-area"></div>
    </div>
  </div>

  <!-- Results Section -->
  <section id="results">
    <div class="res-header">
      <div class="res-title">🎯 Results</div>
      <div id="res-meta"></div>
    </div>
    <div id="res-grid"></div>
  </section>
</div>

<script>
  let resumeCounter = 0;

  function addResume() {
    resumeCounter++;
    const id = resumeCounter;
    const text = '';
    const list = document.getElementById('resume-list');
    const entry = document.createElement('div');
    entry.id = `entry-${id}`;
    entry.className = 'resume-entry';
    entry.innerHTML = `
      <div class="entry-top">
        <div class="entry-num" id="num-${id}">01</div>
        <input type="text" id="name-${id}" placeholder="Name">
        <button class="btn-rm" onclick="removeResume(${id})">✕</button>
      </div>
      <div class="upload-zone" id="uz-${id}" ondragover="dragOver(event,${id})" ondragleave="dragLeave(${id})" ondrop="dropFile(event,${id})">
        <div id="uzicon-${id}" class="uz-icon">🖼️</div>
        <div class="uz-text"><strong>Click or drag</strong> resume image</div>
        <div class="uz-text" style="font-size:10px;margin-top:4px;">JPG · PNG · WEBP</div>
        <input type="file" id="file-${id}" accept="image/*" onchange="handleFile(event,${id})">
      </div>
      <img id="prev-${id}" class="img-prev" alt="preview">
      <div id="ocr-${id}" class="ocr-status"></div>
      <div class="or-row">TYPE / PASTE</div>
      <textarea placeholder="Paste resume text here..." id="text-${id}">${esc(text)}</textarea>
    `;
    list.appendChild(entry);
    renumber();
  }

  function removeResume(id) {
    const el = document.getElementById(`entry-${id}`);
    if (el) el.remove();
    renumber();
  }

  function renumber() {
    document.querySelectorAll('.resume-entry').forEach((el, i) => {
      const id = el.id.replace('entry-','');
      const num = document.getElementById(`num-${id}`);
      if (num) num.textContent = String(i+1).padStart(2,'0');
    });
  }

  function dragOver(e,id){ e.preventDefault(); document.getElementById(`uz-${id}`).classList.add('dragover'); }
  function dragLeave(id){ document.getElementById(`uz-${id}`).classList.remove('dragover'); }
  function dropFile(e,id){ e.preventDefault(); dragLeave(id); const f=e.dataTransfer.files[0]; if(f) processFile(f,id); }
  function handleFile(e,id){ const f=e.target.files[0]; if(f) processFile(f,id); }

  async function processFile(file, id) {
    const ocrEl   = document.getElementById(`ocr-${id}`);
    const prev    = document.getElementById(`prev-${id}`);
    const icon    = document.getElementById(`uzicon-${id}`);
    const textarea= document.getElementById(`text-${id}`);

    if (file.type.startsWith('image/')) {
      prev.src = URL.createObjectURL(file);
      prev.style.display = 'block';
      icon.style.display = 'none';
    }

    ocrEl.className = 'ocr-status ocr-loading';
    ocrEl.style.display = 'block';
    ocrEl.textContent = '⏳ AI reading image...';

    try {
      const base64 = await toBase64(file);
      const mediaType = file.type || 'image/jpeg';

      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 1000,
          messages: [{
            role: 'user',
            content: [
              { type: 'image', source: { type: 'base64', media_type: mediaType, data: base64 } },
              { type: 'text', text: 'Extract ALL text from this resume image. Return ONLY plain text—no markdown, no formatting. Just the resume text exactly as written.' }
            ]
          }]
        })
      });

      const data = await response.json();
      if (data.error) throw new Error(data.error.message);

      const extracted = data.content.map(b => b.text || '').join('\\n').trim();
      if (!extracted) throw new Error('No text detected in image');

      textarea.value = extracted;

      const nameInput = document.getElementById(`name-${id}`);
      if (!nameInput.value.trim()) {
        const firstLine = extracted.split('\\n').find(l => l.trim().length > 1 && l.trim().length < 50);
        if (firstLine) nameInput.value = firstLine.trim();
      }

      ocrEl.className = 'ocr-status ocr-done';
      ocrEl.textContent = `✅ Extracted ${extracted.length} characters`;

    } catch (err) {
      ocrEl.className = 'ocr-status ocr-error';
      ocrEl.textContent = `❌ ${err.message}`;
    }
  }

  function toBase64(file) {
    return new Promise((res, rej) => {
      const r = new FileReader();
      r.onload = () => res(r.result.split(',')[1]);
      r.onerror = () => rej(new Error('File read failed'));
      r.readAsDataURL(file);
    });
  }

  async function runScreen() {
    const btn = document.getElementById('screen-btn');
    const errArea = document.getElementById('err-area');
    errArea.innerHTML = '';

    const jobDesc = document.getElementById('job-desc').value.trim();
    if (!jobDesc) { showErr('Please enter a job description.'); return; }

    const entries = document.querySelectorAll('.resume-entry');
    const resumes = [];
    for (const entry of entries) {
      const id = entry.id.replace('entry-','');
      const name = document.getElementById(`name-${id}`)?.value.trim() || `Candidate ${id}`;
      const text = document.getElementById(`text-${id}`)?.value.trim() || '';
      if (text) resumes.push({ name, text });
    }
    if (!resumes.length) { showErr('Please add at least one resume with text.'); return; }

    const topN = parseInt(document.getElementById('top-n').value) || resumes.length;
    btn.disabled = true;
    btn.innerHTML = '<span class="spin"></span>Analysing candidates…';

    try {
      const resp = await fetch('/api/screen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_description: jobDesc, resumes, top_n: topN })
      });
      const data = await resp.json();
      if (!resp.ok) thro
