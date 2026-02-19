# OptiScam - Holistic Video Scam Detection

## 🎯 Two Analysis Modes

### 1. **Holistic Analysis (Recommended for Scam Detection)**
Analyzes the **entire video** along with **title** and **description** to understand the complete context and detect scams more effectively.

**Best for:**
- YouTube, TikTok, social media videos
- Videos with metadata (title/description)
- Comprehensive scam detection
- Understanding video intent and context

**The model analyzes:**
- ✅ Entire video content (visual scenes, objects, people)
- ✅ Video title
- ✅ Video description
- ✅ Full audio transcription
- ✅ All visible text (OCR)
- ✅ Relationships and mismatches between all components

### 2. **Frame-by-Frame Analysis**
Analyzes individual frames separately with timestamp-based context.

**Best for:**
- Technical analysis of specific frames
- Timeline-based text extraction
- When you need frame-level granularity

---

## 🚀 Quick Start - Holistic Analysis

### Command Line

```bash
# Basic holistic analysis
python main.py video.mp4 --holistic

# With title and description
python main.py video.mp4 --holistic \
    --title "URGENT: Your Account Has Been Suspended" \
    --description "Click here to verify your account within 24 hours"

# With better transcription quality
python main.py video.mp4 --holistic \
    --title "Make $10,000 Per Day!" \
    --description "Join my exclusive course..." \
    --whisper-model medium
```

### Python API

```python
from main import OptiScamAnalyzer

# Initialize analyzer
analyzer = OptiScamAnalyzer()

# Analyze video with metadata
results = analyzer.analyze_video_holistic(
    video_path='suspicious_video.mp4',
    title='Free iPhone Giveaway - Click Now!',
    description='Limited time offer! Click the link to claim your prize...'
)

# Get scam analysis
print(results['scam_analysis'])
```

---

## 📊 What the Holistic Model Detects

### 1. **Mismatches & Deception**
- Does the title match the actual video content?
- Are there contradictions between description and audio?
- Does visual content support the claims being made?

### 2. **Scam Red Flags**
- ⚠️ Fake urgency ("limited time", "act now", "expires soon")
- ⚠️ Requests for personal info, passwords, or payment
- ⚠️ Too-good-to-be-true offers
- ⚠️ Impersonation of brands/companies
- ⚠️ Suspicious URLs or contact information
- ⚠️ Poor grammar or unprofessional presentation

### 3. **Manipulation Tactics**
- Fear-based messaging ("account suspended", "virus detected")
- Urgency tactics ("only 10 spots left", "expires in 1 hour")
- Greed exploitation ("make $10K per day", "free money")

### 4. **Visual Analysis**
- Fake websites or login pages
- Manipulated images or screenshots
- Generic stock footage inconsistent with claims
- Low-quality or stolen branding

---

## 💡 Example Use Cases

### YouTube Video Analysis

```python
from main import OptiScamAnalyzer

analyzer = OptiScamAnalyzer()

# Fetch metadata from YouTube (using youtube-dl or YouTube API)
results = analyzer.analyze_video_holistic(
    video_path='downloaded_video.mp4',
    title='Elon Musk Bitcoin Giveaway - 5000 BTC',
    description='''
    Elon Musk is giving away 5000 BTC!
    Send 0.1 BTC to this address to receive 1 BTC back.
    Limited time only! Don't miss out!
    '''
)

# Output:
# Scam Likelihood: Very High
# Evidence: Impersonation, fake giveaway, advance fee fraud
# Scam Type: Cryptocurrency scam / Advance fee fraud
```

### TikTok/Instagram Video

```python
results = analyzer.analyze_video_holistic(
    video_path='social_media_video.mp4',
    title='Make Money From Home - Easy!',
    description='DM me for the secret method. Limited spots!'
)
```

### Video Without Metadata

```python
# Even without title/description, it still analyzes content
results = analyzer.analyze_video_holistic(
    video_path='mystery_video.mp4',
    title=None,
    description=None
)
# Model analyzes based on visual content + audio + text
```

---

## 🔧 Configuration Options

### High-Quality Analysis

```python
config = {
    'whisper_model_size': 'medium',  # Better transcription (tiny/base/small/medium/large)
    'use_trocr_fallback': True,      # More accurate OCR
    'trocr_confidence_threshold': 0.6,
    'sharpness_threshold': 150.0      # Only sharp frames for OCR
}

analyzer = OptiScamAnalyzer(config=config)
```

### Fast Analysis (Lower Resource Usage)

```python
config = {
    'whisper_model_size': 'tiny',    # Faster transcription
    'use_trocr_fallback': False,     # Disable TrOCR (only RapidOCR)
    'sharpness_threshold': 80.0       # More lenient frame selection
}

analyzer = OptiScamAnalyzer(config=config)
```

---

## 📁 Output Structure

```
output_videoname_timestamp_holistic/
├── holistic_analysis_report.json    # Full JSON report
├── scam_analysis_summary.txt        # Human-readable summary
├── temp_audio.mp3                   # Extracted audio
└── frames/                          # Sampled frames (for OCR)
    ├── frame_0000_0.00s.jpg
    ├── frame_0060_60.00s.jpg
    └── ...
```

### JSON Report Structure

