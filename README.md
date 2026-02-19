# OptiScam - Advanced Video Analysis System

A comprehensive video analysis system that combines CLAHE image enhancement, Laplacian Variance sharpness filtering, RapidOCR + TrOCR text extraction, Whisper audio transcription, and Qwen3-VL-2B-Instruct visual understanding for detecting potential scams in videos.

## Features

### 1. **CLAHE Image Enhancement**
- Applies Contrast Limited Adaptive Histogram Equalization (CLAHE) to improve frame quality
- Works on both grayscale and color images (LAB color space)

### 2. **Laplacian Variance Sharpness Filtering**
- Automatically filters out blurry frames using Laplacian variance calculation
- Ensures only sharp, high-quality frames are analyzed
- Configurable sharpness threshold

### 3. **Dual OCR System (RapidOCR + TrOCR)**
- **RapidOCR**: Fast text detection and extraction
- **TrOCR**: Fallback for low-confidence detections with higher accuracy
- Tracks text with timestamps for timeline analysis
- No text is missed per frame sample

### 4. **Whisper Audio Transcription**
- High-accuracy audio transcription using OpenAI's Whisper
- Word-level timestamps for precise synchronization
- Supports multiple languages with auto-detection
- Works offline (no API keys required)

### 5. **Qwen3-VL-2B-Instruct Visual Analysis**
- State-of-the-art vision-language model for frame analysis
- Scam detection with context from OCR and audio transcription
- Identifies suspicious patterns, fake urgency, phishing attempts

### 6. **Integrated Timeline**
- Synchronized text, audio, and visual analysis per timestamp
- Complete frame-by-frame breakdown
- Exportable reports in JSON and human-readable formats

## System Architecture

```
Video Input
    ↓
┌───────────────────────────────────────────────┐
│  Image Processing (CLAHE + Sharpness Filter)  │
│  - Extract frames at intervals                │
│  - Apply CLAHE enhancement                    │
│  - Filter by Laplacian Variance               │
└───────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────┐
│  Text Extraction (RapidOCR + TrOCR)          │
│  - Primary: RapidOCR for speed               │
│  - Fallback: TrOCR for accuracy              │
│  - Timeline tracking per frame               │
└───────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────┐
│  Audio Transcription (Whisper)                │
│  - Extract audio from video                   │
│  - Word-level timestamp transcription         │
│  - Multi-language support                     │
└───────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────┐
│  Visual Analysis (Qwen3-VL-2B-Instruct)       │
│  - Context-aware frame analysis               │
│  - Scam indicator detection                   │
│  - Integration with OCR + Audio data          │
└───────────────────────────────────────────────┘
    ↓
Comprehensive Report (JSON + Summary)
```

## Installation

### Prerequisites

1. **Python 3.8 or higher**
2. **FFmpeg** (required for audio extraction)
   ```bash
   # Windows (using Chocolatey)
   choco install ffmpeg

   # Windows (using Scoop)
   scoop install ffmpeg

   # Or download from https://ffmpeg.org/download.html
   ```

3. **CUDA** (optional, for GPU acceleration)

### Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# If you encounter issues with PyTorch, install it separately first:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121  # For CUDA 12.1
# OR
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu  # For CPU only
```

### Download Models

The models will be automatically downloaded on first use:
- **Qwen2-VL-2B-Instruct** (~4GB)
- **TrOCR-base-printed** (~1GB)
- **Whisper base** (~140MB)

## Usage

### Basic Usage

```bash
python main.py path/to/video.mp4
```

### Advanced Options

```bash
python main.py path/to/video.mp4 \
    --output-dir results \
    --frame-interval 30 \
    --sharpness-threshold 100.0 \
    --whisper-model base
```

### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `video_path` | Path to video file (required) | - |
| `--output-dir` | Output directory for results | Auto-generated |
| `--frame-interval` | Extract every N frames | 30 |
| `--sharpness-threshold` | Laplacian variance threshold | 100.0 |
| `--no-sharpness-filter` | Disable sharpness filtering | False |
| `--no-frame-analysis` | Skip Qwen3-VL analysis | False |
| `--whisper-model` | Whisper model size (tiny/base/small/medium/large) | base |

### Example

```bash
# Analyze a video with custom settings
python main.py scam_video.mp4 \
    --output-dir analysis_results \
    --frame-interval 15 \
    --sharpness-threshold 150.0 \
    --whisper-model small

# Quick analysis (skip frame analysis, use tiny Whisper)
python main.py video.mp4 \
    --no-frame-analysis \
    --whisper-model tiny \
    --frame-interval 60
```

## Programmatic Usage

```python
from main import OptiScamAnalyzer

# Initialize with custom configuration
config = {
    'sharpness_threshold': 100.0,
    'whisper_model_size': 'base',
    'use_trocr_fallback': True,
    'trocr_confidence_threshold': 0.5
}

analyzer = OptiScamAnalyzer(config=config)

# Process video
results = analyzer.process_video(
    video_path='path/to/video.mp4',
    frame_interval=30,
    use_sharpness_filter=True,
    analyze_frames=True
)

