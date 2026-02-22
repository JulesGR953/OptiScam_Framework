# OptiScam — Front-End Software Requirements Specification

**System:** OptiScam Web Interface
**Technology:** Next.js 14 · React · TypeScript · Tailwind CSS
**Version:** 1.0

---

## 1. Functional Requirements

### 1.1 Video Input

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | The system shall allow the user to submit a video through two mutually exclusive input modes: **file upload** and **platform URL**. | High |
| FR-02 | In file upload mode, the system shall accept video files in the formats MP4, MOV, AVI, MKV, and WebM via a drag-and-drop zone or a file picker dialog. | High |
| FR-03 | In URL mode, the system shall accept YouTube and TikTok URLs entered via a text input field. | High |
| FR-04 | The system shall allow the user to optionally provide a **video title** and **video description** when uploading a local file, to improve classification accuracy. | Medium |
| FR-05 | The system shall provide a **Holistic Mode** toggle that, when enabled, instructs the backend to sample frames at a lower rate suited to longer videos. | Medium |

### 1.2 Thumbnail Preview

| ID | Requirement | Priority |
|---|---|---|
| FR-06 | When a local video file is selected, the system shall automatically capture and display the first frame of the video as a thumbnail preview using the HTML5 Canvas API. | Medium |
| FR-07 | When a YouTube URL is entered, the system shall automatically derive and display the video thumbnail from the YouTube image CDN without requiring a separate API call. | Medium |
| FR-08 | When a TikTok URL is submitted, the system shall retrieve and display the video thumbnail returned by the backend after yt-dlp extraction. | Medium |
| FR-09 | The user shall be able to dismiss the thumbnail preview at any time before submission. | Low |

### 1.3 Job Submission and Status Tracking

| ID | Requirement | Priority |
|---|---|---|
| FR-10 | Upon submission, the system shall send the video or URL to the backend via an HTTP POST request and receive a unique **job ID** in response. | High |
| FR-11 | The system shall poll the backend for job status using the job ID at a fixed interval of **3 seconds** until the job reaches a terminal state (`done` or `error`). | High |
| FR-12 | The system shall display a distinct loading state for each of the following job statuses: **Uploading**, **Queued**, **Downloading** (URL mode), and **Analyzing**. | High |
| FR-13 | The system shall display the video thumbnail with a loading spinner overlay during the analysis phase, if a thumbnail is available. | Medium |

### 1.4 Results Display

| ID | Requirement | Priority |
|---|---|---|
| FR-14 | Upon job completion, the system shall display a **verdict banner** indicating whether the video is classified as a **Scam** or **Legitimate**. | High |
| FR-15 | The verdict banner shall be visually distinguished: red styling for a Scam verdict and green styling for a Legitimate verdict. | High |
| FR-16 | The system shall display the **model confidence score** (0–100%) derived from the model's internal logit probabilities, alongside a colour-coded progress bar. | High |
| FR-17 | The confidence progress bar shall use red colouring for confidence ≥ 80% on a Scam verdict, green for confidence ≥ 80% on a Legitimate verdict, and yellow for confidence between 50% and 79%. | Medium |
| FR-18 | The system shall display the **model reasoning** text (4–5 sentences) below the confidence meter. | High |
| FR-19 | The system shall display the **audio transcript** in a collapsible card, showing the detected language and number of segments. | Medium |
| FR-20 | The system shall display **OCR-detected text** organised by timestamp in a collapsible, scrollable card, showing the extraction method (RapidOCR or TrOCR) and confidence per region. | Medium |
| FR-21 | The system shall display an **Analysis Details** summary panel containing: frames analysed, confidence score, OCR detection count, and audio segment count. | Medium |
| FR-22 | The thumbnail shall be displayed within the verdict banner upon result delivery, if available. | Low |

### 1.5 Error Handling and Reset

| ID | Requirement | Priority |
|---|---|---|
| FR-23 | If the backend returns an error status or the polling connection is lost, the system shall display a descriptive error message to the user. | High |
| FR-24 | The system shall provide a **Cancel** button during analysis that stops polling and returns the interface to the idle state. | Medium |
| FR-25 | The system shall provide an **Analyze Another Video** button on the results screen that resets all state and returns to the input form. | High |

---

## 2. Non-Functional Requirements

### 2.1 Performance

| ID | Requirement |
|---|---|
| NFR-01 | The web interface shall load and become interactive within 3 seconds on a standard broadband connection. |
| NFR-02 | The polling mechanism shall not degrade browser performance; polling requests shall be lightweight (JSON, < 1 KB response). |
| NFR-03 | Thumbnail capture from a local video file shall complete within 2 seconds of file selection. |

### 2.2 Usability

| ID | Requirement |
|---|---|
| NFR-04 | The interface shall be fully usable on desktop screen widths of 1024 px and above. |
| NFR-05 | All interactive elements (buttons, toggles, inputs) shall have visible focus states to support keyboard navigation. |
| NFR-06 | Status labels shall use plain language (e.g., "Downloading video from the internet…") rather than raw status codes. |
| NFR-07 | The input mode toggle (Upload / Link) shall switch immediately without page reload. |

### 2.3 Security

| ID | Requirement |
|---|---|
| NFR-08 | All API requests from the frontend shall be sent to the backend through a same-origin reverse proxy (`/api/*`), preventing direct cross-origin exposure of the backend port. |
| NFR-09 | The frontend shall not store video files, URLs, or analysis results in browser local storage or cookies. |
| NFR-10 | The `NEXT_PUBLIC_BACKEND_URL` environment variable shall be the only configurable endpoint; no backend addresses shall be hardcoded in production builds. |

### 2.4 Reliability

| ID | Requirement |
|---|---|
| NFR-11 | If a polling request fails due to a network error, the system shall display an error message rather than silently retrying indefinitely. |
| NFR-12 | The frontend shall handle `null` or `undefined` values for optional result fields (confidence score, audio transcript, OCR data) without crashing. |

---

## 3. User Interface Requirements

| ID | Requirement |
|---|---|
| UI-01 | The interface shall use a dark colour scheme consistent with the OptiScam visual identity (deep navy/black background, purple and pink accent colours). |
| UI-02 | The header shall display the OptiScam logo and an "AI Ready" indicator confirming backend connectivity. |
| UI-03 | The input form shall be presented in a single card component occupying the centre of the page, with a maximum width of 896 px. |
| UI-04 | The results section shall be presented as a vertical stack of cards below the input area, with smooth slide-up animations on appearance. |
| UI-05 | The verdict banner card shall be the topmost result card and shall be the largest and most visually prominent element on the results screen. |

---

## 4. System Constraints

| ID | Constraint |
|---|---|
| SC-01 | The frontend is built with **Next.js 14** and must be deployed on **Vercel** or run locally via `npm run dev`. |
| SC-02 | The frontend communicates exclusively with the backend REST API; it does not call the YouTube, TikTok, or HuggingFace APIs directly. |
| SC-03 | The frontend does not perform any ML inference; all analysis is delegated to the backend pipeline. |
| SC-04 | Supported browsers: Google Chrome 110+, Mozilla Firefox 110+, Microsoft Edge 110+, Safari 16+. |
