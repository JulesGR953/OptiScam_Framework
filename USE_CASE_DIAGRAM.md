# OptiScam — Use Case Diagram

```plantuml
@startuml OptiScam_UseCaseDiagram

skinparam actorStyle stick
skinparam backgroundColor White

skinparam usecase {
    BackgroundColor White
    BorderColor Black
    FontColor Black
    FontSize 12
}

skinparam rectangle {
    BackgroundColor White
    BorderColor Black
    FontColor Black
    FontSize 11
}

skinparam arrow {
    Color Black
    FontColor Black
    FontSize 10
}

' ─── Actors ──────────────────────────────────────────────────────────────────
actor "User" as USER

' ─── External systems (outside boundary) ─────────────────────────────────────
rectangle "CLAHE\npipeline" as CLAHE
rectangle "Qwen3-VL"        as QWEN
rectangle "Backend"         as BACKEND
actor     "Administrator"   as ADMIN

' ─── System boundary ─────────────────────────────────────────────────────────
rectangle "OptiScam System" {

    usecase "Home page"                         as UC_HOME
    usecase "Video upload,\nmanual metadata input" as UC_UPLOAD
    usecase "Link submission"                   as UC_LINK
    usecase "Pre Processing"                    as UC_PRE
    usecase "Frame Sampling"                    as UC_FRAME
    usecase "Reasoning"                         as UC_REASON
    usecase "Scam Inference"                    as UC_INFER
    usecase "Confidence Score"                  as UC_CONF
    usecase "Output analysis"                   as UC_OUT
    usecase "Performance metrics"               as UC_PERF

}

' ─── User → system ───────────────────────────────────────────────────────────
USER --> UC_HOME
USER --> UC_REASON
USER --> UC_INFER
USER --> UC_CONF

' ─── Internal flow (<<Include>>) ─────────────────────────────────────────────
UC_HOME   ..> UC_UPLOAD : <<Include>>
UC_HOME   --> UC_LINK

UC_UPLOAD ..> UC_PRE    : <<Include>>
UC_LINK   ..> UC_PRE    : <<Include>>

UC_PRE    ..> UC_FRAME  : <<Include>>
UC_FRAME  ..> UC_REASON : <<Include>>
UC_REASON ..> UC_INFER  : <<Include>>
UC_INFER  ..> UC_CONF   : <<Include>>

UC_CONF   --> UC_OUT
UC_CONF   --> UC_PERF

' ─── External system connections ─────────────────────────────────────────────
CLAHE  --  UC_PRE
QWEN   --  UC_REASON

UC_OUT  --> BACKEND
UC_OUT  --> ADMIN
UC_PERF --> ADMIN

@enduml
```

---

> **Render this diagram:**
> - **VS Code** → install *PlantUML* extension → right-click → *Preview Current Diagram*
> - **Online** → paste the `@startuml … @enduml` block at [plantuml.com/plantuml](https://www.plantuml.com/plantuml/uml/)

---

## Use Case Table

| # | Use Case | Actor(s) | Description |
|---|---|---|---|
| 1 | Home page | User | Entry point — choose upload or link submission |
| 2 | Video upload, manual metadata input | User | Upload a local video file + optional title & description |
| 3 | Link submission | User | Paste a YouTube or TikTok URL |
| 4 | Pre Processing | System, CLAHE pipeline | Frame extraction with sharpness filtering + CLAHE contrast enhancement |
| 5 | Frame Sampling | System | Evenly subsample up to 6 representative frames |
| 6 | Reasoning | User, System, Qwen3-VL | Multi-modal inference — frames + title + description → model output |
| 7 | Scam Inference | User, System | Parse model output → Yes / No verdict |
| 8 | Confidence Score | User, System | Derive confidence from model reasoning |
| 9 | Output analysis | System, Backend, Administrator | Persist results (JSON report, summary.txt) |
| 10 | Performance metrics | System, Administrator | Log frame count, OCR detections, audio segments, language |

## Relationships

| Relationship | Type | Notes |
|---|---|---|
| Home page → Video upload | `<<Include>>` | Always available from home |
| Home page → Link submission | association | Alternative input path |
| Video upload / Link → Pre Processing | `<<Include>>` | Both paths merge here |
| Pre Processing ↔ CLAHE pipeline | association | CLAHE is an external processing component |
| Pre Processing → Frame Sampling | `<<Include>>` | |
| Frame Sampling → Reasoning | `<<Include>>` | |
| Reasoning ↔ Qwen3-VL | association | External model actor |
| Reasoning → Scam Inference | `<<Include>>` | |
| Scam Inference → Confidence Score | `<<Include>>` | |
| Confidence Score → Output analysis | association | |
| Confidence Score → Performance metrics | association | |
| Output analysis → Backend / Administrator | association | Results stored and reviewed |
| Performance metrics → Administrator | association | Monitoring |
