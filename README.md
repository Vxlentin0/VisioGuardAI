# 🛡️ VisioGuardAI

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)  
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)  
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)  
[![Security](https://img.shields.io/badge/security-enabled-brightgreen.svg)](https://github.com/Vxlentin0/VisioGuardAI)

> An AI-powered cybersecurity threat detection system using computer vision and machine learning to identify and analyze potential security threats in real-time.

---

## 📋 Table of Contents

- [Overview](#-overview)  
- [Features](#-features)  
- [Architecture](#-architecture)  
- [Prerequisites](#-prerequisites)  
- [Installation](#-installation)  
- [Configuration](#-configuration)  
- [Usage](#-usage)  
- [API Documentation](#-api-documentation)  
- [Security](#-security)  
- [Project Structure](#-project-structure)  
- [Development](#-development)  
- [Troubleshooting](#-troubleshooting)  
- [Contributing](#-contributing)  
- [License](#-license)  
- [Contact](#-contact)

---

## 🔍 Overview

**VisioGuardAI** is a cutting-edge cybersecurity solution that leverages artificial intelligence and computer vision to detect, analyze, and respond to security threats. The system processes images and video feeds in (near) real time, identifying potential threats using configurable, modular machine learning models. It is API-first and designed to be deployed locally or in containerized/cloud environments.

---

## ✨ Features

### Core Functionality

- 🎯 **AI-Powered Detection** — TensorFlow and/or PyTorch-based models for threat detection and classification.  
- 📸 **Image & Video Processing** — OpenCV and Pillow for preprocessing, augmentation and postprocessing.  
- 🔐 **Secure API** — API key authentication, encryption, rate limiting and logging.  
- 🔄 **API Key Rotation** — Scripted rotation utilities (see `scripts/rotate_api_keys.py`) for safer credential handling.  
- 📊 **Analytics & Metadata** — Detection confidence, bounding boxes, timestamps and optional storage of results.  
- 🐳 **Docker Ready** — `Dockerfile` and recommended compose patterns for containerized deployment.

### Technical Features

- **FastAPI** — Async-first API for low-latency inference endpoints.  
- **Pluggable Model Backends** — Swap or add model implementations without touching routing logic.  
- **Fernet / Cryptography** — Symmetric encryption for sensitive config and tokens.  
- **Modular Codebase** — Clear split between `app/` (API), `models/` (model artifacts), and `scripts/` (tools).  
- **Comprehensive Logging & Error Handling** — Structured logs and graceful exception handling.

---

## 🏗️ Architecture

VisioGuardAI is organized as a set of modular components so teams can replace or extend parts independently:

- Client layer: dashboards, cameras, and integration scripts (push data to the API).  
- API layer (FastAPI): receives images/frames, authenticates requests, queues inference, and returns structured responses.  
- Inference layer: one or more model handlers (PyTorch/TensorFlow) that preprocess, run inference, and postprocess outputs.  
- Persistence/Store: optional results database (SQLite by default for API-keys/metadata, extendable to PostgreSQL) and object storage for larger artifacts.  
- Utilities: key rotation, onboarding scripts, Docker build, and CI hooks.

Sequence (simplified): client → FastAPI endpoint → auth & rate-limit → model handler → results → response + optional persistence.

---

## ✅ Prerequisites

- OS: Windows, macOS or Linux (examples below use Windows PowerShell).  
- Python: 3.8+ (3.8–3.12 supported; check specific packages like TensorFlow for compatibility).  
- Git (for cloning).  
- Docker (optional, for containerized deployment).  
- If using GPU acceleration: NVIDIA driver and matching CUDA toolkit (follow PyTorch / TensorFlow docs).

Recommended local isolation: Python virtual environment (`venv`) or conda environment.

---

## ⚙️ Installation

Below are concise, recommended steps for Windows (PowerShell). Adapt for macOS/Linux (use `source .venv/bin/activate`).

1. Clone the repository and enter it:

```powershell
git clone https://github.com/Vxlentin0/VisioGuardAI.git
cd VisioGuardAI
```

2. Create and activate a virtual environment:

```powershell
python -m venv .venv
# PowerShell:
.\.venv\Scripts\Activate.ps1
```

3. Upgrade packaging tooling:

```powershell
python -m pip install --upgrade pip setuptools wheel
```

4. Install core dependencies (grouped to reduce conflicts). If a `requirements.txt` exists, prefer:

```powershell
python -m pip install -r requirements.txt
```

If not, install core groups:

```powershell
# web / api
python -m pip install fastapi uvicorn[standard] starlette

# data & ML basics
python -m pip install numpy pandas scikit-learn matplotlib Pillow opencv-python

# transformers / models
python -m pip install transformers

# deep learning (choose appropriate command for PyTorch / TensorFlow)
# CPU-only PyTorch example (adjust per https://pytorch.org)
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
# TensorFlow (if needed) — check compatibility with your Python version
python -m pip install tensorflow
```

Notes:
- GPU-enabled installs for PyTorch/TensorFlow require matching drivers and possibly different wheel URLs. See the PyTorch/TensorFlow official instructions.
- Some packages (audio, system-level bindings) may need extra system libraries or binary wheels.

---

## 🔧 Configuration

- `.env`: recommended to store runtime settings (do NOT commit secrets).  
- `config/` or `app/settings.py`: project-level configuration (see code for exact filename).  
- API keys: managed via SQLite by default (see `app/`), and rotation helpers are in `scripts/`.

Example `.env` (store at repo root):

```
# .env example
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
ENV=development
API_KEY_DB=./data/api_keys.db
FERNET_KEY=<base64_fernet_key>
```

Generate a Fernet key for encryption:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Place the key into `.env` as `FERNET_KEY`.

---

## ▶️ Usage

### Run the API locally (development)

Assuming `app.main:app` is the FastAPI application:

```powershell
# Activate venv first
.\.venv\Scripts\Activate.ps1

# Run auto-reload development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for interactive Swagger UI. For production, use a proper ASGI server setup and reverse proxy.

### Example: call an inference endpoint (PowerShell)

```powershell
$imgPath = "examples/test.jpg"
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/infer" -Method Post -InFile $imgPath -ContentType "multipart/form-data"
```

Or with curl:

```bash
curl -X POST "http://localhost:8000/api/v1/infer" -F "file=@examples/test.jpg" -H "x-api-key: <YOUR_API_KEY>"
```

Responses typically include: detection classes, confidence scores, bounding boxes and optional metadata.

---

## 📘 API Documentation

- Interactive docs: `GET /docs` (Swagger UI)  
- OpenAPI JSON: `GET /openapi.json`  

Typical endpoints (examples — confirm exact routes in `app/`):

- `POST /api/v1/infer` — send an image/frame for inference  
- `GET /api/v1/models` — list available models and versions  
- `POST /api/v1/keys` — create API key (admin)  
- `POST /api/v1/rotate-keys` — trigger rotation script (admin)  

Check the code in `app/` for exact parameter names and example payloads.

---

## 🔒 Security

- Never commit secrets or private keys. Use `.env` or secret managers.  
- Use HTTPS in production. Configure TLS termination at the proxy/load-balancer (NGINX/Caddy).  
- API keys are stored encrypted with Fernet; rotate regularly using `scripts/rotate_api_keys.py`.  
- Rate limiting is recommended — use middleware or an API gateway (e.g., Cloudflare, Kong).  
- Audit logs for suspicious activity — persist logs to a secured store and monitor.  
- Keep dependencies up to date; run `pip list --outdated` and CI checks.

---

## 🗂️ Project Structure

A conventional structure (your repo may vary):

```
VisioGuardAI/
├─ app/                    # FastAPI application (routes, models, services)
│  ├─ main.py
│  ├─ api/
│  ├─ services/
│  └─ settings.py
├─ scripts/                # Helper scripts (rotate_api_keys.py, maintenance)
├─ models/                 # Binary model artifacts (not usually checked in)
├─ data/                   # Example data, small sample inputs
├─ Dockerfile
├─ requirements.txt
├─ README.md / README.txt
└─ .env (not checked in)
```

Files you will commonly edit:
- `app/main.py` or `app/__init__.py` — application entry.
- `scripts/rotate_api_keys.py` — key rotation tool.
- `requirements.txt` — pinned dependencies for reproducible installs.

---

## 🛠️ Development

Developer workflow suggestions:

- Create feature branches, keep PRs small and focused.  
- Tests: add unit/integration tests under `tests/` and run with `pytest`.  
- Lint: use `flake8` or `ruff`; format with `black`.  
- Pre-commit hooks: recommended for consistent formatting and lightweight checks.

Example local dev commands:

```powershell
# activate venv
.\.venv\Scripts\Activate.ps1

# run tests
pytest -q

# run the app (dev)
uvicorn app.main:app --reload
```

Add a `make` or `tasks.json` for common commands if desired.

---

## 🔎 Troubleshooting

Common install/run issues and how to resolve them:

1. Missing imports after `pip install`:
   - Ensure the active interpreter in VS Code points to your virtual environment (`.venv\Scripts\python.exe`). Use Command Palette → *Python: Select Interpreter*.  
   - Activate the venv in your shell before running scripts.  
   - Upgrade pip/setuptools/wheel:
     ```powershell
     python -m pip install --upgrade pip setuptools wheel
     ```

2. Package installation fails (compiled extensions or wheels):
   - Install in smaller groups to isolate failing package.  
   - For `cryptography`, `opencv-python`, or audio packages, ensure you have required system libs; on Windows prefer wheels.  
   - For `torch`/`tensorflow` GPU builds, ensure matching drivers and CUDA versions. Use CPU-only wheels if needed.

3. `uvicorn` or server binding errors:
   - Check if the port is free or use a different `--port`. Use `--host 0.0.0.0` for external access.

4. Model performance is slow:
   - Use batch inference, smaller precision (float16) if supported, or run on GPU. Consider a lightweight model for production.

If you paste a failing terminal log, I can diagnose the exact error.

---

## 🤝 Contributing

Thanks for considering contributing! Please:

1. Fork the repository.  
2. Create a feature branch: `git checkout -b feature/your-feature`.  
3. Make changes, add tests.  
4. Run tests and linters locally.  
5. Open a Pull Request with a clear description and testing notes.

See `CONTRIBUTING.md` (if added) for more details.

---

## 📝 License

This project is available under the MIT License. See the `LICENSE` file for details.

---

## 📬 Contact

- Repository: https://github.com/Vxlentin0/VisioGuardAI  
- Create an issue for bugs or feature requests. Include reproduction steps and relevant logs.

---

If you want, I can:
- Convert this into `README.md` in the repo root (I can create that file for you), and
- Generate a `requirements.txt` with pinned versions based on the most used files in the workspace,
- Or produce a short `DEV_SETUP.md` with step-by-step environment setup (including recommended PyTorch/TensorFlow commands for CPU/GPU).

Which of those would you like next?
