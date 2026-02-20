# OptiScam — Video Scam Detection System

A multi-modal video analysis pipeline for detecting scams in short-form videos.
Combines CLAHE image enhancement, dual OCR (RapidOCR + TrOCR), Whisper audio transcription,
and Qwen3-VL-2B vision-language model inference with 4-bit quantization.

---

## Software Requirements

| Tool / Library | Min Version | Purpose |
|---|---|---|
| Python | 3.10 | Runtime |
| CUDA Toolkit | 12.1 | GPU acceleration |
| PyTorch | 2.0.0 | Deep learning backend |
| torchvision | 0.15.0 | Vision transforms |
| Transformers (HuggingFace) | 4.50.0 | Model loading & inference |
| Accelerate (HuggingFace) | 0.25.0 | `device_map="auto"` support |
| BitsAndBytes | 0.43.0 | 4-bit model quantization |
| SentencePiece | 0.1.99 | TrOCR tokenizer |
| qwen-vl-utils | 0.0.8 | Qwen vision input processing |
| OpenCV | 4.8.0 | Frame extraction & CLAHE |
| Pillow | 10.0.0 | Image I/O |
| NumPy | 1.24.0 | Array operations |
| RapidOCR (ONNX) | 1.3.0 | Primary OCR engine |
| OpenAI Whisper | 20231117 | Audio transcription |
| FFmpeg | 6.0 *(system binary)* | Audio extraction from video |

---

## Architecture

```
Video Input
    │
    ▼
┌─────────────────────────────────────────┐
│  ImageProcessing                        │
│  · Extract frames at interval           │
│  · CLAHE enhancement (LAB color space)  │
│  · Laplacian variance sharpness filter  │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  TextExtractor                          │
│  · RapidOCR  (primary, fast)            │
│  · TrOCR     (fallback, low-confidence) │
│  · Timestamp-indexed detection list     │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  AudioTranscriber (Whisper)             │
│  · FFmpeg audio extraction              │
│  · Word-level timestamps                │
│  · Multi-language auto-detect           │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Qwen3VLModel                           │
│  · 4-bit quantized (BNB)                │
│  · Context-aware frame analysis         │
│  · Holistic video analysis mode         │
└─────────────────────────────────────────┘
    │
    ▼
JSON report + human-readable summary
```

See [CLASS_DIAGRAM.md](CLASS_DIAGRAM.md) for the full class diagram.

---

## Requirements

- Python 3.10–3.14
- NVIDIA GPU with 6 GB+ VRAM (strongly recommended — CPU inference is impractically slow)
- CUDA Toolkit 12.x
- FFmpeg installed as a system binary

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/OptiScam_Qwen3.git
cd OptiScam_Qwen3
```

### 2. Install PyTorch with CUDA

**Do this first, before installing anything else.**

```bash
# Check your CUDA version
nvidia-smi

# Install matching PyTorch build (replace cu121 with cu124 if your CUDA is 12.4+)
pip install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Verify GPU is detected
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

### 3. Install FFmpeg (system binary)

```bash
# Windows — Chocolatey
choco install ffmpeg

# Windows — Scoop
scoop install ffmpeg

# Verify
ffmpeg -version
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. First run — model downloads

On the first run the following models are downloaded automatically and cached in `~/.cache/huggingface/` and `~/.cache/whisper/`:

| Model | Size | Purpose |
|---|---|---|
| `unsloth/Qwen3-VL-2B-Instruct-unsloth-bnb-4bit` | ~2.4 GB | Visual analysis (4-bit quantized) |
| `microsoft/trocr-small-printed` | ~60 MB | OCR fallback |
| Whisper `tiny` | ~39 MB | Audio transcription |

Models are only downloaded once. Subsequent runs load from cache instantly.

---

## Usage

### Frame-by-frame analysis (default)

```bash
python main.py "path/to/video.mp4"
```

### Holistic analysis (recommended for scam detection)

Passes the entire video plus metadata to Qwen3-VL in one context window.

```bash
python main.py "path/to/video.mp4" --holistic --title "Video Title" --description "Description text"
```

### All CLI options

| Argument | Default | Description |
|---|---|---|
| `video_path` | *(required)* | Path to video file |
| `--output-dir` | Auto-timestamped | Output directory |
| `--holistic` | False | Use holistic analysis mode |
| `--title` | None | Video title (holistic mode) |
| `--description` | None | Video description (holistic mode) |
| `--frame-interval` | 30 | Extract every N frames |
| `--sharpness-threshold` | 100.0 | Laplacian variance cutoff |
| `--no-sharpness-filter` | False | Disable sharpness filtering |
| `--no-frame-analysis` | False | Skip Qwen3-VL frame analysis |
| `--whisper-model` | `tiny` | `tiny` / `base` / `small` / `medium` / `large` |
| `--device` | auto | `cuda` or `cpu` |

### Programmatic usage

```python
from main import OptiScamAnalyzer

