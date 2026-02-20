# OptiScam — Video Scam Detection System

A multi-modal video analysis pipeline for detecting scams in short-form videos.
Combines CLAHE image enhancement, dual OCR (RapidOCR + TrOCR), Whisper audio transcription,
and Qwen3-VL-2B vision-language model inference with 4-bit NF4 quantization.

---

## Software Requirements

| Tool / Library | Min Version | Purpose |
|---|---|---|
| Python | 3.10 | Runtime |
| CUDA Toolkit | 12.x | GPU acceleration |
| PyTorch | 2.0.0 | Deep learning backend |
| torchvision | 0.15.0 | Vision transforms |
| Transformers (HuggingFace) | 4.50.0 | Model loading & inference |
| Accelerate (HuggingFace) | 0.25.0 | `device_map="auto"` support |
| BitsAndBytes | 0.43.0 | NF4 4-bit quantization |
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
│  · RapidOCR  (primary, fast, CPU)       │
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
│  Qwen3VLModel.classify_video()          │
│  · Up to 6 frames, evenly subsampled    │
│  · Images capped at 448×448 px          │
│  · Prompt: title + description +        │
│    "Is this a scam? Yes/No + reasoning" │
│  · One inference call per video         │
└─────────────────────────────────────────┘
    │
    ▼
Verdict (Yes/No + 4-5 sentence reasoning)
+ JSON report + summary.txt
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

# Install matching PyTorch build
# CUDA 12.6 (recommended):
pip install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu126
# CUDA 12.4:
# pip install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu124
# CUDA 12.1:
# pip install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu121

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

| Model | Download Size | VRAM After Loading | Purpose |
|---|---|---|---|
| `Qwen/Qwen3-VL-2B-Instruct` | ~5 GB | ~2 GB | Visual scam classification (NF4 quantized on first run) |
| `microsoft/trocr-small-printed` | ~60 MB | ~60 MB | OCR fallback |
| Whisper `tiny` | ~39 MB | ~39 MB | Audio transcription |

Models are only downloaded once. Subsequent runs load from cache instantly.

---

## Usage

### Basic (no metadata)

```bash
python main.py "path/to/video.mp4"
```

### With title and description (recommended)

Title and description are injected directly into the model prompt, matching the training format.

```bash
python main.py "path/to/video.mp4" \
    --title "Best Free Crypto Mining Apps!" \
    --description "Want to earn crypto without investment? Click the link..."
```

### Holistic mode

Same classification method, samples frames at a lower rate (every 60 frames vs 30).
Useful for longer videos where dense frame extraction is unnecessary.

```bash
python main.py "path/to/video.mp4" --holistic \
    --title "Video Title" \
    --description "Description text"
```

### All CLI options

| Argument | Default | Description |
|---|---|---|
| `video_path` | *(required)* | Path to video file |
| `--output-dir` | Auto-timestamped | Output directory |
| `--title` | None | Video title (injected into model prompt) |
| `--description` | None | Video description (injected into model prompt) |
| `--holistic` | False | Lower frame rate variant (every 60 frames) |
| `--frame-interval` | 30 | Extract every N frames |
| `--sharpness-threshold` | 100.0 | Laplacian variance cutoff for frame selection |
| `--no-sharpness-filter` | False | Disable sharpness filtering (keep all frames) |
| `--whisper-model` | `tiny` | `tiny` / `base` / `small` / `medium` / `large` |
| `--device` | auto | `cuda` or `cpu` |

### Programmatic usage

```python
from main import OptiScamAnalyzer

config = {
    # Image processing
    'sharpness_threshold': 100.0,

    # OCR
    'use_trocr_fallback': True,
    'trocr_confidence_threshold': 0.5,

    # Audio
    'whisper_model_size': 'tiny',

    # Vision model
    'vision_model_name': 'Qwen/Qwen3-VL-2B-Instruct',

    # Device
    'device': None,  # None = auto-detect GPU
}

analyzer = OptiScamAnalyzer(config=config)

results = analyzer.process_video(
    video_path='video.mp4',
    title='Best Free Crypto Mining Apps!',
    description='Want to earn crypto without investment? Click the link...',
)

print(results['verdict'])   # "No. The content is considered legitimate because..."
print(results['is_scam'])   # True or False
```

---

## Output

Both modes produce the same directory structure:

