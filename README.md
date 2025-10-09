# VisioGuardAI — Project Overview

VisioGuardAI is a collection of tools, services, and scripts aimed at visual threat detection, API/key management, and related utilities. This repository contains an application (API and web components), helper scripts, model files and training/output directories. The project uses Python and some ML / computer vision libraries and can be run locally or inside Docker.

This `README.txt` is written using GitHub-style Markdown formatting so it displays readably on GitHub and in editors that render Markdown.

## Highlights

- FastAPI-based API for serving vision models and utilities
- Scripts for API key rotation and automation under `scripts/`
- Dockerfile for containerized deployment
- Model and data folders for machine learning assets

## Repository layout (important paths)

- `app/` — Main application sources (API, routes, app entrypoints)
- `scripts/` — Utility scripts (e.g., `rotate_api_keys.py`)
- `requirements.txt` — (recommended) Python dependencies
- `Dockerfile` — Container image build spec
- `models/` — Trained models and artifacts (may be large; usually stored outside the repo)
- `data/` — Example datasets and sample inputs/outputs

> Note: some folders may be placeholders or contain generated files. Check `.gitignore` for files that are ignored.

## Quick-start (Windows / PowerShell)

These steps assume you will run locally on Windows and want an isolated Python virtual environment.

1. Clone the repo:

```powershell
git clone <repo-url> VisioGuardAI
cd VisioGuardAI
```

2. Create and activate a venv (recommended name: `.venv`):

```powershell
python -m venv .venv
# PowerShell activation
.\.venv\Scripts\Activate.ps1
# If using cmd.exe: .\.venv\Scripts\activate.bat
```

3. Upgrade packaging tools and install dependencies:

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

If you did not clone a `requirements.txt`, you can install core packages manually (grouped to reduce conflicts):

```powershell
# Core web + dev
python -m pip install fastapi uvicorn starlette
# Data / ML
python -m pip install numpy pandas scikit-learn matplotlib
# Imaging / CV
python -m pip install Pillow opencv-python
# Deep learning (Torch: choose appropriate command for your platform/GPU)
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
# Hugging Face transformers
python -m pip install transformers
```

Notes:
- For `torch`, follow instructions on https://pytorch.org/ to pick the correct wheel for your CUDA/CPU setup.
- `tensorflow` can be installed similarly but may require a specific Python version (often 3.8–3.11 depending on release) and can be large.

## Running the API locally (FastAPI / Uvicorn)

If the main app exposes a FastAPI instance, run with uvicorn from the repo root. Example where `app.main:app` is the FastAPI app object:

```powershell
# Activate venv first
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for the interactive OpenAPI docs if applicable.

## Example: Running a script (rotate_api_keys)

Many helper scripts live in `scripts/`. To run the `rotate_api_keys.py` script:

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\rotate_api_keys.py --help
# or run with expected args
python scripts\rotate_api_keys.py --config path\to\config.json
```

Check the script header or `--help` for expected parameters.

## Docker

Build and run the Docker image (simple example):

```powershell
# From repo root
docker build -t visioguardai:latest .
docker run -p 8000:8000 --env-file .env visioguardai:latest
```

Adjust the run flags for volumes, GPU access (nvidia runtime), or environment variables as required.

## Common setup & installation problems

If you encounter errors while installing packages, try the following checklist:

1. Activate the correct virtual environment. VS Code may be pointing to a different interpreter. In VS Code: Ctrl+Shift+P -> "Python: Select Interpreter" -> pick the `.venv` Python.

2. Upgrade pip/setuptools/wheel before installing large packages:

```powershell
python -m pip install --upgrade pip setuptools wheel
```

3. Install packages in small groups to isolate failures. For example, install core packages first, then imaging/ML, then optional extras.

4. For packages that require compilation (rare on Windows in recent wheels), you may need Microsoft Build Tools / C++ Build Tools. Install from:
https://visualstudio.microsoft.com/visual-cpp-build-tools/

5. GPU-based packages (TensorFlow, PyTorch with CUDA) often require matching NVIDIA drivers and CUDA toolkits. If you don't have a GPU or want a simpler install, choose the CPU-only wheel.

6. If installing `opencv-python` fails, try using the prebuilt wheel (pip should fetch it) or install `opencv-python-headless` for server environments without GUI support.

7. If cryptography installation fails, install the latest `pip` and `setuptools`, and on Windows the `cryptography` wheel should install automatically. On some systems you may need OpenSSL dev libs.

If you paste the full error output, I'll analyze it and give targeted steps.

## VS Code — selecting the correct interpreter (short guide)

1. Open the Command Palette (Ctrl+Shift+P).
2. Type `Python: Select Interpreter` and press Enter.
3. Choose the interpreter pointing to your venv, usually named `.venv\Scripts\python.exe` or showing the project path.
4. Restart the VS Code window if errors still show.

## Testing

If the project contains tests (e.g., `pytest`), run them from the repo root:

```powershell
.\.venv\Scripts\Activate.ps1
pytest -q
```

Add or adjust tests under a `tests/` directory as needed.

## Troubleshooting specific packages

- PyTorch: follow https://pytorch.org/get-started/locally/ for platform-specific commands. Use CPU-only wheel if unsure.
- TensorFlow: check Python version compatibility; TensorFlow releases often lag behind the latest Python.
- google-api-python-client / google-auth-oauthlib: ensure you follow Google OAuth setup for credentials and store them securely (do not commit `.json` keys to the repo).
- Speech libraries (pyttsx3, SpeechRecognition): may need system audio drivers or additional backends (e.g., `pyaudio` requires portaudio, which needs a binary wheel or system libs).

## Security and API keys

- Do NOT commit any secrets, API keys, or credentials. Use `.env` files, environment variables, or secret managers.
- Rotate and revoke keys regularly. The `scripts/rotate_api_keys.py` is provided to help with rotation — review it and test in a safe environment.

## Contributing

- Fork the repo and open a pull request for non-trivial changes.
- Keep commits small and focused. Add tests for new functionality.
- Run linters and tests locally before opening PRs.

## License

Specify your license here (e.g., MIT, Apache-2.0). If you don't have a license file, add `LICENSE` at the repo root.

## Contact / Support

For questions or issues, open a GitHub Issue in this repository with a reproducible description and relevant logs.

---

Revision notes:
- This file is intended as a general, approachable guide for developers and users on Windows. Adapt the commands for macOS/Linux (activate venv with `source .venv/bin/activate`).
- If you'd like, I can also generate a `requirements.txt` with the recommended packages and a minimal `setup` script for easier install.