config = {
    'sharpness_threshold': 100.0,
    'whisper_model_size': 'tiny',
    'use_trocr_fallback': True,
    'trocr_confidence_threshold': 0.5,
}

analyzer = OptiScamAnalyzer(config=config)

# Frame-by-frame
results = analyzer.process_video(
    video_path='video.mp4',
    frame_interval=30,
    use_sharpness_filter=True,
    analyze_frames=True,
)

# Holistic
results = analyzer.analyze_video_holistic(
    video_path='video.mp4',
    title='Win a free iPhone!',
    description='Click the link in bio...',
)
```

---

## Output

**Frame-by-frame mode:**
```
output_<videoname>_<timestamp>/
├── frames/
│   ├── frame_0000.jpg
│   └── ...
├── analysis_report.json
├── summary.txt
└── transcription.txt
```

**Holistic mode:**
```
output_<videoname>_<timestamp>_holistic/
├── frames/
├── holistic_analysis_report.json
└── scam_analysis_summary.txt
```

---

## Configuration reference

```python
config = {
    # Image processing
    'clahe_clip_limit': 2.0,
    'clahe_tile_grid_size': (8, 8),
    'sharpness_threshold': 100.0,

    # OCR
    'use_trocr_fallback': True,
    'trocr_confidence_threshold': 0.5,

    # Audio
    'whisper_model_size': 'tiny',       # tiny | base | small | medium | large
    'whisper_language': None,           # None = auto-detect, or e.g. 'en'

    # Vision model
    'vision_model_name': 'unsloth/Qwen3-VL-2B-Instruct-unsloth-bnb-4bit',

    # Device
    'device': None,                     # None = auto-detect GPU
}
```

---

## GPU usage by component

| Component | GPU? | Notes |
|---|---|---|
| Qwen3-VL | Yes | `device_map="auto"`, 4-bit BNB, CUDA required |
| Whisper | Yes | auto-detects CUDA |
| TrOCR | Yes | auto-detects CUDA |
| RapidOCR | No | ONNX Runtime, CPU only |
| OpenCV (CLAHE) | No | always CPU |

---

## Troubleshooting

### `torch.cuda.is_available()` returns `False`
PyTorch is installed as a CPU-only build. Reinstall with the CUDA index:
```bash
pip install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### `ImportError: No module named 'qwen_vl_utils'`
```bash
pip install qwen-vl-utils
```

### `ModuleNotFoundError: No module named 'sentencepiece'`
```bash
pip install sentencepiece
```

### `ValueError: Using a device_map requires accelerate`
```bash
pip install accelerate
```

### `TypeError: LoadLibrary() argument 1 must be str, not None`
A Graphite Whisper stub (`whisper.py`) is shadowing the real OpenAI Whisper package:
```bash
pip uninstall whisper -y
pip install openai-whisper
```

### FFmpeg not found
```bash
# Verify it is on PATH
ffmpeg -version

# Windows — add to PATH permanently
setx PATH "%PATH%;C:\path\to\ffmpeg\bin"
```

### CUDA out of memory
Use smaller models:
```bash
python main.py video.mp4 --whisper-model tiny --no-frame-analysis
```

---

## System requirements

| | Minimum | Recommended |
|---|---|---|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16 GB+ |
| VRAM | 4 GB | 8 GB+ |
| Storage | 10 GB | 20 GB+ |
| GPU | — | NVIDIA RTX 3060 or better |

---

## Modules

| File | Class | Purpose |
|---|---|---|
| [main.py](main.py) | `OptiScamAnalyzer` | Pipeline orchestration, CLI |
| [image_processing.py](image_processing.py) | `ImageProcessing` | CLAHE, sharpness filtering, frame extraction |
| [text_extraction.py](text_extraction.py) | `TextExtractor` | RapidOCR + TrOCR dual OCR |
| [audio_transcription.py](audio_transcription.py) | `AudioTranscriber` | Whisper transcription |
| [Qwen3_VL_2B.py](Qwen3_VL_2B.py) | `Qwen3VLModel` | Vision-language inference |
| [model_for_pre_processing.py](model_for_pre_processing.py) | `PreProcessing` | Additional image preprocessing utilities |

---

## License

Open-source components used:

| Component | License |
|---|---|
| Qwen3-VL (Unsloth 4-bit) | Apache 2.0 |
| OpenAI Whisper | MIT |
| Microsoft TrOCR | MIT |
| RapidOCR | Apache 2.0 |
| OpenCV | Apache 2.0 |