```
output_<videoname>_<timestamp>/
├── frames/
│   ├── frame_0000.jpg
│   └── ...
├── analysis_report.json
├── summary.txt
└── transcription.txt
```

Holistic mode appends `_holistic` to the directory name.

### `analysis_report.json` structure

```json
{
  "video_path": "...",
  "title": "...",
  "description": "...",
  "output_dir": "...",
  "timestamp": "...",
  "frames": [...],
  "text_detections": [...],
  "text_timeline": {...},
  "audio_transcription": {
    "full_text": "...",
    "timeline": [...],
    "language": "en"
  },
  "verdict": "No. The content is considered legitimate because...",
  "is_scam": false
}
```

### `summary.txt` structure

```
============================================================
OptiScam Video Analysis Report
============================================================

SCAM VERDICT
------------------------------------------------------------
RESULT: NO — This video does not appear to be a scam.

No. The content is considered legitimate because...

AUDIO TRANSCRIPTION
------------------------------------------------------------
...

TEXT DETECTED IN FRAMES (Timeline)
------------------------------------------------------------
...
```

---

## Configuration reference

```python
config = {
    # Image processing
    'clahe_clip_limit': 2.0,            # CLAHE contrast limit
    'clahe_tile_grid_size': (8, 8),     # CLAHE tile size
    'sharpness_threshold': 100.0,       # Laplacian variance cutoff (higher = stricter)

    # OCR
    'use_trocr_fallback': True,         # Use TrOCR for low-confidence RapidOCR results
    'trocr_confidence_threshold': 0.5,  # RapidOCR confidence below this triggers TrOCR

    # Audio
    'whisper_model_size': 'tiny',       # tiny | base | small | medium | large
    'whisper_language': None,           # None = auto-detect, or e.g. 'en'

    # Vision model
    'vision_model_name': 'Qwen/Qwen3-VL-2B-Instruct',  # HuggingFace model ID

    # Device
    'device': None,                     # None = auto-detect GPU, or 'cuda' / 'cpu'
}
```

### `classify_video` parameters (advanced)

These are set inside `Qwen3VLModel.classify_video()` and can be changed if needed:

| Parameter | Default | Description |
|---|---|---|
| `max_frames` | 6 | Max frames passed to model per call (increase only with >8 GB VRAM) |
| `max_pixels` | 448 × 448 | Per-image resolution cap (lower = less VRAM, faster inference) |
| `max_new_tokens` | 512 | Max tokens in the model's response |

---

## GPU usage by component

| Component | GPU? | Notes |
|---|---|---|
| Qwen3-VL | Yes | `device_map="auto"`, NF4 via `BitsAndBytesConfig`, CUDA required |
| Whisper | Yes | auto-detects CUDA |
| TrOCR | Yes | auto-detects CUDA |
| RapidOCR | No | ONNX Runtime, CPU only |
| OpenCV (CLAHE) | No | always CPU |

---

## Troubleshooting

### `torch.cuda.is_available()` returns `False`
PyTorch is installed as a CPU-only build. Reinstall with the CUDA index:
```bash
pip install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu126
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

### CUDA out of memory during inference
The model uses ~2 GB VRAM at rest. Each additional frame adds visual tokens.
Reduce frame count or resolution:

```python
# In Qwen3_VL_2B.py, classify_video() call — reduce max_frames or max_pixels:
verdict = self.vision_model.classify_video(
    image_paths=frame_paths,
    title=title,
    description=description,
    max_frames=4,           # default 6 — lower to reduce VRAM
)
```

Or reduce the per-image resolution cap inside `classify_video`:
```python
"max_pixels": 336 * 336,  # default 448*448
```

---

## System requirements

| | Minimum | Recommended |
|---|---|---|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16 GB+ |
| VRAM | 6 GB | 8 GB+ |
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
| [Qwen3_VL_2B.py](Qwen3_VL_2B.py) | `Qwen3VLModel` | Vision-language scam classification |
| [model_for_pre_processing.py](model_for_pre_processing.py) | `PreProcessing` | Additional image preprocessing utilities |

---

## License

Open-source components used:

| Component | License |
|---|---|
| Qwen3-VL (Official, HuggingFace) | Apache 2.0 |
| OpenAI Whisper | MIT |
| Microsoft TrOCR | MIT |
| RapidOCR | Apache 2.0 |
| OpenCV | Apache 2.0 |
