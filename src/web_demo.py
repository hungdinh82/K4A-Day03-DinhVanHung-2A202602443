"""Giao diện web cục bộ để demo Recruitment AI Agent."""

import json
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import run_react_agent, save_waterfall_trace
from mcp_server import MCPAcademicServer
from providers import get_llm_provider


load_dotenv()
HOST = "127.0.0.1"
PORT = 8000

PAGE = """<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Recruitment AI Agent Demo</title>
  <style>
    :root { --ink:#172033; --muted:#60708b; --line:#dce3ee; --bg:#f4f7fb; --accent:#4456d9; --tool:#ed7d31; --ok:#178060; }
    * { box-sizing:border-box } body { margin:0; background:var(--bg); color:var(--ink); font-family:Inter,system-ui,-apple-system,sans-serif }
    header { background:linear-gradient(120deg,#182857,#4358d6); color:#fff; padding:30px max(24px,calc((100vw - 1120px)/2)); }
    h1 { margin:0; font-size:clamp(24px,4vw,36px) } header p { margin:8px 0 0; opacity:.88 }
    main { max-width:1120px; margin:28px auto; padding:0 20px; display:grid; grid-template-columns:1.05fr .95fr; gap:20px }
    .card { background:#fff; border:1px solid var(--line); border-radius:16px; padding:22px; box-shadow:0 5px 18px #20305d0d }
    h2 { font-size:18px; margin:0 0 14px } label { display:block; font-weight:700; margin-bottom:8px }
    textarea { width:100%; min-height:185px; border:1px solid #cbd5e1; border-radius:11px; padding:13px; font:inherit; resize:vertical; color:var(--ink) }
    textarea:focus { outline:3px solid #dfe4ff; border-color:var(--accent) } button { border:0; border-radius:10px; padding:11px 15px; font:600 14px inherit; cursor:pointer }
    #send { margin-top:12px; width:100%; color:#fff; background:var(--accent) } #send:disabled { opacity:.6; cursor:wait }
    .samples { display:flex; flex-wrap:wrap; gap:8px; margin-top:13px }.sample { color:#3646b5; background:#eef0ff; padding:8px 10px }
    #answer { white-space:pre-wrap; line-height:1.55; background:#f7f9fc; border-left:4px solid var(--ok); border-radius:6px; padding:13px; min-height:74px }
    .empty { color:var(--muted) }.step { border-left:3px solid var(--accent); padding:0 0 16px 14px; margin-left:4px }.step.tool { border-color:var(--tool) }.step.final { border-color:var(--ok) }
    .badge { display:inline-block; border-radius:99px; padding:3px 8px; font-size:12px; font-weight:700; background:#eef0ff; color:#3646b5 }.tool .badge { background:#fff0e7; color:#bd5d18 }.final .badge { background:#e6f6ef; color:#117054 }
    .step p { margin:8px 0 0; white-space:pre-wrap; line-height:1.45 }.meta { color:var(--muted); font-size:13px; margin-top:5px } footer { text-align:center; color:var(--muted); padding:0 20px 28px; font-size:13px }
    @media (max-width:800px) { main { grid-template-columns:1fr; margin-top:18px } }
  </style>
</head>
<body>
  <header><h1>💼 Recruitment AI Agent</h1><p>Demo sàng lọc CV và gửi lịch phỏng vấn qua MCP Tool Calling</p></header>
  <main>
    <section class="card"><h2>Nhập yêu cầu tuyển dụng</h2>
      <label for="query">Câu hỏi / thông tin ứng viên</label>
      <textarea id="query" placeholder="Ví dụ: Hãy tra cứu tiêu chí tuyển dụng cho vị trí Data Analyst."></textarea>
      <button id="send">Gửi tới Agent</button>
      <div class="samples">
        <button class="sample" data-q="Hãy tra cứu tiêu chí tuyển dụng cho vị trí Data Analyst.">Tra cứu Data Analyst</button>
        <button class="sample" data-q="Ứng viên: Nguyễn Minh Anh, email minh.anh@example.com, ứng tuyển Data Analyst. CV có 2 năm kinh nghiệm phân tích dữ liệu, tốt nghiệp đại học chuyên ngành phù hợp và có SQL, Python, Power BI. Hãy sàng lọc và gửi lịch phỏng vấn lúc 14:00 15/09/2026. Người phỏng vấn: Trần Quốc B.">Sàng lọc & mời phỏng vấn</button>
      </div>
    </section>
    <section class="card"><h2>Trả lời cuối cùng</h2><div id="answer" class="empty">Kết quả sẽ xuất hiện ở đây.</div></section>
    <section class="card" style="grid-column:1/-1"><h2>Waterfall Trace — ReAct Loop</h2><div id="trace" class="empty">Chưa có lượt chạy.</div></section>
  </main>
  <footer>Chạy cục bộ · API key chỉ nằm trong file .env trên máy của bạn</footer>
  <script>
    const query = document.querySelector('#query'), send = document.querySelector('#send'), answer = document.querySelector('#answer'), trace = document.querySelector('#trace');
    document.querySelectorAll('.sample').forEach(button => button.onclick = () => { query.value = button.dataset.q; query.focus(); });
    const esc = value => String(value ?? '').replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
    function drawTrace(items) {
      trace.classList.remove('empty'); trace.innerHTML = items.map(item => {
        const isTool = item.action_type === 'TOOL_EXECUTION', isFinal = item.action_type === 'FINAL_ANSWER';
        const content = isTool ? `Tool: ${item.tool_name}\\nArguments: ${JSON.stringify(item.arguments)}\\nObservation: ${JSON.stringify(item.observation)}` : item.output;
        return `<article class="step ${isTool ? 'tool' : ''} ${isFinal ? 'final' : ''}"><span class="badge">Bước ${item.step} · ${isTool ? 'TOOL' : 'FINAL'}</span><div class="meta">${esc(item.latency_ms)} ms · ${esc(item.thought)}</div><p>${esc(content)}</p></article>`;
      }).join('');
    }
    async function ask() {
      const text = query.value.trim(); if (!text) { query.focus(); return; }
      send.disabled = true; send.textContent = 'Agent đang suy luận…'; answer.textContent = 'Đang gọi Agent…'; answer.classList.add('empty'); trace.textContent = 'Đang tạo Waterfall Trace…'; trace.classList.add('empty');
      try {
        const response = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({query:text})});
        const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Không thể gọi Agent.');
        const final = data.trace.findLast(item => item.action_type === 'FINAL_ANSWER');
        answer.textContent = final ? final.output : 'Agent chưa có câu trả lời cuối cùng.'; answer.classList.remove('empty'); drawTrace(data.trace);
      } catch (error) { answer.textContent = `Lỗi: ${error.message}`; answer.classList.remove('empty'); trace.textContent = 'Lượt chạy chưa tạo được trace.'; }
      finally { send.disabled = false; send.textContent = 'Gửi tới Agent'; }
    }
    send.onclick = ask; query.addEventListener('keydown', event => { if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') ask(); });
  </script>
</body></html>"""


class DemoHandler(BaseHTTPRequestHandler):
    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()

    def _json(self, status, payload):
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.path != "/":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content = PAGE.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            query = body.get("query", "").strip()
            if not query:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "Hãy nhập câu hỏi trước khi gửi."})
                return
            trace = run_react_agent(query, self.provider, self.mcp_server)
            save_waterfall_trace(trace)
            self._json(HTTPStatus.OK, {"trace": trace})
        except Exception as error:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Agent không thể xử lý yêu cầu: {error}"})

    def log_message(self, format, *args):
        print(f"[Web demo] {format % args}")


if __name__ == "__main__":
    print(f"💼 Recruitment AI Agent UI: http://{HOST}:{PORT}")
    print("Nhấn Ctrl+C để dừng máy chủ.")
    ThreadingHTTPServer((HOST, PORT), DemoHandler).serve_forever()
