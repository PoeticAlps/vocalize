"""FastAPI web server — single-file app with embedded HTML frontend."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from vocalize.output import FORMATTERS
from vocalize.pipeline import run_pipeline
from vocalize.types import TranscriptionResult

app = FastAPI(title="Vocalize Web")

# ── in-memory job store ─────────────────────────────────────────────
jobs: dict[str, dict] = {}
_JOB_TTL = 3600  # keep completed jobs for 1 hour


def _start_gc() -> None:
    """Start background thread that purges expired jobs."""
    def _cleanup() -> None:
        while True:
            time.sleep(300)
            cutoff = time.time() - _JOB_TTL
            expired = [jid for jid, j in jobs.items() if j.get("_ts", 0) < cutoff]
            for jid in expired:
                del jobs[jid]

    t = threading.Thread(target=_cleanup, daemon=True)
    t.start()


class TranscribeRequest(BaseModel):
    job_id: str
    model_size: str = "base"
    language: str | None = None
    fmt: str = "txt"


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_CONTENT


@app.post("/api/transcribe")
def transcribe(file: UploadFile = File(...), req: str = Form(...)):
    body = TranscribeRequest(**json.loads(req))
    job_id = body.job_id

    jobs[job_id] = {"status": "uploading", "error": None, "result": None, "_ts": time.time()}

    suffix = Path(file.filename or "upload.mp4").suffix
    tmp = Path(tempfile.gettempdir()) / f"vocalize_{job_id}{suffix}"
    tmp.write_bytes(file.file.read())

    try:
        jobs[job_id]["status"] = "processing"
        result: TranscriptionResult = run_pipeline(
            tmp,
            model_size=body.model_size,
            language=body.language or None,
            fmt=body.fmt,
            output=None,
        )
        formatter = FORMATTERS.get(body.fmt, FORMATTERS["txt"])
        text_output = formatter(result)

        jobs[job_id].update(
            status="done",
            _ts=time.time(),
            result={
                "text": text_output,
                "meta": {
                    "language": result.language,
                    "duration": result.duration,
                    "segments": len(result.segments),
                    "fmt": body.fmt,
                    "filename": file.filename or "video",
                },
            },
        )
    except Exception as exc:
        jobs[job_id].update(status="error", _ts=time.time(), error=str(exc))
    finally:
        tmp.unlink(missing_ok=True)

    return JSONResponse({"job_id": job_id})


@app.get("/api/status/{job_id}")
async def status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "job not found")
    return JSONResponse(jobs[job_id])


def launch(port: int = 8080) -> None:
    import uvicorn

    _start_gc()
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


# ── embedded frontend ────────────────────────────────────────────────
HTML_CONTENT = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vocalize — 视频转文字</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh; color: #e0e0e0; padding: 20px;
  }
  .container { max-width: 720px; margin: 0 auto; }
  h1 { text-align: center; font-size: 2rem; margin-bottom: 4px;
       background: linear-gradient(90deg, #00dbde, #fc00ff);
       -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .subtitle { text-align: center; color: #888; margin-bottom: 30px; font-size: 0.9rem; }

  .card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px; padding: 24px; margin-bottom: 16px;
    backdrop-filter: blur(10px);
  }

  .drop-zone {
    border: 2px dashed rgba(255,255,255,0.2);
    border-radius: 12px; padding: 40px 20px; text-align: center;
    cursor: pointer; transition: all 0.3s;
    color: #aaa;
  }
  .drop-zone:hover, .drop-zone.dragover {
    border-color: #00dbde; background: rgba(0,219,222,0.08); color: #fff;
  }
  .drop-zone .icon { font-size: 3rem; margin-bottom: 8px; }
  .drop-zone .name { color: #00dbde; margin-top: 8px; font-weight: 500; }

  .settings { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-top: 16px; }
  .field label { display: block; font-size: 0.75rem; color: #888; margin-bottom: 4px; }
  select, button {
    width: 100%; padding: 10px 14px; border-radius: 8px; border: none;
    font-size: 0.95rem; cursor: pointer;
  }
  select { background: rgba(255,255,255,0.1); color: #fff; }
  select option { background: #1a1a2e; color: #fff; }
  button.primary {
    background: linear-gradient(90deg, #00dbde, #fc00ff);
    color: #fff; font-weight: 600; font-size: 1rem; margin-top: 16px;
  }
  button.primary:hover { opacity: 0.9; }
  button.primary:disabled { opacity: 0.4; cursor: not-allowed; }

  .status { text-align: center; margin-top: 16px; min-height: 24px; }
  .status.error { color: #ff6b6b; }
  .status.success { color: #51cf66; }

  .progress-bar {
    width: 100%; height: 8px; background: rgba(255,255,255,0.1);
    border-radius: 4px; margin-top: 12px; overflow: hidden; display: none;
  }
  .progress-bar.active { display: block; }
  .progress-fill {
    height: 100%; width: 0%;
    background: linear-gradient(90deg, #00dbde, #fc00ff);
    transition: width 0.5s ease; border-radius: 4px;
  }

  .result-tabs { display: flex; gap: 4px; margin-bottom: 0; }
  .result-tabs button {
    flex: 1; padding: 8px; font-size: 0.85rem;
    background: rgba(255,255,255,0.05); color: #888;
    border-radius: 8px 8px 0 0;
  }
  .result-tabs button.active { background: rgba(255,255,255,0.12); color: #fff; }
  .result-box {
    background: rgba(0,0,0,0.3); border-radius: 0 8px 8px 8px;
    padding: 16px; min-height: 200px; white-space: pre-wrap;
    font-family: "SF Mono", "Cascadia Code", monospace; font-size: 0.9rem;
    line-height: 1.6; overflow-y: auto; max-height: 400px;
  }
  .result-box .meta { color: #888; font-size: 0.8rem; margin-bottom: 12px; }
  .download-btn {
    display: inline-block; margin-top: 12px; padding: 8px 20px;
    background: rgba(0,219,222,0.15); color: #00dbde;
    border: 1px solid rgba(0,219,222,0.3); border-radius: 8px;
    text-decoration: none; font-size: 0.85rem; cursor: pointer;
  }
  .download-btn:hover { background: rgba(0,219,222,0.25); }

  .hidden { display: none !important; }
  input[type="file"] { display: none; }
</style>
</head>
<body>
<div class="container">
  <h1>🎙️ Vocalize</h1>
  <p class="subtitle">视频转文字 — 拖入文件，一键提取语音</p>

  <div class="card">
    <div class="drop-zone" id="dropZone">
      <div class="icon">📁</div>
      <div>拖入视频文件，或点击选择</div>
      <div style="font-size:0.8rem;margin-top:4px;">支持 MP4, AVI, MKV, MOV, WMV, FLV, WebM, MP3, WAV</div>
      <div class="name hidden" id="fileName"></div>
    </div>
    <input type="file" id="fileInput" accept="video/*,audio/*">

    <div class="settings">
      <div class="field">
        <label>Whisper 模型</label>
        <select id="model">
          <option value="tiny">tiny (最快)</option>
          <option value="base" selected>base (推荐)</option>
          <option value="small">small</option>
          <option value="medium">medium</option>
          <option value="large-v3">large-v3 (最准)</option>
        </select>
      </div>
      <div class="field">
        <label>语言</label>
        <select id="language">
          <option value="">自动检测</option>
          <option value="zh">中文</option>
          <option value="en">英语</option>
          <option value="ja">日语</option>
          <option value="ko">韩语</option>
          <option value="fr">法语</option>
          <option value="de">德语</option>
          <option value="es">西班牙语</option>
        </select>
      </div>
      <div class="field">
        <label>输出格式</label>
        <select id="format">
          <option value="txt">纯文本</option>
          <option value="srt">字幕 SRT</option>
          <option value="json">JSON</option>
        </select>
      </div>
    </div>

    <button class="primary" id="runBtn" disabled>🚀 开始转写</button>

    <div class="progress-bar" id="progressBar">
      <div class="progress-fill" id="progressFill"></div>
    </div>

    <div class="status" id="status"></div>
  </div>

  <div class="card hidden" id="resultCard">
    <div class="result-tabs">
      <button class="active" data-tab="text">📄 文本</button>
      <button data-tab="download">📥 下载</button>
    </div>
    <div class="result-box" id="resultBox"></div>
    <div id="downloadArea"></div>
  </div>
</div>

<script>
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const runBtn = document.getElementById('runBtn');
const statusEl = document.getElementById('status');
const progressBar = document.getElementById('progressBar');
const progressFill = document.getElementById('progressFill');
const resultCard = document.getElementById('resultCard');
const resultBox = document.getElementById('resultBox');
const downloadArea = document.getElementById('downloadArea');

let selectedFile = null;

dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => pickFile(e.target.files[0]));

dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
  e.preventDefault(); dropZone.classList.remove('dragover');
  if (e.dataTransfer.files[0]) pickFile(e.dataTransfer.files[0]);
});

function pickFile(file) {
  selectedFile = file;
  fileName.textContent = file.name;
  fileName.classList.remove('hidden');
  runBtn.disabled = false;
  statusEl.textContent = '';
  statusEl.className = 'status';
  resultCard.classList.add('hidden');
}

runBtn.addEventListener('click', async () => {
  if (!selectedFile) return;
  const jobId = crypto.randomUUID();
  const formData = new FormData();
  formData.append('file', selectedFile);
  formData.append('req', JSON.stringify({
    job_id: jobId,
    model_size: document.getElementById('model').value,
    language: document.getElementById('language').value || null,
    fmt: document.getElementById('format').value,
  }));

  runBtn.disabled = true;
  progressBar.classList.add('active');
  statusEl.textContent = '⏳ 上传中…';
  progressFill.style.width = '10%';

  try {
    const resp = await fetch('/api/transcribe', { method: 'POST', body: formData });
    if (!resp.ok) throw new Error(await resp.text());
    statusEl.textContent = '🔊 提取音频…';
    progressFill.style.width = '30%';

    await pollStatus(jobId);
  } catch (err) {
    statusEl.textContent = '❌ ' + err.message;
    statusEl.className = 'status error';
    runBtn.disabled = false;
    progressBar.classList.remove('active');
  }
});

async function pollStatus(jobId) {
  const steps = [
    { at: 0.3, text: '🔊 提取音频…' },
    { at: 0.5, text: '🧠 加载模型…' },
    { at: 0.7, text: '📝 转写中…' },
  ];
  let stepIdx = 0;

  while (true) {
    await new Promise(r => setTimeout(r, 1500));
    const resp = await fetch(`/api/status/${jobId}`);
    const data = await resp.json();

    if (stepIdx < steps.length && data.status !== 'processing') {
      progressFill.style.width = (steps[stepIdx].at * 100) + '%';
      statusEl.textContent = steps[stepIdx].text;
      stepIdx++;
    }

    if (data.status === 'done') {
      progressFill.style.width = '100%';
      statusEl.textContent = '✅ 完成!';
      statusEl.className = 'status success';
      showResult(data.result);
      runBtn.disabled = false;
      progressBar.classList.remove('active');
      return;
    }
    if (data.status === 'error') {
      progressBar.classList.remove('active');
      statusEl.textContent = '❌ ' + data.error;
      statusEl.className = 'status error';
      runBtn.disabled = false;
      return;
    }
    // Update progress bar if processing
    if (data.status === 'processing' && stepIdx < steps.length) {
      progressFill.style.width = (steps[stepIdx].at * 100) + '%';
      statusEl.textContent = steps[stepIdx].text;
      stepIdx++;
    }
  }
}

function showResult(result) {
  resultCard.classList.remove('hidden');
  const fmt = result.meta.fmt;
  const extMap = { txt: 'txt', srt: 'srt', json: 'json' };

  resultBox.innerHTML = `<div class="meta">
    🌐 语言: ${result.meta.language} &nbsp;|&nbsp;
    ⏱️ 时长: ${result.meta.duration.toFixed(1)}s &nbsp;|&nbsp;
    📑 分段: ${result.meta.segments}
  </div>` + escapeHtml(result.text);

  downloadArea.innerHTML = '';
  const blob = new Blob([result.text], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const baseName = (result.meta.filename || 'video').replace(/\.[^.]+$/, '');
  a.href = url;
  a.download = baseName + '.' + extMap[fmt];
  a.className = 'download-btn';
  a.textContent = '⬇️ 下载 ' + baseName + '.' + extMap[fmt];
  a.addEventListener('click', () => URL.revokeObjectURL(url));
  downloadArea.appendChild(a);
}

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// Tab switching
document.querySelectorAll('.result-tabs button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.result-tabs button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const tab = btn.dataset.tab;
    if (tab === 'text') {
      resultBox.classList.remove('hidden');
      downloadArea.classList.add('hidden');
    } else {
      resultBox.classList.add('hidden');
      downloadArea.classList.remove('hidden');
    }
  });
});
downloadArea.classList.add('hidden');
</script>
</body>
</html>
"""
