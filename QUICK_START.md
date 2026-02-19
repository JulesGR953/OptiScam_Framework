# Quick Start Guide

Get up and running with OptiScam in 5 minutes.

## Installation

### 1. Install FFmpeg (Required)

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# OR using Scoop
scoop install ffmpeg
```

**Verify installation:**
```bash
ffmpeg -version
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Setup

```bash
python setup.py
```

## Basic Usage

### Analyze a Video

```bash
python main.py path/to/video.mp4
```

That's it! The system will:
1. Extract frames with CLAHE enhancement
2. Filter by sharpness (Laplacian Variance)
3. Extract text with RapidOCR + TrOCR
4. Transcribe audio with Whisper
5. Analyze frames with Qwen3-VL-2B
6. Generate comprehensive report

### Results Location

Results are saved to `output_videoname_timestamp/`:
- `frames/` - Extracted frames
- `analysis_report.json` - Complete data
- `summary.txt` - Human-readable report
- `transcription.txt` - Audio transcript

## Common Commands

### Quick Analysis (Fast)
```bash
python main.py video.mp4 --whisper-model tiny --frame-interval 60 --no-frame-analysis
```

### Balanced Analysis (Recommended)
```bash
python main.py video.mp4 --frame-interval 30 --whisper-model base
```

### High-Quality Analysis (Slow but thorough)
```bash
python main.py video.mp4 --frame-interval 15 --whisper-model medium --sharpness-threshold 150
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--frame-interval N` | Extract every N frames | 30 |
| `--whisper-model SIZE` | tiny/base/small/medium/large | base |
| `--sharpness-threshold N` | Sharpness filter threshold | 100.0 |
| `--output-dir DIR` | Custom output directory | Auto |
| `--no-sharpness-filter` | Disable sharpness filtering | Off |
| `--no-frame-analysis` | Skip Qwen3-VL analysis | Off |

## Programmatic Usage

```python
from main import OptiScamAnalyzer

# Initialize
analyzer = OptiScamAnalyzer()

# Process video
results = analyzer.process_video(
    video_path='video.mp4',
    frame_interval=30
)

# Access results
print(results['audio_transcription']['full_text'])
```

## Troubleshooting

### FFmpeg Not Found
```bash
# Check if FFmpeg is in PATH
ffmpeg -version

# Add to PATH (Windows)
setx PATH "%PATH%;C:\path\to\ffmpeg\bin"
```

### CUDA Out of Memory
```bash
# Use smaller models
python main.py video.mp4 --whisper-model tiny --no-frame-analysis
```

### Slow Performance
- Use GPU: Install PyTorch with CUDA
- Increase frame interval: `--frame-interval 60`
- Use smaller Whisper: `--whisper-model tiny`
- Skip frame analysis: `--no-frame-analysis`

## System Requirements

### Minimum
- Python 3.8+
- 8GB RAM
- CPU: 4 cores
- 10GB disk space

### Recommended
- Python 3.10+
- 16GB+ RAM
- GPU: NVIDIA RTX 3060+ (8GB VRAM)
- 20GB+ disk space

## What Each Component Does

### CLAHE
Enhances image contrast for better OCR and analysis

### Laplacian Variance
Filters out blurry frames automatically

### RapidOCR + TrOCR
- RapidOCR: Fast text detection
- TrOCR: Fallback for difficult text
- Tracks text per timestamp

### Whisper
- Transcribes audio with word-level timestamps
- Works offline (no API needed)
- Supports 99+ languages

### Qwen3-VL-2B
- Visual understanding and scam detection
- Context-aware (uses OCR + audio)
- Identifies suspicious patterns

## Examples

See [example_usage.py](example_usage.py) for detailed code examples:
- Basic analysis
- Custom configuration
- OCR-only processing
- Individual components
- Context-aware analysis
- Batch processing
- Export results

## Next Steps

1. Read full documentation: [README.md](README.md)
2. Explore examples: [example_usage.py](example_usage.py)
3. Customize config: [config_template.json](config_template.json)

## Support

For issues or questions:
- Check README.md troubleshooting section
- Review example_usage.py for code examples
- Verify setup with `python setup.py`
