# vocalize

Extract speech from videos — fast, local transcription powered by [faster-whisper](https://github.com/Systran/faster-whisper).

## Quick Start

```bash
# Install core (CLI)
pip install vocalize

# Transcribe a video
vocalize my_video.mp4

# With options
vocalize my_video.mp4 -m small -l zh -f srt -o subtitles.srt
```

## Web Panel (新手友好 🎨)

```bash
# Install with web UI support
pip install vocalize[web]

# Launch panel
vocalize-web
```

Then 打开浏览器访问 `http://localhost:8080`，拖入视频、选模型、点按钮即可。

## Features

| Feature | Detail |
|---------|--------|
| **Local-only** | No cloud API, your media never leaves your machine |
| **Fast** | faster-whisper + CTranslate2 is 4x faster than stock Whisper |
| **3 output formats** | `.txt` (plain text), `.srt` (subtitles), `.json` (structured) |
| **Multi-language** | Auto-detect or force a language code (`zh`, `en`, `ja`, …) |
| **GPU support** | CUDA, MPS (Apple Silicon), or pure CPU |

## CLI Options

```
vocalize <video> [-m MODEL] [-l LANG] [-d DEVICE] [-f FMT] [-o OUTPUT]

  -m, --model     tiny / base / small / medium / large-v3  (default: base)
  -l, --language  ISO-639-1 code (auto-detect if omitted)
  -d, --device    cpu / cuda / mps (auto-detected if omitted)
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
- ffmpeg
- faster-whisper + PyTorch (installed automatically via pip)

### Web Panel additionally requires

- fastapi, uvicorn, python-multipart (`pip install vocalize[web]`)

## License

MIT
