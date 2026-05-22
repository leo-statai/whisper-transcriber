# Transcritor v2

<div align="center">

**Aplicação web local para transcrição de áudio e vídeo com GPU NVIDIA**

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-2.x-FF3E00?logo=svelte&logoColor=white)](https://kit.svelte.dev/)
[![faster-whisper](https://img.shields.io/badge/faster--whisper-1.1+-4A90E2)](https://github.com/SYSTRAN/faster-whisper)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Visão Geral

O **Transcritor v2** é uma aplicação self-hosted para transcrição automática de arquivos de áudio e vídeo, incluindo arquivos de vários GB. Usa o modelo **Whisper** via **faster-whisper** (CTranslate2) com aceleração NVIDIA CUDA para transcrição rápida e precisa diretamente na sua máquina — sem enviar dados para serviços externos.

### Destaques

- **Uploads resumíveis** via protocolo tus — sem perder progresso se a conexão cair
- **Streaming em tempo real** do progresso da transcrição via Server-Sent Events
- **5 formatos de exportação**: SRT, VTT, TXT, JSON, DOCX
- **Detecção automática de idioma** ou idioma fixo configurável
- **Cancelamento cooperativo** de jobs em andamento
- **Interface em pt-BR** com tema claro/escuro

---

## Arquitetura

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

| Serviço   | Tecnologia                          | Função                                    |
|-----------|-------------------------------------|-------------------------------------------|
| frontend  | SvelteKit 2 + Tailwind CSS 4        | Interface do usuário                      |
| backend   | FastAPI + SQLModel + SSE            | API REST, fila de jobs, exportação        |
| worker    | ARQ + faster-whisper + CTranslate2  | Transcrição com GPU                       |
| redis     | Redis 7                             | Fila de tarefas e pub/sub                 |
| tusd      | tus v2.4 (uploads resumíveis)       | Recepção de arquivos grandes              |

---

## Pré-requisitos

- **Linux** (Ubuntu 20.04+ recomendado) com Docker Engine ≥ 24 e Docker Compose v2
- **GPU NVIDIA** com driver atualizado (testado com CUDA 12.4)
- **NVIDIA Container Toolkit** instalado

### Verificar se a GPU está disponível no Docker

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

> Se o comando falhar, execute o script auxiliar incluído no projeto:
> ```bash
> bash install-nvidia-toolkit.sh
> ```

---

## Instalação e Execução

### 1. Clone o repositório

```bash
git clone https://github.com/leo-statai/transcritor_v2.git
cd transcritor_v2
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` conforme sua GPU:

| Variável               | Padrão          | Descrição                                              |
|------------------------|-----------------|--------------------------------------------------------|
| `WHISPER_MODEL`        | `large-v3`      | Modelo: `tiny`, `base`, `small`, `medium`, `large-v3`, `large-v3-turbo` |
| `WHISPER_COMPUTE_TYPE` | `float16`       | Precisão: `float16` (GPU) ou `int8_float16` (menos VRAM) |
| `WHISPER_BEAM_SIZE`    | `5`             | Beam search (maior = mais preciso, mais lento)         |
| `WHISPER_VAD_FILTER`   | `true`          | Filtro de silêncio — recomendado para arquivos longos  |
| `WHISPER_LANGUAGE`     | *(vazio)*       | Forçar idioma (`pt`, `en`, `es`...) ou deixar vazio para autodetect |
| `WORKER_CONCURRENCY`   | `1`             | Jobs simultâneos (1 para GPU dedicada)                 |

### 3. Suba os contêineres

```bash
docker compose up -d --build
```

> No primeiro boot, o worker baixa o modelo Whisper (~3 GB para `large-v3`). Acompanhe com:
> ```bash
> docker compose logs -f worker
> ```

### 4. Acesse a interface

```
http://localhost:3000
```

Em um home server na rede local, substitua `localhost` pelo IP da máquina.

---

## Como Usar

1. Clique em **Novo upload** na barra superior
2. Arraste um arquivo de áudio ou vídeo (ou clique para selecionar) — até **20 GB**
3. Escolha o idioma do áudio, ou deixe em **Detectar automaticamente**
4. Clique em **Iniciar transcrição**
   - Uploads grandes usam o protocolo **tus**: se a conexão cair, retome reabrindo a página
5. Acompanhe a transcrição rolando em tempo real na tela do job
6. Ao concluir, baixe no formato desejado: **SRT · VTT · TXT · JSON · DOCX**

---

## API REST

| Método   | Rota                                      | Descrição                              |
|----------|-------------------------------------------|----------------------------------------|
| `GET`    | `/health`                                 | Health check                           |
| `GET`    | `/jobs`                                   | Lista todos os jobs                    |
| `GET`    | `/jobs/{id}`                              | Detalhes e segmentos de um job         |
| `GET`    | `/jobs/{id}/stream`                       | SSE com progresso em tempo real        |
| `GET`    | `/jobs/{id}/export?format=srt\|vtt\|txt\|json\|docx` | Download do arquivo exportado |
| `POST`   | `/jobs/{id}/cancel`                       | Cancela um job em execução             |
| `DELETE` | `/jobs/{id}`                              | Remove job e arquivo do disco          |
| `POST`   | `/tus/hook`                               | Webhook interno do tusd                |

**Uploads** (protocolo tus 1.0): `POST/PATCH/HEAD http://<host>:1080/files/`

---

## Estrutura do Projeto

```
transcritor_v2/
├── docker-compose.yml          # Orquestração dos 5 serviços
├── .env.example                # Variáveis de ambiente (modelo, precisão, idioma)
├── install-nvidia-toolkit.sh   # Helper para instalar o NVIDIA Container Toolkit
│
├── backend/
│   ├── Dockerfile.api          # Imagem CUDA + FastAPI (uvicorn)
│   ├── Dockerfile.worker       # Imagem CUDA + ARQ worker
│   ├── pyproject.toml
│   ├── app/                    # FastAPI: rotas, modelos, exportadores (SRT/VTT/TXT/JSON/DOCX)
│   └── worker/                 # Tarefa transcribe_job com faster-whisper
│
├── frontend/
│   ├── Dockerfile
│   ├── src/                    # SvelteKit + Tailwind CSS
│   └── ...
│
├── tusd/
│   └── hooks/post-finish       # Script que notifica o backend ao terminar upload
│
└── data/                       # Volumes persistentes (montados no Docker)
    ├── uploads/                # Arquivos enviados pelo usuário
    ├── models/                 # Modelos Whisper baixados
    └── transcritor.db          # Banco SQLite com jobs e segmentos
```

---

## Verificações e Monitoramento

### Confirmar GPU dentro do worker

```bash
docker compose exec worker python -c \
  "from faster_whisper import WhisperModel; \
   m = WhisperModel('tiny', device='cuda'); print('GPU OK')"
```

### Logs em tempo real

```bash
docker compose logs -f worker    # Progresso das transcrições
docker compose logs -f backend   # API e hooks
docker compose logs -f tusd      # Uploads
```

### Health check da API

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## Solução de Problemas

| Sintoma | Causa provável | Solução |
|---------|---------------|---------|
| `cuDNN missing` / falha ao carregar modelo | cuDNN ausente | A imagem base já inclui cuDNN 9 — confirme com `docker compose exec worker bash -c 'find / -name "libcudnn*" 2>/dev/null'` |
| GPU não visível no container | NVIDIA Container Toolkit não configurado | Execute `bash install-nvidia-toolkit.sh` ou siga a [documentação oficial](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) |
| Upload trava / timeout | Arquivo muito grande, conexão instável | O protocolo tus retoma automaticamente — feche e reabra o navegador |
| Pouca VRAM / OOM | Modelo grande + GPU com pouca memória | Ajuste `WHISPER_COMPUTE_TYPE=int8_float16` ou `WHISPER_MODEL=medium` no `.env` |
| Sem GPU (CPU only) | Máquina sem GPU NVIDIA | Remova o bloco `deploy.resources` do worker no `docker-compose.yml` e defina `WHISPER_COMPUTE_TYPE=int8` |

---

## Stack de Tecnologias

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — API REST assíncrona
- [ARQ](https://arq-docs.helpmanual.io/) — Fila de tasks com Redis
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — Whisper otimizado com CTranslate2
- [SQLModel](https://sqlmodel.tiangolo.com/) — ORM sobre SQLite
- [sse-starlette](https://github.com/sysid/sse-starlette) — Server-Sent Events

**Frontend**
- [SvelteKit 2](https://kit.svelte.dev/) + [Svelte 5](https://svelte.dev/)
- [Tailwind CSS 4](https://tailwindcss.com/)
- [TanStack Query](https://tanstack.com/query) — Cache e sincronização de dados
- [tus-js-client](https://github.com/tus/tus-js-client) — Uploads resumíveis
- [Lucide](https://lucide.dev/) — Ícones

**Infraestrutura**
- [Docker Compose](https://docs.docker.com/compose/) — Orquestração local
- [tusd](https://github.com/tus/tusd) — Servidor tus para uploads grandes
- [Redis 7](https://redis.io/) — Broker de filas

---

## Roadmap

- [ ] Diarização de falantes com [pyannote.audio](https://github.com/pyannote/pyannote-audio)
- [ ] Tradução automática (`task="translate"` do Whisper)
- [ ] Edição manual de transcrições no navegador
- [ ] Suporte multi-usuário com autenticação
- [ ] Checkpointing de jobs interrompidos no meio da transcrição

---

## Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
