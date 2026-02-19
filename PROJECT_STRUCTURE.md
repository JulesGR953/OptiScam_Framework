# Project Structure

## Overview

```
OptiScam_Qwen3/
├── Core Modules
│   ├── main.py                          # Main orchestration system
│   ├── image_processing.py              # CLAHE + Laplacian Variance
│   ├── text_extraction.py               # RapidOCR + TrOCR
│   ├── audio_transcription.py           # Whisper integration
│   ├── Qwen3_VL_2B.py                   # Qwen3-VL-2B-Instruct model
│   └── model_for_pre_processing.py      # Additional preprocessing utilities
│
├── Configuration & Setup
│   ├── requirements.txt                 # Python dependencies
│   ├── config_template.json             # Configuration template
│   ├── setup.py                         # Setup verification script
│   └── install.bat                      # Windows installation script
│
├── Documentation
│   ├── README.md                        # Complete documentation
│   ├── QUICK_START.md                   # Quick start guide
│   └── PROJECT_STRUCTURE.md             # This file
│
├── Examples
│   └── example_usage.py                 # Usage examples and patterns
│
└── Utilities
    └── .gitignore                       # Git ignore rules
```

## File Descriptions

### Core Modules

#### [main.py](main.py)
**OptiScamAnalyzer - Main Orchestration System**
- Coordinates all analysis components
- Processes videos end-to-end
- Generates comprehensive reports
- Command-line interface

**Key Classes:**
- `OptiScamAnalyzer`: Main analyzer class

**Key Methods:**
- `process_video()`: Process complete video
- `_generate_summary()`: Create human-readable report

**Usage:**
```bash
python main.py video.mp4 --frame-interval 30
```

---

#### [image_processing.py](image_processing.py)
**Image Processing with CLAHE and Sharpness Filtering**
- Applies CLAHE (Contrast Limited Adaptive Histogram Equalization)
- Calculates Laplacian Variance for sharpness scoring
- Smart frame sampling based on sharpness threshold
- Preserves frame metadata with timestamps

**Key Classes:**
- `ImageProcessing`: CLAHE and frame extraction

**Key Methods:**
- `calculate_sharpness()`: Laplacian variance calculation
- `apply_clahe()`: CLAHE enhancement
- `sample_frames_by_sharpness()`: Sharpness-based frame sampling

**Features:**
- Grayscale and color image support (LAB color space)
- Configurable CLAHE parameters
- Adjustable sharpness threshold
- Frame metadata tracking

---

#### [text_extraction.py](text_extraction.py)
**Dual OCR System: RapidOCR + TrOCR**
- Primary: RapidOCR for fast text detection
- Fallback: TrOCR for low-confidence detections
- Timestamp tracking for text timeline
- Bounding box and confidence scores

**Key Classes:**
- `TextExtractor`: Dual OCR system

**Key Methods:**
- `extract_with_rapidocr()`: Fast OCR
- `extract_with_trocr()`: Accurate OCR fallback
- `extract_text_from_frames()`: Batch processing
- `get_text_timeline()`: Timeline organization

**Features:**
- Confidence-based fallback mechanism
- Bounding box cropping for TrOCR
- Timeline view of text per second
- Method tracking (rapidocr vs trocr)

---

#### [audio_transcription.py](audio_transcription.py)
**Whisper Audio Transcription**
- Audio extraction from video via FFmpeg
- High-accuracy transcription with Whisper
- Word-level timestamp tracking
- Multi-language support with auto-detection

**Key Classes:**
- `AudioTranscriber`: Whisper integration

**Key Methods:**
- `extract_audio_from_video()`: FFmpeg audio extraction
- `transcribe_video()`: End-to-end transcription
- `get_transcription_timeline()`: Segment timeline
- `get_text_at_timestamp()`: Query by time
- `export_transcription()`: Export to TXT/JSON/SRT

**Features:**
- Configurable model size (tiny to large)
- Automatic audio cleanup
- Multiple export formats
- Language detection

---

#### [Qwen3_VL_2B.py](Qwen3_VL_2B.py)
**Qwen3-VL-2B-Instruct Vision-Language Model**
- Visual understanding and analysis
- Scam detection with context awareness
- Integrates OCR and audio transcription
- Custom prompt support

**Key Classes:**
- `Qwen3VLModel`: Vision model wrapper

**Key Methods:**
- `analyze_image()`: Single image analysis
- `analyze_with_context()`: Context-aware analysis
- `analyze_frames_for_scams()`: Scam detection pipeline
- `batch_analyze()`: Batch processing

**Features:**
- GPU acceleration support
- Context integration (OCR + audio)
- Customizable analysis prompts
- Scam indicator detection

---

#### [model_for_pre_processing.py](model_for_pre_processing.py)
**Additional Preprocessing Utilities**
- Denoising algorithms (bilateral, nlmeans, gaussian)
- Brightness/contrast adjustment
- Unsharp masking for edge enhancement
- Auto white balance
- OCR-specific enhancement
- Skew detection and correction

**Key Classes:**
- `PreProcessing`: Utility functions

**Key Methods:**
- `denoise_image()`: Various denoising methods
- `enhance_for_ocr()`: OCR optimization
- `detect_and_correct_skew()`: Text alignment
- `apply_preprocessing_pipeline()`: Complete pipeline

**Features:**
- Multiple denoising algorithms
- OCR-specific optimizations
- Model input preparation
- Morphological operations

---

### Configuration & Setup

#### [requirements.txt](requirements.txt)
**Python Dependencies**
- PyTorch and Transformers for deep learning
- OpenCV and Pillow for image processing
- RapidOCR and TrOCR for text extraction
- Whisper for audio transcription
- Supporting utilities

