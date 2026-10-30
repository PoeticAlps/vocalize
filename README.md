# vocalize

Extract speech from videos — fast, local transcription powered by [faster-whisper](https://github.com/Systran/faster-whisper).

## Quick Start

```bash
# 从仓库根目录本地安装(CLI)
pip install -e .

# Transcribe a video
vocalize my_video.mp4

# With options
vocalize my_video.mp4 -m small -l zh -f srt -o subtitles.srt
```

> 前置条件:系统需装有 [ffmpeg](https://ffmpeg.org/) 并在 PATH 中(macOS: `brew install ffmpeg`)。
> pip 不会自动安装 ffmpeg。

## Web Panel (新手友好 🎨)

```bash
# Install with web UI support
pip install -e ".[web]"

# Launch panel
vocalize-web
```

Then 打开浏览器访问 `http://localhost:8080`，拖入视频、选模型、点按钮即可。

Web 模式流程:上传文件后任务立即进入队列(服务端在后台线程转写，不会阻塞请求)→ 页面轮询显示**真实进度百分比**(提取音频 → 按 segment 迭代的转写进度)→ 完成后在线预览并下载 txt / srt / json。模型只加载一次(按 model_size 缓存)，重复上传不再重新加载。

## Features

| Feature | Detail |
|---------|--------|
| **Local-only** | No cloud API, your media never leaves your machine |
| **Fast** | faster-whisper + CTranslate2 is 4x faster than stock Whisper |
| **3 output formats** | `.txt` (plain text), `.srt` (subtitles), `.json` (structured) |
| **Multi-language** | Auto-detect or force a language code (`zh`, `en`, `ja`, …) |
| **GPU support** | CUDA GPU 或纯 CPU(CTranslate2 不支持 Apple MPS，macOS 上自动用 CPU int8) |
| **No PyTorch** | 只依赖 faster-whisper/CTranslate2，不需要安装 PyTorch |

## CLI Options

```
vocalize <video> [-m MODEL] [-l LANG] [-d DEVICE] [-f FMT] [-o OUTPUT]

  -m, --model     tiny / base / small / medium / large-v3  (default: base)
  -l, --language  ISO-639-1 code (auto-detect if omitted)
  -d, --device    cpu / cuda (auto-detected if omitted)
  -f, --format    txt / srt / json  (default: txt)
  -o, --output    output file path
```

## Output Formats

**TXT** — clean plain text, one segment per line
```
大家好，欢迎观看这个视频。
今天我们来聊聊人工智能。
```

**SRT** — standard subtitle format with timestamps
```
1
00:00:00,000 --> 00:00:03,500
大家好，欢迎观看这个视频。
```

**JSON** — full structured data
```json
{
  "source": "video.mp4",
  "language": "zh",
  "model_size": "base",
  "duration_seconds": 7.2,
  "segments": [...]
}
```

## Python API

```python
from vocalize import run_pipeline

result = run_pipeline(
    "video.mp4",
    model_size="small",
    language="zh",
    fmt="srt",
    output="out.srt",
)
print(result.full_text)
```

## Requirements

- Python ≥ 3.9
- ffmpeg（需自行安装，pip 不会装系统依赖）
- faster-whisper（含 CTranslate2，随 `pip install` 自动安装；无需 PyTorch）

### Web Panel additionally requires

- fastapi, uvicorn, python-multipart（`pip install -e ".[web]"`）

## License

MIT