# Access results
print(f"Frames analyzed: {len(results['frames'])}")
print(f"Text timeline: {results['text_timeline']}")
print(f"Transcription: {results['audio_transcription']['full_text']}")
```

## Output Structure

```
output_videoname_20260212_143022/
├── frames/                      # Extracted and processed frames
│   ├── frame_0000.jpg
│   ├── frame_0001.jpg
│   └── ...
├── analysis_report.json         # Complete analysis in JSON format
├── summary.txt                  # Human-readable summary report
└── transcription.txt            # Audio transcription with timestamps
```

### Report Contents

**analysis_report.json** includes:
- Frame metadata (timestamps, sharpness scores, paths)
- Text detections with timestamps and confidence scores
- Audio transcription timeline
- Visual analysis results with context
- Complete configuration used

**summary.txt** includes:
- Audio transcription
- Text detection timeline
- Frame-by-frame visual analysis
- Context-aware insights

## Configuration Options

### Image Processing

```python
config = {
    'clahe_clip_limit': 2.0,           # CLAHE clip limit
    'clahe_tile_grid_size': (8, 8),    # CLAHE tile grid
    'sharpness_threshold': 100.0        # Laplacian variance threshold
}
```

### Text Extraction

```python
config = {
    'use_trocr_fallback': True,         # Enable TrOCR fallback
    'trocr_confidence_threshold': 0.5   # Confidence threshold for TrOCR
}
```

### Audio Transcription

```python
config = {
    'whisper_model_size': 'base',       # tiny, base, small, medium, large
    'whisper_language': None            # Auto-detect or specify (e.g., 'en')
}
```

### Vision Model

```python
config = {
    'vision_model_name': 'Qwen/Qwen2-VL-2B-Instruct'
}
```

## Module Documentation

### [image_processing.py](image_processing.py)
- `ImageProcessing`: CLAHE enhancement and frame extraction
- `calculate_sharpness()`: Laplacian variance calculation
- `sample_frames_by_sharpness()`: Smart frame sampling

### [text_extraction.py](text_extraction.py)
- `TextExtractor`: RapidOCR + TrOCR integration
- `extract_text()`: Dual OCR system
- `get_text_timeline()`: Timestamp-organized text

### [audio_transcription.py](audio_transcription.py)
- `AudioTranscriber`: Whisper integration
- `transcribe_video()`: End-to-end audio transcription
- `get_text_at_timestamp()`: Query audio at specific time

### [Qwen3_VL_2B.py](Qwen3_VL_2B.py)
- `Qwen3VLModel`: Vision-language model wrapper
- `analyze_with_context()`: Context-aware analysis
- `analyze_frames_for_scams()`: Scam detection pipeline

### [model_for_pre_processing.py](model_for_pre_processing.py)
- `PreProcessing`: Additional preprocessing utilities
- Denoising, brightness/contrast adjustment, white balance
- OCR optimization and skew correction

## Performance Tips

1. **GPU Acceleration**: Install PyTorch with CUDA for 10-20x speedup
2. **Frame Interval**: Increase for faster processing (e.g., 60 for long videos)
3. **Whisper Model**: Use 'tiny' or 'base' for faster transcription
4. **Sharpness Threshold**: Increase to filter more aggressively (reduce frames)
5. **Skip Frame Analysis**: Use `--no-frame-analysis` for quick OCR+audio only

## System Requirements

### Minimum
- CPU: 4 cores
- RAM: 8GB
- Storage: 10GB free space
- GPU: None (CPU-only mode supported)

### Recommended
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 20GB+ free space
- GPU: NVIDIA GPU with 8GB+ VRAM (RTX 3060 or better)

## Troubleshooting

### CUDA Out of Memory
```python
# Use smaller models or reduce batch size
config = {
    'whisper_model_size': 'tiny',  # Instead of 'base'
}
```

### FFmpeg Not Found
```bash
# Verify FFmpeg installation
ffmpeg -version

# Add to PATH if needed (Windows)
setx PATH "%PATH%;C:\path\to\ffmpeg\bin"
```

### Model Download Issues
```python
# Set HuggingFace cache directory
import os
os.environ['TRANSFORMERS_CACHE'] = 'D:/models/cache'
```

## Why Whisper Instead of YouTube API?

1. **Universal**: Works with any video source (YouTube, TikTok, local files)
2. **Offline**: No API keys or internet required after model download
3. **Privacy**: All processing done locally
4. **Accuracy**: State-of-the-art transcription quality
5. **Free**: No usage limits or costs
6. **Multi-language**: 99+ languages supported out of the box

YouTube API only works for YouTube videos and requires authentication.

## License

This project uses multiple open-source components. Please check individual licenses:
- Qwen2-VL: Apache 2.0
- Whisper: MIT
- TrOCR: MIT
- RapidOCR: Apache 2.0

## Citation

If you use this system in research, please cite the underlying models:
- [Qwen2-VL](https://github.com/QwenLM/Qwen2-VL)
- [Whisper](https://github.com/openai/whisper)
- [TrOCR](https://github.com/microsoft/unilm/tree/master/trocr)