#### [config_template.json](config_template.json)
**Configuration Template**
- Image processing settings
- Text extraction parameters
- Audio transcription options
- Vision model configuration
- Performance tuning
- Preset configurations (quick, balanced, high_quality)

#### [setup.py](setup.py)
**Setup Verification Script**
- Checks Python version
- Verifies FFmpeg installation
- Tests package installations
- Checks CUDA availability
- Downloads and tests models
- Runs system diagnostics

**Usage:**
```bash
python setup.py
```

#### [install.bat](install.bat)
**Windows Installation Script**
- Automated installation for Windows
- Checks prerequisites
- Installs Python packages
- Verifies FFmpeg
- Provides next steps

**Usage:**
```bash
install.bat
```

---

### Documentation

#### [README.md](README.md)
**Complete Documentation**
- System overview and architecture
- Installation instructions
- Usage examples (CLI and programmatic)
- Configuration options
- Module documentation
- Performance tips
- Troubleshooting guide
- System requirements

#### [QUICK_START.md](QUICK_START.md)
**Quick Start Guide**
- 5-minute setup guide
- Basic usage examples
- Common commands
- Troubleshooting quick reference
- Component overview

#### [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
**This File**
- Complete project structure
- File descriptions
- Module relationships
- Development workflow

---

### Examples

#### [example_usage.py](example_usage.py)
**Usage Examples and Patterns**

**7 Complete Examples:**
1. Basic video analysis
2. Custom configuration
3. Quick OCR-only analysis
4. Individual component usage
5. Context-aware analysis
6. Batch processing multiple videos
7. Export and process results

**Usage:**
```bash
python example_usage.py
```

---

## Module Relationships

```
main.py (Orchestrator)
    │
    ├─→ image_processing.py
    │   └─→ model_for_pre_processing.py (optional)
    │
    ├─→ text_extraction.py
    │   ├─→ RapidOCR
    │   └─→ TrOCR (Transformers)
    │
    ├─→ audio_transcription.py
    │   ├─→ FFmpeg (external)
    │   └─→ Whisper
    │
    └─→ Qwen3_VL_2B.py
        └─→ Qwen2-VL-2B-Instruct (Transformers)
```

## Data Flow

```
Video Input
    ↓
[image_processing] → Frames + Metadata
    ↓
[text_extraction] → Text Detections + Timeline
    ↓
[audio_transcription] → Audio Transcript + Timeline
    ↓
[Qwen3_VL_2B] → Visual Analysis + Context
    ↓
[main] → Comprehensive Report
    ↓
Output Directory
    ├─ frames/
    ├─ analysis_report.json
    ├─ summary.txt
    └─ transcription.txt
```

## Development Workflow

### Adding New Features

1. **New Preprocessing Method:**
   - Add to `model_for_pre_processing.py`
   - Import in `image_processing.py` if needed
   - Update `ImageProcessing` class

2. **New Analysis Prompt:**
   - Add method to `Qwen3_VL_2B.py`
   - Update `OptiScamAnalyzer` in `main.py`
   - Add config option to `config_template.json`

3. **New OCR Method:**
   - Add to `text_extraction.py`
   - Update `TextExtractor` class
   - Modify fallback logic if needed

### Testing

1. **Individual Components:**
```python
from image_processing import ImageProcessing
img_proc = ImageProcessing()
# Test methods...
```

2. **Integration:**
```bash
python setup.py  # Verify setup
python main.py test_video.mp4  # Test pipeline
```

3. **Performance:**
```bash
# Quick mode
python main.py video.mp4 --whisper-model tiny --no-frame-analysis

# Full mode
python main.py video.mp4 --whisper-model medium --frame-interval 15
```

## File Sizes and Performance

| Component | Size | Load Time | Memory Usage |
|-----------|------|-----------|--------------|
| Whisper (tiny) | ~70MB | <5s | ~1GB RAM |
| Whisper (base) | ~140MB | ~10s | ~1.5GB RAM |
| TrOCR | ~1GB | ~30s | ~2GB RAM |
| Qwen2-VL-2B | ~4GB | ~60s | ~6GB RAM (GPU) |

## Configuration Examples

### Quick Analysis (Fast)
```json
{
  "frame_interval": 60,
  "whisper_model_size": "tiny",
  "analyze_frames": false,
  "use_trocr_fallback": false
}
```

### Balanced Analysis
```json
{
  "frame_interval": 30,
  "whisper_model_size": "base",
  "analyze_frames": true,
  "use_trocr_fallback": true
}
```

### High-Quality Analysis
```json
{
  "frame_interval": 15,
  "whisper_model_size": "medium",
  "sharpness_threshold": 150.0,
  "analyze_frames": true
}
```

## Output Formats

### analysis_report.json
Complete structured data with all results

### summary.txt
Human-readable report with:
- Audio transcription
- Text timeline
- Visual analyses

### transcription.txt
Audio transcript with timestamps

## Extension Points

1. **Custom Scam Detection Rules**
   - Extend `Qwen3VLModel.analyze_frames_for_scams()`
   - Add custom prompts via config

2. **Additional OCR Engines**
   - Add to `TextExtractor` class
   - Implement as alternative to RapidOCR/TrOCR

3. **Alternative Vision Models**
   - Create new model wrapper (like Qwen3_VL_2B.py)
   - Update main.py to support selection

4. **Custom Preprocessing**
   - Add to `PreProcessing` class
   - Integrate into `ImageProcessing` pipeline

## Version Information

- **Python**: 3.8+
- **PyTorch**: 2.0+
- **Transformers**: 4.35+
- **OpenCV**: 4.8+
- **Whisper**: Latest

---

For detailed usage instructions, see [README.md](README.md)
For quick start, see [QUICK_START.md](QUICK_START.md)
For code examples, see [example_usage.py](example_usage.py)