```json
{
  "video_path": "video.mp4",
  "title": "Video Title",
  "description": "Video Description",
  "timestamp": "2025-01-15T10:30:00",
  "analysis_type": "holistic",

  "audio_transcription": {
    "full_text": "Complete audio transcript...",
    "language": "en"
  },

  "ocr_text": "All text detected in video frames",

  "scam_analysis": "Scam Likelihood: High\n\nEvidence:\n- Fake urgency language...\n- Suspicious URL...\n\nScam Type: Phishing\n\nRecommendation: Do not click links or provide information."
}
```

---

## 🆚 Holistic vs Frame-by-Frame

| Feature | Holistic | Frame-by-Frame |
|---------|----------|----------------|
| **Analysis Scope** | Entire video | Individual frames |
| **Context Understanding** | Full context | Per-frame context |
| **Title/Description** | ✅ Included | ❌ Not used |
| **Scam Detection** | ✅ Comprehensive | ⚠️ Limited |
| **Speed** | Slower (analyzes whole video) | Faster (per frame) |
| **Best For** | Scam detection, content moderation | Technical frame analysis |

---

## 🔍 How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    VIDEO INPUT                          │
│  • Video file (MP4, AVI, etc.)                          │
│  • Title (optional)                                     │
│  • Description (optional)                               │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              CONTENT EXTRACTION                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Audio           │  │ Visual Text     │              │
│  │ (Whisper)       │  │ (RapidOCR +     │              │
│  │                 │  │  TrOCR)         │              │
│  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│         QWEN2-VL-2B HOLISTIC ANALYSIS                   │
│                                                         │
│  Inputs:                                                │
│  • Video frames (sampled at 1 FPS)                      │
│  • Title + Description                                  │
│  • Full audio transcript                                │
│  • All OCR text                                         │
│                                                         │
│  Analysis:                                              │
│  • Detect mismatches between components                 │
│  • Identify scam red flags                              │
│  • Recognize manipulation tactics                       │
│  • Assess visual authenticity                           │
│                                                         │
│  Output:                                                │
│  • Scam likelihood (Low/Medium/High/Very High)          │
│  • Specific evidence and examples                       │
│  • Scam type classification                             │
│  • Recommendations                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              RESULTS & REPORTS                          │
│  • JSON report                                          │
│  • Human-readable summary                               │
│  • Evidence and recommendations                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📖 Example Output

### Input
```
Video: "suspicious_video.mp4"
Title: "URGENT: Your Amazon Account Will Be Closed"
Description: "Click this link to verify your account immediately or it will be permanently deleted within 24 hours!"
```

### Output (Summary)
```
COMPREHENSIVE SCAM ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scam Likelihood: Very High

Evidence:
1. URGENCY TACTICS: Title uses "URGENT" and description threatens
   account deletion within "24 hours" - classic pressure tactic

2. IMPERSONATION: Claims to be from Amazon but video shows generic
   template, no authentic Amazon branding

3. SUSPICIOUS REQUEST: Asks user to click external link for
   "verification" - Amazon never does this via video

4. MISMATCH: Audio transcript mentions "login credentials" and
   "confirm payment information" - legitimate companies never
   request this

5. VISUAL INDICATORS: Low-quality graphics, stock footage, fake
   "Amazon" logo with incorrect colors

Scam Type: Phishing / Account Verification Scam

Recommendation:
DO NOT CLICK ANY LINKS. This is a phishing attempt to steal your
Amazon credentials. Amazon will never ask for account verification
through third-party links or videos. If you have concerns about
your account, log in directly through amazon.com.
```

---

## 🛠️ Advanced Usage

### Batch Processing Multiple Videos

```python
videos = [
    {'path': 'v1.mp4', 'title': 'Title 1', 'description': 'Desc 1'},
    {'path': 'v2.mp4', 'title': 'Title 2', 'description': 'Desc 2'},
]

analyzer = OptiScamAnalyzer()

for video in videos:
    results = analyzer.analyze_video_holistic(
        video_path=video['path'],
        title=video['title'],
        description=video['description']
    )

    # Save to database, trigger alerts, etc.
    if 'Very High' in results['scam_analysis']:
        print(f"⚠️ HIGH RISK: {video['title']}")
```

### Integration with YouTube API

```python
from googleapiclient.discovery import build
from main import OptiScamAnalyzer

# Fetch video metadata from YouTube
youtube = build('youtube', 'v3', developerKey='YOUR_API_KEY')
video_info = youtube.videos().list(part='snippet', id='VIDEO_ID').execute()

title = video_info['items'][0]['snippet']['title']
description = video_info['items'][0]['snippet']['description']

# Download video (using yt-dlp or similar)
# ... download code ...

# Analyze
analyzer = OptiScamAnalyzer()
results = analyzer.analyze_video_holistic(
    video_path='downloaded_video.mp4',
    title=title,
    description=description
)
```

---

## 💻 System Requirements

- **GPU**: NVIDIA GPU with 8GB+ VRAM (for Qwen2-VL-2B)
  - Or CPU with 16GB+ RAM (slower)
- **Python**: 3.8+
- **Storage**: ~10GB for models

---

## 🎯 Conclusion

**Use Holistic Analysis when:**
- ✅ You have video metadata (title/description)
- ✅ You want comprehensive scam detection
- ✅ You need to understand video intent and context
- ✅ You're analyzing social media or YouTube videos

**Use Frame-by-Frame Analysis when:**
- You need granular frame-level analysis
- You want timeline-based OCR extraction
- You don't have or need metadata

For most scam detection use cases, **Holistic Analysis** provides significantly better results by understanding the complete context of the video!
