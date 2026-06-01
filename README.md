# Whisper Transcriber

<div align="center">

**Self-hosted web app for audio and video transcription with NVIDIA GPU**

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-2.x-FF3E00?logo=svelte&logoColor=white)](https://kit.svelte.dev/)
[![faster-whisper](https://img.shields.io/badge/faster--whisper-1.1+-4A90E2)](https://github.com/SYSTRAN/faster-whisper)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Overview

**Whisper Transcriber** is a self-hosted application for automatic transcription of audio and video files — including multi-GB inputs. It runs **Whisper** through **faster-whisper** (CTranslate2) with NVIDIA CUDA acceleration, producing fast and accurate transcripts entirely on your own hardware, without sending data to external services.

### Highlights

- **Resumable uploads** via the tus protocol — no progress lost if the connection drops
- **Real-time transcription progress** streamed over Server-Sent Events
- **5 export formats**: SRT, VTT, TXT, JSON, DOCX
- **Automatic language detection**, or a configurable fixed language
- **Cooperative cancellation** of running jobs
- **UI in Brazilian Portuguese** with light/dark theme

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                     Docker Compose                   │
│                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐  │
│  │ Frontend │───▶│ Backend  │───▶│    Worker    │  │
│  │SvelteKit │    │ FastAPI  │    │ ARQ + Whisper│  │
│  │ :3000    │    │  :8000   │    │   (CUDA)     │  │
│  └──────────┘    └────┬─────┘    └──────────────┘  │
│                       │                              │
│  ┌──────────┐    ┌────▼─────┐                        │
│  │   tusd   │───▶│  Redis   │                        │
│  │  :1080   │    │  :6379   │                        │
│  └──────────┘    └──────────┘                        │
└─────────────────────────────────────────────────────┘
```

| Service   | Stack                               | Role                                        |
|-----------|-------------------------------------|---------------------------------------------|
| frontend  | SvelteKit 2 + Tailwind CSS 4        | User interface                              |
| backend   | FastAPI + SQLModel + SSE            | REST API, job queue, export                 |
| worker    | ARQ + faster-whisper + CTranslate2  | GPU transcription                           |
| redis     | Redis 7                             | Task queue and pub/sub                      |
| tusd      | tus v2.4 (resumable uploads)        | Large-file upload receiver                  |

---

## Prerequisites

- **Linux** (Ubuntu 20.04+ recommended) with Docker Engine ≥ 24 and Docker Compose v2
- **NVIDIA GPU** with an up-to-date driver (tested with CUDA 12.4)
- **NVIDIA Container Toolkit** installed

### Verify GPU access from Docker

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

> If the command fails, run the helper script included in the project:
> ```bash
> bash install-nvidia-toolkit.sh
> ```

---

## Installation and execution

### 1. Clone the repository

```bash
git clone https://github.com/leo-statai/whisper-transcriber.git
cd whisper-transcriber
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` according to your GPU:

| Variable               | Default         | Description                                            |
|------------------------|-----------------|--------------------------------------------------------|
| `WHISPER_MODEL`        | `large-v3`      | Model: `tiny`, `base`, `small`, `medium`, `large-v3`, `large-v3-turbo` |
| `WHISPER_COMPUTE_TYPE` | `float16`       | Precision: `float16` (GPU) or `int8_float16` (less VRAM) |
| `WHISPER_BEAM_SIZE`    | `5`             | Beam search width (higher = more accurate, slower)     |
| `WHISPER_VAD_FILTER`   | `true`          | Silence filter — recommended for long files            |
| `WHISPER_LANGUAGE`     | *(empty)*       | Force a language (`pt`, `en`, `es`…) or leave empty for autodetect |
| `WORKER_CONCURRENCY`   | `1`             | Concurrent jobs (1 for a dedicated GPU)                |

### 3. Start the containers

```bash
docker compose up -d --build
```

> On first boot, the worker downloads the Whisper model (~3 GB for `large-v3`). Follow along with:
> ```bash
> docker compose logs -f worker
> ```

### 4. Open the UI

```
http://localhost:3000
```

On a home server on the local network, replace `localhost` with the machine's IP.

---

## How to use

1. Click **Novo upload** in the top bar
2. Drop an audio or video file (or click to pick) — up to **20 GB**
3. Pick the audio language, or leave **Detectar automaticamente** for auto-detection
4. Click **Iniciar transcrição**
   - Large uploads use the **tus** protocol: if the connection drops, resume by reopening the page
5. Watch the transcript stream live on the job screen
6. When finished, download in the format you want: **SRT · VTT · TXT · JSON · DOCX**

> The UI is currently in Brazilian Portuguese; English localisation is on the roadmap.

---

## REST API

| Method   | Route                                     | Description                                |
|----------|-------------------------------------------|--------------------------------------------|
| `GET`    | `/health`                                 | Health check                               |
| `GET`    | `/jobs`                                   | List all jobs                              |
| `GET`    | `/jobs/{id}`                              | Job details and segments                   |
| `GET`    | `/jobs/{id}/stream`                       | SSE stream of real-time progress           |
| `GET`    | `/jobs/{id}/export?format=srt\|vtt\|txt\|json\|docx` | Download exported file          |
| `POST`   | `/jobs/{id}/cancel`                       | Cancel a running job                       |
| `DELETE` | `/jobs/{id}`                              | Remove job and file from disk              |
| `POST`   | `/tus/hook`                               | Internal tusd webhook                      |

**Uploads** (tus 1.0 protocol): `POST/PATCH/HEAD http://<host>:1080/files/`

---

## Project structure

```
whisper-transcriber/
├── docker-compose.yml          # Orchestration of 5 services
├── .env.example                # Env vars (model, precision, language)
├── install-nvidia-toolkit.sh   # Helper to install the NVIDIA Container Toolkit
│
├── backend/
│   ├── Dockerfile.api          # CUDA + FastAPI (uvicorn) image
│   ├── Dockerfile.worker       # CUDA + ARQ worker image
│   ├── pyproject.toml
│   ├── app/                    # FastAPI: routes, models, exporters (SRT/VTT/TXT/JSON/DOCX)
│   └── worker/                 # transcribe_job task using faster-whisper
│
├── frontend/
│   ├── Dockerfile
│   ├── src/                    # SvelteKit + Tailwind CSS
│   └── ...
│
├── tusd/
│   └── hooks/post-finish       # Script that notifies the backend on upload completion
│
└── data/                       # Persistent volumes (mounted via Docker)
    ├── uploads/                # User-uploaded files
    ├── models/                 # Downloaded Whisper models
    └── transcritor.db          # SQLite DB with jobs and segments
```

---

## Verification and monitoring

### Confirm GPU inside the worker

```bash
docker compose exec worker python -c \
  "from faster_whisper import WhisperModel; \
   m = WhisperModel('tiny', device='cuda'); print('GPU OK')"
```

### Live logs

```bash
docker compose logs -f worker    # Transcription progress
docker compose logs -f backend   # API and hooks
docker compose logs -f tusd      # Uploads
```

### API health check

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `cuDNN missing` / model load failure | cuDNN absent | The base image already ships cuDNN 9 — confirm with `docker compose exec worker bash -c 'find / -name "libcudnn*" 2>/dev/null'` |
| GPU not visible in container | NVIDIA Container Toolkit not configured | Run `bash install-nvidia-toolkit.sh` or follow the [official docs](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) |
| Upload stalls / times out | Very large file, unstable connection | The tus protocol resumes automatically — close and reopen the browser |
| Low VRAM / OOM | Large model on a small GPU | Set `WHISPER_COMPUTE_TYPE=int8_float16` or `WHISPER_MODEL=medium` in `.env` |
| No GPU (CPU only) | Machine without NVIDIA GPU | Remove the `deploy.resources` block from the worker in `docker-compose.yml` and set `WHISPER_COMPUTE_TYPE=int8` |

---

## Tech stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — async REST API
- [ARQ](https://arq-docs.helpmanual.io/) — Redis-backed task queue
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — Whisper optimised via CTranslate2
- [SQLModel](https://sqlmodel.tiangolo.com/) — ORM on top of SQLite
- [sse-starlette](https://github.com/sysid/sse-starlette) — Server-Sent Events

**Frontend**
- [SvelteKit 2](https://kit.svelte.dev/) + [Svelte 5](https://svelte.dev/)
- [Tailwind CSS 4](https://tailwindcss.com/)
- [TanStack Query](https://tanstack.com/query) — data cache and sync
- [tus-js-client](https://github.com/tus/tus-js-client) — resumable uploads
- [Lucide](https://lucide.dev/) — icons

**Infrastructure**
- [Docker Compose](https://docs.docker.com/compose/) — local orchestration
- [tusd](https://github.com/tus/tusd) — tus server for large uploads
- [Redis 7](https://redis.io/) — queue broker

---

## Roadmap

- [ ] Speaker diarisation with [pyannote.audio](https://github.com/pyannote/pyannote-audio)
- [ ] Automatic translation (Whisper's `task="translate"`)
- [ ] In-browser transcript editing
- [ ] Multi-user support with authentication
- [ ] Checkpointing of jobs interrupted mid-transcription
- [ ] English UI localisation

---

## License

Released under the **MIT License**. See [LICENSE](LICENSE) for details.
