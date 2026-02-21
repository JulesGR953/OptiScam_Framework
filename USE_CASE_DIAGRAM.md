# OptiScam — Use Case Diagram

```plantuml
@startuml OptiScam_UseCaseDiagram

skinparam backgroundColor #050510
skinparam actorStyle awesome

skinparam actor {
    BackgroundColor #1a1040
    BorderColor #7c3aed
    FontColor #e2e8f0
}

skinparam usecase {
    BackgroundColor #0f172a
    BorderColor #6366f1
    FontColor #e2e8f0
    ArrowColor #ec4899
}

skinparam rectangle {
    BackgroundColor #0a0620
    BorderColor #4c1d95
    FontColor #c4b5fd
}

' ─── Actors ──────────────────────────────────────────────────────────────────
actor "User"            as USER
actor "YouTube / TikTok\nPlatform"  as PLATFORM   #Orange
actor "Qwen3-VL-2B\nModel"          as QWEN        #Cyan
actor "Whisper\nModel"              as WHISPER     #Green
actor "RapidOCR /\nTrOCR"          as OCR         #Pink

' ─── System boundary ─────────────────────────────────────────────────────────
rectangle "OptiScam System" {

    ' ── Primary use cases ──
    usecase "Upload Video File"             as UC_UPLOAD
    usecase "Paste YouTube / TikTok Link"   as UC_LINK
    usecase "Enter Video Title"             as UC_TITLE
    usecase "Enter Video Description"       as UC_DESC
    usecase "Toggle Holistic Mode"          as UC_HOLISTIC
    usecase "Submit for Analysis"           as UC_SUBMIT
    usecase "View Analysis Results"         as UC_RESULTS
    usecase "View Audio Transcript"         as UC_TRANSCRIPT
    usecase "View OCR Text Timeline"        as UC_OCR_VIEW
    usecase "Analyze Another Video"         as UC_RESET

    ' ── System use cases ──
    usecase "Validate Video / Metadata"     as UC_VALIDATE
    usecase "Download Video via yt-dlp"     as UC_DOWNLOAD
    usecase "Extract Frames (CLAHE)"        as UC_FRAMES
    usecase "Transcribe Audio"              as UC_AUDIO
    usecase "Extract On-Screen Text"        as UC_TEXT
    usecase "Apply TrOCR Fallback\n(< 80% confidence)" as UC_TROCR
    usecase "Classify Video\n(Scam / Not Scam)"         as UC_CLASSIFY
    usecase "Generate Verdict + Reasoning"  as UC_VERDICT
    usecase "Show Thumbnail Preview"        as UC_THUMBNAIL
    usecase "Poll Job Status"               as UC_POLL
}

' ─── User associations ───────────────────────────────────────────────────────
USER --> UC_UPLOAD
USER --> UC_LINK
USER --> UC_TITLE
USER --> UC_DESC
USER --> UC_HOLISTIC
USER --> UC_SUBMIT
USER --> UC_RESULTS
USER --> UC_TRANSCRIPT
USER --> UC_OCR_VIEW
USER --> UC_RESET

' ─── System internal associations ────────────────────────────────────────────
UC_SUBMIT       ..> UC_VALIDATE    : <<include>>
UC_VALIDATE     ..> UC_DOWNLOAD    : <<include>>\n[if URL]
UC_VALIDATE     ..> UC_FRAMES      : <<include>>
UC_FRAMES       ..> UC_TEXT        : <<include>>
UC_FRAMES       ..> UC_AUDIO       : <<include>>
UC_TEXT         ..> UC_TROCR       : <<extend>>\n[conf < 80%]
UC_FRAMES       ..> UC_CLASSIFY    : <<include>>
UC_CLASSIFY     ..> UC_VERDICT     : <<include>>
UC_SUBMIT       ..> UC_POLL        : <<include>>
UC_LINK         ..> UC_THUMBNAIL   : <<extend>>
UC_UPLOAD       ..> UC_THUMBNAIL   : <<extend>>

' ─── External actor associations ─────────────────────────────────────────────
PLATFORM    --> UC_DOWNLOAD
QWEN        --> UC_CLASSIFY
WHISPER     --> UC_AUDIO
OCR         --> UC_TEXT
OCR         --> UC_TROCR

@enduml
```

---

> **Tip — render this diagram:**
> - **VS Code**: install the *PlantUML* extension → right-click → *Preview Current Diagram*
> - **Online**: paste the `@startuml … @enduml` block at [plantuml.com/plantuml](https://www.plantuml.com/plantuml/uml/)

---

## Use Case Descriptions

### Primary Actor — User

| Use Case | Description |
|---|---|
| Upload Video File | Drag-and-drop or browse for a local MP4 / MOV / AVI / MKV / WebM file |
| Paste YouTube / TikTok Link | Enter a public URL; yt-dlp fetches the video, title, and description automatically |
| Enter Video Title | Optional free-text — passed directly into the model prompt to improve accuracy |
| Enter Video Description | Optional free-text — same purpose as title |
| Toggle Holistic Mode | Switches to a lower frame rate suitable for longer videos |
| Submit for Analysis | Triggers the full backend pipeline |
| View Analysis Results | Sees the Scam / Not Scam verdict plus 4–5 sentence AI reasoning |
| View Audio Transcript | Expands the collapsible Whisper transcript panel |
| View OCR Text Timeline | Expands the collapsible per-frame text detection panel |
| Analyze Another Video | Resets the UI to start a new job |

### Secondary Actors — AI Models / Platform

| Actor | Role |
|---|---|
| YouTube / TikTok Platform | Source of video, title, description, and thumbnail via yt-dlp |
| Qwen3-VL-2B Model | Multi-modal vision-language model — produces the final verdict |
| Whisper Model | OpenAI speech-to-text — transcribes the video audio track |
| RapidOCR / TrOCR | Detects on-screen text in frames; TrOCR activates when RapidOCR confidence < 80 % |

### Include / Extend relationships

| Relationship | Type | Condition |
|---|---|---|
| Submit → Validate Video | `<<include>>` | Always |
| Validate → Download via yt-dlp | `<<include>>` | Only when a URL was pasted |
| Validate → Extract Frames | `<<include>>` | Always |
| Extract Frames → Transcribe Audio | `<<include>>` | Always |
| Extract Frames → Extract Text | `<<include>>` | Always |
| Extract Text → TrOCR Fallback | `<<extend>>` | Only when RapidOCR confidence < 80 % |
| Extract Frames → Classify Video | `<<include>>` | Always |
| Classify Video → Generate Verdict | `<<include>>` | Always |
| Submit → Poll Job Status | `<<include>>` | Always (every 3 s until done) |
| Paste Link → Show Thumbnail | `<<extend>>` | When a valid YouTube URL is detected |
| Upload File → Show Thumbnail | `<<extend>>` | First frame captured via HTML5 video API |
