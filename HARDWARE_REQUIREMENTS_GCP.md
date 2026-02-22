# OptiScam — Hardware Requirements (Google Cloud Deployment)

**Deployment Target:** Google Cloud Platform + Vercel
**Version:** 1.0

---

## 1. Compute Requirements

### 1.1 Frontend — Vercel (Managed, No Hardware Configuration Required)

| Component | Specification |
|---|---|
| Platform | Vercel Edge Network (managed by Vercel) |
| Runtime | Serverless Node.js (Next.js) |
| Hardware | Abstracted — no user-configurable hardware |
| Configuration | Zero — deployed via `vercel deploy` or git push |

---

### 1.2 Orchestration Layer — Cloud Run (CPU)

The FastAPI REST API is stateless and CPU-bound. It handles HTTP requests, invokes yt-dlp, and communicates with Firestore and Cloud Storage.

| Component | Minimum | Recommended |
|---|---|---|
| Machine type | Cloud Run (2nd gen) | Cloud Run (2nd gen) |
| vCPU per instance | 1 vCPU | 2 vCPU |
| Memory per instance | 512 MB | 1 GB |
| Max instances | 5 | 20 |
| Concurrency per instance | 10 | 20 |
| Region | asia-southeast1 (Singapore) | asia-southeast1 (Singapore) |

> Cloud Run scales to **zero** when idle — no compute cost outside of active requests.

---

### 1.3 Inference Layer — Cloud Run (GPU Worker)

The ML pipeline runs Qwen3-VL-2B (NF4 quantised), Whisper, RapidOCR, and TrOCR. This layer requires a dedicated GPU instance.

| Component | Minimum | Recommended |
|---|---|---|
| Machine type | `g2-standard-4` (L4) | `g2-standard-8` (L4) |
| GPU | NVIDIA L4 (24 GB GDDR6) | NVIDIA L4 (24 GB GDDR6) |
| vCPU | 4 vCPU | 8 vCPU |
| RAM | 16 GB | 32 GB |
| GPU VRAM required | ~2.5 GB (NF4 Qwen3-VL-2B) + ~1 GB (TrOCR + Whisper) ≈ **4 GB total** | Same |
| Boot disk | 20 GB SSD | 50 GB SSD |
| Max instances | 1 | 3 |
| Startup timeout | 300 s (model load from GCS) | 300 s |
| Region | asia-southeast1 (Singapore) | asia-southeast1 (Singapore) |

> **Why L4 over T4:** The NVIDIA L4 offers ~60% faster inference than the T4 for NF4-quantised transformers and supports `bfloat16` natively, reducing numerical errors. The L4 is available on Cloud Run GPU in `g2-standard` machine types.

> **VRAM breakdown:**
> | Model | Quantisation | VRAM |
> |---|---|---|
> | Qwen3-VL-2B-Instruct | NF4 (4-bit) | ~2.5 GB |
> | TrOCR (microsoft/trocr-base-printed) | FP32 | ~0.6 GB |
> | Whisper (tiny) | FP32 | ~0.15 GB |
> | **Total** | | **~3.25 GB** |

---

## 2. Storage Requirements

### 2.1 Cloud Storage (GCS)

| Bucket | Purpose | Estimated Size | Lifecycle Policy |
|---|---|---|---|
| `optiscam-uploads` | Temporary video uploads awaiting analysis | Variable — depends on traffic | Auto-delete after **24 hours** |
| `optiscam-results` | Analysis reports, summary text, CLAHE frame images | ~5–20 MB per job | Retain for **30 days** |
| `optiscam-models` | Cached model weights (Qwen3-VL, TrOCR, Whisper) | ~5 GB (fixed) | No expiry |

### 2.2 Firestore

| Collection | Content | Estimated Document Size |
|---|---|---|
| `jobs` | Job ID, status, verdict, confidence score, text timeline, audio transcript, thumbnail URL | ~5–50 KB per document |
| TTL policy | Documents auto-deleted after **7 days** via Firestore TTL field | — |

---

## 3. Network Requirements

| Requirement | Specification |
|---|---|
| Ingress (user → Vercel) | Public HTTPS — managed by Vercel CDN |
| Ingress (user → Cloud Load Balancer) | Public HTTPS on port 443 |
| Internal (Cloud Run API → GPU Worker) | Via Cloud Pub/Sub push — no direct network path required |
| Internal (Cloud Run → Firestore) | Private Google network — no public IP needed |
| Internal (Cloud Run → Cloud Storage) | Private Google network via VPC Service Controls |
| Egress (GPU Worker → HuggingFace Hub) | Required only on **first deployment** to populate GCS model cache (~5 GB) |
| Egress (API → YouTube/TikTok) | Required for URL-based video download via yt-dlp |

---

## 4. Estimated Cloud Cost (Monthly)

> Estimates based on **moderate usage** (~500 analyses per month, average 2-minute GPU inference per job).

| Service | Usage | Estimated Monthly Cost |
|---|---|---|
| Cloud Run — CPU (API) | ~1,000 requests/month, 1 vCPU, 1 GB RAM | ~$2–5 USD |
| Cloud Run — GPU (L4) | ~500 jobs × 2 min = ~17 GPU-hours/month | ~$10–15 USD |
| Cloud Storage | ~5 GB model cache + ~10 GB results | ~$0.30–1 USD |
| Firestore | ~500 reads + 500 writes/month | < $0.01 USD |
| Cloud Pub/Sub | ~500 messages/month | < $0.01 USD |
| Cloud Load Balancer | 1 forwarding rule | ~$18 USD |
| Vercel | Hobby / Pro plan (frontend) | $0–20 USD |
| **Total** | | **~$30–60 USD / month** |

> Cost scales linearly with usage. The GPU instance is the primary cost driver — it only runs when a job is being processed.

---

## 5. Local Development Hardware Requirements

> Minimum hardware needed to run OptiScam on a local machine (current architecture).

| Component | Minimum | Recommended |
|---|---|---|
| CPU | Intel Core i5 / AMD Ryzen 5 (8th gen+) | Intel Core i7 / AMD Ryzen 7 |
| RAM | 8 GB | 16 GB |
| GPU | NVIDIA GTX 1660 (6 GB VRAM) | NVIDIA RTX 3060 / 4060 (8–12 GB VRAM) |
| VRAM | 4 GB (NF4 quantisation) | 8 GB |
| Storage | 20 GB free (models + outputs) | 50 GB SSD |
| OS | Windows 10/11, Ubuntu 20.04+, macOS 12+ | Ubuntu 22.04 / Windows 11 |
| CUDA | 12.1+ | 12.6 |
| Python | 3.10+ | 3.11+ |
