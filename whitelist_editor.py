import http.server
import socketserver
import json
import os
import urllib.parse
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WHITELIST_PATH = os.path.join(BASE_DIR, "process_whitelist.json")

HTML_PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>进程白名单编辑器</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f5f5f5;margin:0;padding:0}
.container{max-width:960px;margin:40px auto;background:#fff;border-radius:4px;box-shadow:0 2px 6px rgba(0,0,0,0.1);padding:20px 24px}
h1{margin-top:0;font-size:20px;color:#333}
textarea{width:100%;height:480px;font-family:monospace;font-size:13px;border:1px solid #ccc;border-radius:3px;padding:8px;box-sizing:border-box}
.toolbar{margin:12px 0;display:flex;gap:8px}
button{padding:6px 14px;border-radius:3px;border:1px solid #007bff;background:#007bff;color:#fff;cursor:pointer;font-size:13px}
button.secondary{border-color:#6c757d;background:#6c757d}
.status{margin-top:8px;font-size:13px;color:#555}
</style>
</head>
<body>
<div class="container">
<h1>进程白名单 JSON 编辑器</h1>
<p>根据发行版 ID 维护系统默认进程白名单，例如: <code>ubuntu</code>、<code>centos</code>、<code>alpine</code> 等。</p>
<div class="toolbar">
<button onclick="loadData()" class="secondary">重新加载</button>
<button onclick="saveData()">保存</button>
</div>
<textarea id="data"></textarea>
<div class="status" id="status"></div>
</div>
<script>
async function loadData(){try{const r=await fetch("/data");if(!r.ok){throw new Error("HTTP "+r.status);}const t=await r.text();document.getElementById("data").value=t;setStatus("已加载白名单文件","ok");}catch(e){setStatus("加载失败: "+e.message,"err");}}
async function saveData(){const ta=document.getElementById("data");const v=ta.value;try{JSON.parse(v);}catch(e){setStatus("JSON 无效: "+e.message,"err");alert("JSON 无效: "+e.message);return;}try{const body=new URLSearchParams();body.append("data",v);const r=await fetch("/save",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body});const text=await r.text();if(r.ok){setStatus(text,"ok");}else{setStatus("保存失败: "+text,"err");}}catch(e){setStatus("保存请求失败: "+e.message,"err");}}
function setStatus(msg,kind){const el=document.getElementById("status");el.textContent=msg;if(kind==="ok"){el.style.color="#155724";}else if(kind==="err"){el.style.color="#721c24";}else{el.style.color="#555";}}
document.addEventListener("DOMContentLoaded",loadData);
</script>
</body>
</html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path.startswith("/data"):
            self.handle_data_get()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith("/save"):
            self.handle_save()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_data_get(self):
        try:
            if os.path.exists(WHITELIST_PATH):
                with open(WHITELIST_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = "{}"
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(("读取文件失败: " + str(e)).encode("utf-8"))
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def handle_save(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        params = urllib.parse.parse_qs(body)
        data_text_list = params.get("data")
        if not data_text_list:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("缺少 data 字段".encode("utf-8"))
            return
        data_text = data_text_list[0]
        try:
            parsed = json.loads(data_text)
        except Exception as e:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(("JSON 无效: " + str(e)).encode("utf-8"))
            return
        try:
            with open(WHITELIST_PATH, "w", encoding="utf-8") as f:
                json.dump(parsed, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(("写入文件失败: " + str(e)).encode("utf-8"))
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("保存成功".encode("utf-8"))


def run_server(port=8000):
    with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
        url = f"http://127.0.0.1:{port}/"
        print("在浏览器中打开:", url)
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    run_server()
