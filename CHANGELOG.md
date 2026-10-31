# Changelog

## 0.2.0 (2026-10-31)

修复与体验升级，本版本起可在 Mac 上开箱即用：

- **修复**：移除 `torch` 硬依赖（原代码直接 `import torch` 但未声明，干净环境装完即 ImportError）；改用 `ctranslate2.get_cuda_device_count()` 探测 GPU
- **修复**：macOS 不再返回不支持的 `mps` 设备（CTranslate2 仅支持 cpu/cuda），设备自动判定 cuda→float16 / cpu→int8
- **Web 面板**：转写任务异步化——上传后立即入队返回，轮询真实进度（提取音频→转写→完成），不再超时假死
- **Web 面板**：模型按 (size, device, compute_type) 缓存复用，多次上传不再重复加载模型（Web 场景最大卡顿源）
- **依赖**：移除声明但未使用的 `ffmpeg-python`（实际直接调用 ffmpeg 二进制，需自行安装：`brew install ffmpeg`）
- CLI `-d` 参数移除 `mps` 选项

## 0.1.0

首版：CLI 转写（TXT/SRT/VTT/JSON）+ FastAPI Web 面板。
