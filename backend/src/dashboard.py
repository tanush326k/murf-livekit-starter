"""
Day 8: Call Analytics Dashboard
A lightweight standalone server to view call analytics metrics, failure distributions,
latency trends, and open escalation requests.
Run: python src/dashboard.py
Open: http://localhost:8890
"""

import json
import os
import sys
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Ensure src/ is importable
sys.path.insert(0, os.path.dirname(__file__))
import db  # noqa: E402

DASHBOARD_PORT = 8890

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MoneyBuddy — Call Analytics & Escalations</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg-dark: #0a0f1d;
    --card-bg: rgba(255, 255, 255, 0.03);
    --card-border: rgba(255, 255, 255, 0.08);
    --primary: #10b981;
    --primary-glow: rgba(16, 185, 129, 0.25);
    --danger: #ef4444;
    --warning: #f59e0b;
    --info: #3b82f6;
    --text-main: #f1f5f9;
    --text-muted: #64748b;
  }
  body {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    background: var(--bg-dark);
    color: var(--text-main);
    min-height: 100vh;
    padding: 1.5rem 2rem;
    line-height: 1.5;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.75rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--card-border);
  }
  .brand { display: flex; align-items: center; gap: 0.85rem; }
  .brand-dot {
    width: 12px; height: 12px;
    background: var(--primary);
    border-radius: 50%;
    box-shadow: 0 0 12px var(--primary);
    animation: pulse 2s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.85); }
  }
  h1 { font-size: 1.6rem; font-weight: 700; letter-spacing: -0.02em; }
  h1 span { color: var(--primary); }
  .subtitle { color: var(--text-muted); font-size: 0.85rem; margin-top: 0.1rem; }
  
  .header-actions { display: flex; align-items: center; gap: 1rem; }
  .lang-btn {
    background: rgba(255,255,255,0.06);
    border: 1px solid var(--card-border);
    color: var(--text-main);
    padding: 0.4rem 0.85rem;
    border-radius: 8px;
    font-size: 0.8rem;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
  }
  .lang-btn:hover { background: rgba(255,255,255,0.12); }
  .lang-btn.active { border-color: var(--primary); color: var(--primary); background: rgba(16,185,129,0.1); }

  /* Filters */
  .filter-bar {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    align-items: center;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 0.85rem 1.25rem;
    margin-bottom: 1.75rem;
    backdrop-filter: blur(8px);
  }
  .filter-group { display: flex; align-items: center; gap: 0.5rem; }
  .filter-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; }
  select, input[type="date"] {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid var(--card-border);
    color: var(--text-main);
    padding: 0.4rem 0.75rem;
    border-radius: 6px;
    font-size: 0.825rem;
    outline: none;
    transition: border-color 0.2s;
  }
  select:focus, input[type="date"]:focus { border-color: var(--primary); }
  .reset-btn {
    margin-left: auto;
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 0.8rem;
    cursor: pointer;
    text-decoration: underline;
  }
  .reset-btn:hover { color: var(--text-main); }

  /* KPIs */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 1.75rem;
  }
  .kpi-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 1.15rem 1.35rem;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, border-color 0.2s;
  }
  .kpi-card:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.15); }
  .kpi-card::before {
    content: '';
    position: absolute; top: 0; left: 0; width: 100%; height: 3px;
    background: var(--card-border);
  }
  .kpi-card.primary::before { background: var(--primary); }
  .kpi-card.success::before { background: var(--primary); }
  .kpi-card.danger::before { background: var(--danger); }
  .kpi-card.info::before { background: var(--info); }
  .kpi-card.warning::before { background: var(--warning); }
  
  .kpi-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; }
  .kpi-value { font-size: 1.85rem; font-weight: 700; margin-top: 0.35rem; font-family: 'JetBrains Mono', monospace; }
  .kpi-subtext { font-size: 0.725rem; color: var(--text-muted); margin-top: 0.2rem; }

  /* Grid Layout for Charts & Content */
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; margin-bottom: 1.75rem; }
  @media (max-width: 900px) { .grid-2 { grid-template-columns: 1fr; } }
  
  .chart-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 1.25rem;
    display: flex;
    flex-col;
  }
  .chart-title { font-size: 0.9rem; font-weight: 600; margin-bottom: 1rem; color: var(--text-main); display: flex; align-items: center; justify-content: space-between; }
  .chart-box { width: 100%; height: 180px; position: relative; }

  /* Custom CSS/SVG Charts */
  .bar-chart { display: flex; align-items: flex-end; justify-content: space-around; height: 100%; gap: 0.5rem; padding-top: 1rem; }
  .bar-col { display: flex; flex-direction: column; align-items: center; flex: 1; height: 100%; justify-content: flex-end; }
  .bar-wrapper { width: 100%; max-width: 28px; background: rgba(255,255,255,0.04); border-radius: 4px; overflow: hidden; display: flex; flex-direction: column; justify-content: flex-end; height: 100%; }
  .bar-success { background: var(--primary); transition: height 0.5s ease-out; }
  .bar-failed { background: var(--danger); transition: height 0.5s ease-out; }
  .bar-date { font-size: 0.65rem; color: var(--text-muted); margin-top: 0.4rem; white-space: nowrap; }

  .dist-list { display: flex; flex-direction: column; gap: 0.65rem; justify-content: center; height: 100%; }
  .dist-item { display: flex; flex-direction: column; gap: 0.25rem; }
  .dist-header { display: flex; justify-content: space-between; font-size: 0.775rem; }
  .dist-name { color: var(--text-main); font-weight: 500; }
  .dist-count { font-family: 'JetBrains Mono', monospace; color: var(--text-muted); }
  .dist-bar-bg { width: 100%; height: 6px; background: rgba(255,255,255,0.06); border-radius: 99px; overflow: hidden; }
  .dist-bar-fill { height: 100%; border-radius: 99px; transition: width 0.5s ease-out; }

  /* Tabs */
  .nav-tabs { display: flex; gap: 0.5rem; margin-bottom: 1.25rem; border-bottom: 1px solid var(--card-border); padding-bottom: 0.5rem; }
  .tab-btn {
    background: transparent; border: none; color: var(--text-muted); padding: 0.5rem 1rem;
    font-size: 0.9rem; font-weight: 600; cursor: pointer; position: relative; transition: color 0.2s;
  }
  .tab-btn:hover { color: var(--text-main); }
  .tab-btn.active { color: var(--primary); }
  .tab-btn.active::after {
    content: ''; position: absolute; bottom: -0.5rem; left: 0; width: 100%; height: 2px; background: var(--primary);
  }

  /* Table */
  .table-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    overflow: hidden;
  }
  table { width: 100%; border-collapse: collapse; text-align: left; }
  thead { background: rgba(255,255,255,0.03); border-bottom: 1px solid var(--card-border); }
  th { padding: 0.85rem 1rem; font-size: 0.725rem; text-transform: uppercase; color: var(--text-muted); font-weight: 600; letter-spacing: 0.05em; }
  td { padding: 0.85rem 1rem; font-size: 0.825rem; border-bottom: 1px solid rgba(255,255,255,0.04); vertical-align: middle; }
  tr:last-child td { border-bottom: none; }
  tr:hover { background: rgba(255,255,255,0.02); }

  .badge {
    display: inline-flex; align-items: center; padding: 0.2rem 0.55rem; border-radius: 6px;
    font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em;
  }
  .badge-success { background: rgba(16,185,129,0.15); color: #34d399; }
  .badge-failed { background: rgba(239,68,68,0.15); color: #f87171; }
  .badge-channel { background: rgba(59,130,246,0.12); color: #60a5fa; }
  .badge-reason { background: rgba(245,158,11,0.12); color: #fbbf24; }
  .badge-escalation { background: rgba(168,85,247,0.15); color: #c084fc; }

  .call-id { font-family: 'JetBrains Mono', monospace; color: var(--primary); font-size: 0.775rem; }
  .empty-state { text-align: center; padding: 3.5rem 1.5rem; color: var(--text-muted); }
  .empty-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
  
  .status-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; font-size: 0.75rem; color: var(--text-muted); }
  .banner-msg { display: none; padding: 0.6rem 1rem; border-radius: 8px; font-size: 0.8rem; margin-bottom: 1rem; }
  .banner-error { display: block; background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); color: #f87171; }
</style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="brand-dot"></div>
      <div>
        <h1 id="title-text">Money<span>Buddy</span> Call Analytics</h1>
        <div class="subtitle" id="subtitle-text">Real-time voice agent metrics & call performance</div>
      </div>
    </div>
    <div class="header-actions">
      <button class="lang-btn active" id="btn-en" onclick="setLang('en')">English</button>
      <button class="lang-btn" id="btn-hi" onclick="setLang('hi')">हिंदी</button>
    </div>
  </header>

  <div id="banner" class="banner-msg"></div>

  <!-- Filter Bar -->
  <div class="filter-bar">
    <div class="filter-group">
      <span class="filter-label" id="lbl-date-from">From</span>
      <input type="date" id="flt-from" onchange="fetchData()">
    </div>
    <div class="filter-group">
      <span class="filter-label" id="lbl-date-to">To</span>
      <input type="date" id="flt-to" onchange="fetchData()">
    </div>
    <div class="filter-group">
      <span class="filter-label" id="lbl-channel">Channel</span>
      <select id="flt-channel" onchange="fetchData()">
        <option value="">All Channels</option>
        <option value="browser">Browser</option>
        <option value="sip">SIP / Outbound</option>
      </select>
    </div>
    <div class="filter-group">
      <span class="filter-label" id="lbl-language">Language</span>
      <select id="flt-language" onchange="fetchData()">
        <option value="">All Languages</option>
        <option value="English">English</option>
        <option value="Hindi">Hindi</option>
      </select>
    </div>
    <div class="filter-group">
      <span class="filter-label" id="lbl-outcome">Outcome</span>
      <select id="flt-outcome" onchange="fetchData()">
        <option value="">All Outcomes</option>
        <option value="successful">Successful</option>
        <option value="failed">Failed</option>
      </select>
    </div>
    <button class="reset-btn" onclick="resetFilters()" id="btn-reset">Reset Filters</button>
  </div>

  <!-- KPI Cards -->
  <div class="kpi-grid">
    <div class="kpi-card primary">
      <div class="kpi-label" id="kpi-lbl-total">Total Calls</div>
      <div class="kpi-value" id="kpi-total">-</div>
      <div class="kpi-subtext" id="kpi-sub-total">All recorded sessions</div>
    </div>
    <div class="kpi-card success">
      <div class="kpi-label" id="kpi-lbl-success">Successful Calls</div>
      <div class="kpi-value" style="color:#34d399" id="kpi-success">-</div>
      <div class="kpi-subtext" id="kpi-sub-success">Task completed successfully</div>
    </div>
    <div class="kpi-card danger">
      <div class="kpi-label" id="kpi-lbl-failed">Failed Calls</div>
      <div class="kpi-value" style="color:#f87171" id="kpi-failed">-</div>
      <div class="kpi-subtext" id="kpi-sub-failed">Task not completed</div>
    </div>
    <div class="kpi-card warning">
      <div class="kpi-label" id="kpi-lbl-rate">Success Rate</div>
      <div class="kpi-value" style="color:#fbbf24" id="kpi-rate">-%</div>
      <div class="kpi-subtext" id="kpi-sub-rate">Real database percentage</div>
    </div>
    <div class="kpi-card info">
      <div class="kpi-label" id="kpi-lbl-latency">Avg Voice Latency</div>
      <div class="kpi-value" style="color:#60a5fa" id="kpi-latency">- ms</div>
      <div class="kpi-subtext" id="kpi-sub-latency">User stop to agent speech</div>
    </div>
  </div>

  <!-- Charts Row -->
  <div class="grid-2">
    <div class="chart-card">
      <div class="chart-title">
        <span id="chart-lbl-timeline">Calls Over Time</span>
        <span style="font-size:0.75rem; color:var(--text-muted)">Daily breakdown</span>
      </div>
      <div class="chart-box" id="box-timeline">
        <div class="bar-chart" id="chart-bars"></div>
      </div>
    </div>
    <div class="chart-card">
      <div class="chart-title">
        <span id="chart-lbl-failures">Failure Type Distribution</span>
        <span style="font-size:0.75rem; color:var(--text-muted)">Reason breakdown</span>
      </div>
      <div class="chart-box" id="box-failures">
        <div class="dist-list" id="chart-failures-list"></div>
      </div>
    </div>
  </div>

  <!-- Navigation Tabs -->
  <div class="nav-tabs">
    <button class="tab-btn active" id="tab-analytics" onclick="switchTab('analytics')">Call History</button>
    <button class="tab-btn" id="tab-escalations" onclick="switchTab('escalations')">Human Escalations</button>
  </div>

  <!-- Table Container -->
  <div class="table-card" id="table-container">
    <div id="content-area"></div>
  </div>

  <div class="status-footer">
    <span id="status-live">● Live updates active (Polling 15s)</span>
    <span id="updated-at">Last refreshed: -</span>
  </div>

<script>
  let currentLang = 'en';
  let currentTab = 'analytics';
  let cachedAnalytics = [];
  let cachedSummary = {};
  let cachedCharts = {};
  let cachedEscalations = [];

  const i18n = {
    en: {
      title: "Money<span>Buddy</span> Call Analytics",
      subtitle: "Real-time voice agent metrics & call performance",
      from: "From", to: "To", channel: "Channel", language: "Language", outcome: "Outcome", reset: "Reset Filters",
      totalCalls: "Total Calls", totalSub: "All recorded sessions",
      successfulCalls: "Successful Calls", successSub: "Task completed successfully",
      failedCalls: "Failed Calls", failedSub: "Task not completed",
      successRate: "Success Rate", rateSub: "Real database percentage",
      avgLatency: "Avg Voice Latency", latencySub: "User stop to agent speech",
      timeline: "Calls Over Time", failureDist: "Failure Type Distribution",
      tabHistory: "Call History", tabEscalations: "Human Escalations",
      loading: "Loading call analytics...",
      error: "Unable to load call history. Retrying in background...",
      emptyHistory: "No call records found for selected filters.",
      emptyEscalations: "No escalation requests yet. All clear!",
      thId: "Call ID", thTime: "Time", thChannel: "Channel", thLang: "Language",
      thDuration: "Duration", thLatency: "Latency", thOutcome: "Outcome", thDetails: "Financial Result / Failure Reason"
    },
    hi: {
      title: "मनी<span>बडी</span> कॉल विश्लेषिकी",
      subtitle: "वास्तविक समय वॉयस एजेंट प्रदर्शन एवं मेट्रिक्स",
      from: "से", to: "तक", channel: "चैनल", language: "भाषा", outcome: "परिणाम", reset: "फ़िल्टर रीसेट करें",
      totalCalls: "कुल कॉल", totalSub: "सभी रिकॉर्ड की गई कॉल",
      successfulCalls: "सफल कॉल", successSub: "कार्य सफलतापूर्वक पूरा हुआ",
      failedCalls: "असफल कॉल", failedSub: "कार्य पूरा नहीं हो सका",
      successRate: "सफलता दर", rateSub: "वास्तविक डेटाबेस प्रतिशत",
      avgLatency: "औसत वॉयस रिस्पॉन्स टाइम", latencySub: "यूजर्स बोलने के बाद प्रतिक्रिया समय",
      timeline: "समय के साथ कॉल", failureDist: "विफलता प्रकार वितरण",
      tabHistory: "कॉल इतिहास", tabEscalations: "मानव सहायता टिकट",
      loading: "कॉल विश्लेषिकी लोड हो रही है...",
      error: "कॉल इतिहास लोड करने में असमर्थ। पुनः प्रयास जारी है...",
      emptyHistory: "चुने गए फ़िल्टर के लिए कोई कॉल रिकॉर्ड नहीं मिला।",
      emptyEscalations: "अभी तक कोई मानव सहायता टिकट नहीं है।",
      thId: "कॉल आईडी", thTime: "समय", thChannel: "चैनल", thLang: "भाषा",
      thDuration: "अवधि", thLatency: "विलंबता", thOutcome: "परिणाम", thDetails: "वित्तीय परिणाम / विफलता का कारण"
    }
  };

  function setLang(lang) {
    currentLang = lang;
    document.getElementById('btn-en').classList.toggle('active', lang === 'en');
    document.getElementById('btn-hi').classList.toggle('active', lang === 'hi');
    applyTranslations();
    renderAll();
  }

  function applyTranslations() {
    const t = i18n[currentLang];
    document.getElementById('title-text').innerHTML = t.title;
    document.getElementById('subtitle-text').textContent = t.subtitle;
    document.getElementById('lbl-date-from').textContent = t.from;
    document.getElementById('lbl-date-to').textContent = t.to;
    document.getElementById('lbl-channel').textContent = t.channel;
    document.getElementById('lbl-language').textContent = t.language;
    document.getElementById('lbl-outcome').textContent = t.outcome;
    document.getElementById('btn-reset').textContent = t.reset;

    document.getElementById('kpi-lbl-total').textContent = t.totalCalls;
    document.getElementById('kpi-sub-total').textContent = t.totalSub;
    document.getElementById('kpi-lbl-success').textContent = t.successfulCalls;
    document.getElementById('kpi-sub-success').textContent = t.successSub;
    document.getElementById('kpi-lbl-failed').textContent = t.failedCalls;
    document.getElementById('kpi-sub-failed').textContent = t.failedSub;
    document.getElementById('kpi-lbl-rate').textContent = t.successRate;
    document.getElementById('kpi-sub-rate').textContent = t.rateSub;
    document.getElementById('kpi-lbl-latency').textContent = t.avgLatency;
    document.getElementById('kpi-sub-latency').textContent = t.latencySub;

    document.getElementById('chart-lbl-timeline').textContent = t.timeline;
    document.getElementById('chart-lbl-failures').textContent = t.failureDist;
    document.getElementById('tab-analytics').textContent = t.tabHistory;
    document.getElementById('tab-escalations').textContent = t.tabEscalations;
  }

  function getQueryString() {
    const params = new URLSearchParams();
    const from = document.getElementById('flt-from').value;
    const to = document.getElementById('flt-to').value;
    const channel = document.getElementById('flt-channel').value;
    const language = document.getElementById('flt-language').value;
    const outcome = document.getElementById('flt-outcome').value;

    if (from) params.append('date_from', from);
    if (to) params.append('date_to', to);
    if (channel) params.append('channel', channel);
    if (language) params.append('language', language);
    if (outcome) params.append('outcome', outcome);
    return params.toString();
  }

  function resetFilters() {
    document.getElementById('flt-from').value = '';
    document.getElementById('flt-to').value = '';
    document.getElementById('flt-channel').value = '';
    document.getElementById('flt-language').value = '';
    document.getElementById('flt-outcome').value = '';
    fetchData();
  }

  function switchTab(tab) {
    currentTab = tab;
    document.getElementById('tab-analytics').classList.toggle('active', tab === 'analytics');
    document.getElementById('tab-escalations').classList.toggle('active', tab === 'escalations');
    renderTable();
  }

  async function fetchData() {
    const qs = getQueryString();
    const banner = document.getElementById('banner');
    banner.className = 'banner-msg';
    banner.style.display = 'none';

    try {
      const [sumRes, chartRes, listRes, escRes] = await Promise.all([
        fetch('/api/analytics/summary?' + qs),
        fetch('/api/analytics/charts?' + qs),
        fetch('/api/analytics?' + qs),
        fetch('/api/escalations')
      ]);

      if (!sumRes.ok || !chartRes.ok || !listRes.ok) throw new Error('API failure');

      cachedSummary = await sumRes.json();
      cachedCharts = await chartRes.json();
      cachedAnalytics = await listRes.json();
      cachedEscalations = await escRes.json();

      document.getElementById('updated-at').textContent = 'Last refreshed: ' + new Date().toLocaleTimeString();
      renderAll();
    } catch (err) {
      banner.className = 'banner-msg banner-error';
      banner.textContent = i18n[currentLang].error;
      banner.style.display = 'block';
    }
  }

  function renderAll() {
    renderKPIs();
    renderTimelineChart();
    renderFailureChart();
    renderTable();
  }

  function renderKPIs() {
    document.getElementById('kpi-total').textContent = cachedSummary.total_calls ?? 0;
    document.getElementById('kpi-success').textContent = cachedSummary.successful_calls ?? 0;
    document.getElementById('kpi-failed').textContent = cachedSummary.failed_calls ?? 0;
    document.getElementById('kpi-rate').textContent = (cachedSummary.success_rate ?? 0) + '%';
    document.getElementById('kpi-latency').textContent = cachedSummary.avg_latency_ms ? Math.round(cachedSummary.avg_latency_ms) + ' ms' : 'N/A';
  }

  function renderTimelineChart() {
    const container = document.getElementById('chart-bars');
    const data = cachedCharts.calls_over_time || [];
    if (!data.length) {
      container.innerHTML = '<div style="margin:auto; color:var(--text-muted); font-size:0.8rem;">No timeline data</div>';
      return;
    }
    let max = 0;
    data.forEach(d => { const tot = d.successful + d.failed; if (tot > max) max = tot; });
    if (max === 0) max = 1;

    let html = '';
    data.slice(-7).forEach(d => {
      const succH = Math.round((d.successful / max) * 100);
      const failH = Math.round((d.failed / max) * 100);
      html += `
        <div class="bar-col">
          <div class="bar-wrapper" title="${d.date}: ${d.successful} successful, ${d.failed} failed">
            <div class="bar-failed" style="height:${failH}%"></div>
            <div class="bar-success" style="height:${succH}%"></div>
          </div>
          <div class="bar-date">${d.date.slice(5)}</div>
        </div>
      `;
    });
    container.innerHTML = html;
  }

  function renderFailureChart() {
    const container = document.getElementById('chart-failures-list');
    const data = cachedCharts.failure_distribution || [];
    if (!data.length) {
      container.innerHTML = '<div style="margin:auto; color:var(--text-muted); font-size:0.8rem;">No failure records recorded yet</div>';
      return;
    }
    let totalFail = 0;
    data.forEach(d => totalFail += d.count);
    if (totalFail === 0) totalFail = 1;

    let html = '';
    data.slice(0, 4).forEach(d => {
      const pct = Math.round((d.count / totalFail) * 100);
      html += `
        <div class="dist-item">
          <div class="dist-header">
            <span class="dist-name">${d.type}</span>
            <span class="dist-count">${d.count} (${pct}%)</span>
          </div>
          <div class="dist-bar-bg">
            <div class="dist-bar-fill" style="width:${pct}%; background:var(--danger)"></div>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  }

  function renderTable() {
    const area = document.getElementById('content-area');
    const t = i18n[currentLang];

    if (currentTab === 'escalations') {
      if (!cachedEscalations.length) {
        area.innerHTML = `<div class="empty-state"><div class="empty-icon">✅</div>${t.emptyEscalations}</div>`;
        return;
      }
      let html = `<table><thead><tr>
        <th>Ref ID</th><th>Time</th><th>Caller</th><th>Reason</th><th>Summary</th><th>Urgency</th><th>Status</th>
      </tr></thead><tbody>`;
      cachedEscalations.forEach(r => {
        const dt = r.created_at ? new Date(r.created_at).toLocaleString() : '';
        html += `<tr>
          <td class="call-id">${r.reference_id}</td>
          <td>${dt}</td>
          <td>${r.caller_name || '-'}</td>
          <td>${r.reason || '-'}</td>
          <td>${r.summary || '-'}</td>
          <td><span class="badge badge-reason">${r.urgency || 'normal'}</span></td>
          <td><span class="badge badge-success">${r.status}</span></td>
        </tr>`;
      });
      html += '</tbody></table>';
      area.innerHTML = html;
      return;
    }

    // Analytics Call History Table
    if (!cachedAnalytics.length) {
      area.innerHTML = `<div class="empty-state"><div class="empty-icon">📊</div>${t.emptyHistory}</div>`;
      return;
    }

    let html = `<table><thead><tr>
      <th>${t.thId}</th>
      <th>${t.thTime}</th>
      <th>${t.thChannel}</th>
      <th>${t.thLang}</th>
      <th>${t.thDuration}</th>
      <th>${t.thLatency}</th>
      <th>${t.thOutcome}</th>
      <th>${t.thDetails}</th>
    </tr></thead><tbody>`;

    cachedAnalytics.forEach(r => {
      const dt = r.start_time ? new Date(r.start_time).toLocaleTimeString() : '-';
      const dur = r.duration_seconds ? r.duration_seconds + 's' : '-';
      const lat = r.avg_latency_ms ? Math.round(r.avg_latency_ms) + 'ms' : '-';
      const isSuccess = r.outcome === 'successful';
      const outcomeBadge = isSuccess 
        ? `<span class="badge badge-success">Successful</span>`
        : `<span class="badge badge-failed">Failed</span>`;
      
      const detailText = isSuccess 
        ? (r.financial_outcome || r.success_reason || 'Task completed')
        : (r.failure_type ? `Reason: ${r.failure_type}` : 'Incomplete');

      const escBadge = r.escalation_created ? `<span class="badge badge-escalation" style="margin-left:4px">Escalated</span>` : '';

      html += `<tr>
        <td class="call-id">${r.call_id}</td>
        <td>${dt}</td>
        <td><span class="badge badge-channel">${r.channel || 'browser'}</span></td>
        <td>${r.language || 'English'}</td>
        <td>${dur}</td>
        <td>${lat}</td>
        <td>${outcomeBadge}${escBadge}</td>
        <td>${detailText}</td>
      </tr>`;
    });
    html += '</tbody></table>';
    area.innerHTML = html;
  }

  // Initial Load & Auto-polling every 15 seconds
  fetchData();
  setInterval(fetchData, 15000);
</script>
</body>
</html>"""


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        # Helper to extract string query params
        def param(key: str):
            val = qs.get(key)
            return val[0] if val else None

        if path == "/api/analytics":
            records = db.get_call_analytics(
                date_from=param("date_from"),
                date_to=param("date_to"),
                language=param("language"),
                channel=param("channel"),
                outcome=param("outcome"),
            )
            self._send_json(records)

        elif path == "/api/analytics/summary":
            summary = db.get_analytics_summary(
                date_from=param("date_from"),
                date_to=param("date_to"),
                language=param("language"),
                channel=param("channel"),
            )
            self._send_json(summary)

        elif path == "/api/analytics/charts":
            charts = db.get_analytics_charts(
                date_from=param("date_from"),
                date_to=param("date_to"),
                language=param("language"),
                channel=param("channel"),
            )
            self._send_json(charts)

        elif path == "/api/escalations":
            escalations = db.get_open_escalations()
            self._send_json(escalations)

        elif path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))

        else:
            self.send_error(404)

    def _send_json(self, data: any):
        payload = json.dumps(data, ensure_ascii=False)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload.encode("utf-8"))

    def log_message(self, format, *args):
        # Quieter logging
        print(f"[dashboard] {args[0]}")


if __name__ == "__main__":
    print(f"MoneyBuddy Call Analytics & Escalation Dashboard starting on http://localhost:{DASHBOARD_PORT}")
    server = HTTPServer(("", DASHBOARD_PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
        server.server_close()

