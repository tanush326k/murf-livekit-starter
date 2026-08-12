"""
Day 7: Human Escalation Dashboard
A lightweight standalone server to view open escalation requests.
Run: python src/dashboard.py
Open: http://localhost:8890
"""

import json
import os
import sys
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
<title>MoneyBuddy — Escalation Dashboard</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: #0a0f1e;
    color: #e2e8f0;
    min-height: 100vh;
    padding: 2rem;
  }
  header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 2rem;
  }
  header .dot {
    width: 10px; height: 10px;
    background: #10b981;
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }
  h1 { font-size: 1.5rem; font-weight: 700; }
  h1 span { color: #10b981; }
  .subtitle { color: #64748b; font-size: 0.85rem; margin-top: 0.25rem; }
  .stats {
    display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;
  }
  .stat-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    min-width: 160px;
  }
  .stat-card .label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
  .stat-card .value { font-size: 1.75rem; font-weight: 700; color: #10b981; margin-top: 0.25rem; }
  table {
    width: 100%;
    border-collapse: collapse;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    overflow: hidden;
  }
  thead { background: rgba(255,255,255,0.04); }
  th {
    text-align: left;
    padding: 0.75rem 1rem;
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }
  td {
    padding: 0.85rem 1rem;
    font-size: 0.875rem;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    vertical-align: top;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover { background: rgba(255,255,255,0.03); }
  .ref-id { font-family: monospace; color: #10b981; font-weight: 600; }
  .badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .badge-open { background: rgba(16,185,129,0.15); color: #10b981; }
  .badge-progress { background: rgba(59,130,246,0.15); color: #3b82f6; }
  .badge-resolved { background: rgba(100,116,139,0.15); color: #94a3b8; }
  .badge-emergency { background: rgba(147,51,234,0.15); color: #a855f7; }
  .badge-high { background: rgba(239,68,68,0.15); color: #ef4444; }
  .badge-medium { background: rgba(245,158,11,0.15); color: #f59e0b; }
  .badge-low { background: rgba(59,130,246,0.15); color: #3b82f6; }
  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #475569;
  }
  .empty-state .icon { font-size: 3rem; margin-bottom: 1rem; }
  .last-updated { color: #475569; font-size: 0.75rem; margin-top: 1rem; text-align: right; }
</style>
</head>
<body>
  <header>
    <div class="dot"></div>
    <div>
      <h1>Money<span>Buddy</span> Escalation Dashboard</h1>
      <div class="subtitle">Human-help requests from the voice agent</div>
    </div>
  </header>

  <div class="stats" id="stats"></div>
  <div id="content"></div>
  <div class="last-updated" id="updated"></div>

  <script>
    async function load() {
      try {
        const res = await fetch('/api/escalations');
        const data = await res.json();
        renderStats(data);
        renderTable(data);
        document.getElementById('updated').textContent =
          'Last refreshed: ' + new Date().toLocaleTimeString();
      } catch (e) {
        document.getElementById('content').innerHTML =
          '<div class="empty-state"><div class="icon">⚠️</div>Failed to load escalations.</div>';
      }
    }

    function renderStats(data) {
      const open = data.filter(d => d.status === 'open').length;
      const high = data.filter(d => ['high', 'emergency'].includes((d.urgency || '').toLowerCase())).length;
      document.getElementById('stats').innerHTML = `
        <div class="stat-card"><div class="label">Total Requests</div><div class="value">${data.length}</div></div>
        <div class="stat-card"><div class="label">Open</div><div class="value">${open}</div></div>
        <div class="stat-card"><div class="label">High/Emergency</div><div class="value" style="color:#ef4444">${high}</div></div>
      `;
    }

    function urgencyBadge(u) {
      const l = (u || 'unknown').toLowerCase();
      const cls = l === 'emergency' ? 'badge-emergency' : l === 'high' ? 'badge-high' : l === 'medium' ? 'badge-medium' : 'badge-low';
      return '<span class="badge ' + cls + '">' + u + '</span>';
    }

    function statusBadge(s) {
      const l = (s || 'open').toLowerCase().replace(' ', '_');
      const cls = l === 'in_progress' ? 'badge-progress' : l === 'resolved' ? 'badge-resolved' : 'badge-open';
      return '<span class="badge ' + cls + '">' + s + '</span>';
    }

    function renderTable(data) {
      if (!data.length) {
        document.getElementById('content').innerHTML =
          '<div class="empty-state"><div class="icon">✅</div>No escalation requests yet. All clear!</div>';
        return;
      }
      let html = `<table>
        <thead><tr>
          <th>Reference ID</th><th>Date/Time</th><th>Caller</th><th>Reason</th>
          <th>Summary</th><th>Urgency</th><th>Language</th><th>Follow-up</th><th>Status</th>
        </tr></thead><tbody>`;
      for (const row of data) {
        const dt = row.created_at ? new Date(row.created_at).toLocaleString() : '';
        html += `<tr>
          <td class="ref-id">${row.reference_id}</td>
          <td>${dt}</td>
          <td>${row.caller_name || '-'}</td>
          <td>${row.reason || '-'}</td>
          <td>${row.summary || '-'}</td>
          <td>${urgencyBadge(row.urgency || 'Unknown')}</td>
          <td>${row.language || '-'}</td>
          <td>${row.preferred_followup || '-'}</td>
          <td>${statusBadge(row.status)}</td>
        </tr>`;
      }
      html += '</tbody></table>';
      document.getElementById('content').innerHTML = html;
    }

    load();
    setInterval(load, 30000);
  </script>
</body>
</html>"""


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/escalations":
            escalations = db.get_open_escalations()
            payload = json.dumps(escalations, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload.encode("utf-8"))
        elif self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        # Quieter logging
        print(f"[dashboard] {args[0]}")


if __name__ == "__main__":
    print(f"MoneyBuddy Escalation Dashboard starting on http://localhost:{DASHBOARD_PORT}")
    server = HTTPServer(("", DASHBOARD_PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
        server.server_close()
