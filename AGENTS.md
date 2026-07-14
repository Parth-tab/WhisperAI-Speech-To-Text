# AGENTS.md — WhisperAI Speech-To-Text

> This file is read by all coding agents on every invocation. It encodes the engineering
> philosophy, architecture constraints, and operational rules for this project.
> Treat it as a senior engineer's tribal knowledge dump.

---

## Project Overview

**What this is:** A fast, context-aware, 100% local voice dictation application for Windows that utilizes Faster-Whisper and local LLMs to intelligently inject transcribed text into any active window.

**Tech stack:**
- Language: Python 3.10+
- Desktop Framework: PySide6 (Qt)
- ASR Engine: `faster-whisper`
- LLM Engine: `llama-cpp-python` (running Qwen 1.5B via GGUF)
- Packaging: PyInstaller (compiles into a single portable `.exe`)
- Testing: `pytest`

**Monorepo layout:**
```text
WhisperAI/
├── src/                # Core application source code
│   ├── asr/            # Automatic Speech Recognition (Faster-Whisper)
│   ├── llm/            # Intent-extraction LLM Engine (Llama.cpp)
│   ├── core/           # App mediator, Pipeline, and Telemetry
│   ├── injection/      # Keyboard injection and Window detection
│   ├── gui/            # PySide6 Desktop Interface
│   ├── utils/          # Path helpers, validators, logic extractors
│   └── assets/         # Branding, images, UI resources
├── tests/              # Pytest suite
├── installer/          # Inno Setup configurations
├── main.py             # Application entrypoint
├── WhisperAI.spec      # PyInstaller build configuration
└── requirements.txt    # Python dependencies
```

---

## Folder Conventions

> Violating these conventions is a bug, not a style preference.

- `src/gui/` — PySide6 UI components only. Never place business logic, LLM inferencing, or hardware I/O here. 
- `src/core/` — Mediators and coordinators. Contains `app.py` and telemetry. 
- `src/utils/` — Pure functions. Specifically, `paths.py` MUST be used for all file and asset loading to support PyInstaller runtime environments.
- `installer/` — Inno Setup `.iss` scripts and specific installer graphics (e.g. 24-bit BMPs).

**Cross-boundary import rules:**
- AI/Inference logic (`src/asr/`, `src/llm/`) must NOT import from `src/gui/`. 
- `src/injection/` handles raw Windows API calls (pyautogui, pywin32). Never mix Qt code into injection modules.

---

## Mandatory Commands

Before marking any task complete, run ALL of the following:

```bash
# Tests
pytest

# Compile the executable (Production verification)
pyinstaller WhisperAI.spec --clean
```

A task is NOT done until all commands pass with zero errors and the `.exe` successfully compiles.

---

## Architecture Rules

### 1. PyInstaller Asset Handling (CRITICAL)
- The application is distributed as a single-file executable using PyInstaller.
- When packaged, `main.py` is extracted into a temporary `sys._MEIPASS` directory.
- **NEVER use relative paths** (e.g., `./src/assets/logo.png`) or `__file__` naively.
- **ALWAYS use `src.utils.paths.get_asset_path(relative_path)`** to load resources (icons, models, sounds). If you add a new asset folder, you MUST add it to `WhisperAI.spec` under `datas_list`.

### 2. LLM Engine (1.5B Parameter Limitations)
- We use Qwen2.5-1.5B (quantized). It is fast but small.
- **Do not rely on complex reasoning.** The LLM will hallucinate or degrade if prompted to do too many tasks simultaneously.
- If you need to implement a complex feature (like numbered list formatting or code block handling), you MUST use a "Split-Pass" or rule-based regex pre/post-processing strategy. Do not expect the prompt alone to force strict formatting without failure.

### 3. UI Layer (PySide6)
- The UI runs in the main thread.
- **NEVER run blocking operations** (Whisper transcription, LLM generation, model downloading) in the main thread. Always dispatch heavy work to background threads (`QThread` or `ThreadPoolExecutor`) and communicate back via Qt Signals.

---

## Preferred Libraries

> When adding functionality, reach for these before introducing anything new.

| Need | Use |
|---|---|
| Desktop GUI | `PySide6` (Never `PyQt5`, `tkinter` or `customtkinter`) |
| Keyboard Injection | `pyautogui` and `pynput` |
| Image Processing | `Pillow` |
| LLM Inference | `llama-cpp-python` |
| System paths | `pathlib` (built-in) |

**Never introduce a new dependency without asking first.** Keep the installer footprint small.

---

## Anti-Patterns — Do Not Do These

These are the known failure modes in this codebase:

- [ ] **No bare relative paths.** Never use `open("data.json")` or `QPixmap("image.png")`. ALWAYS use `get_asset_path()`.
- [ ] **No blocking the event loop.** Never run `self.llm(...)` inside a UI button click handler.
- [ ] **No hallucination tolerance.** Never let the LLM output "Here is your text:" preambles. Strip them via strict regex or stop-tokens.
- [ ] **No hardcoded Windows path assumptions.** Use `pathlib.Path.home()` or `os.getenv('APPDATA')`.
- [ ] **No `print()` in production.** PyInstaller is run with `--noconsole`. `sys.stdout` is redirected to a log file. Do not rely on print for user feedback.

---

## Git Rules

**Commit message format:**
```text
type(scope): concise summary (max 72 chars)

[optional body — explain WHY, not WHAT]
```
Types: `feat` | `fix` | `refactor` | `chore` | `docs` | `test` | `perf`

---

## Continuous Integration (CI) & Pull Requests

Any AI working on this repository MUST always check the GitHub Actions tab for CI failures after pushing. You are strictly forbidden from bypassing the Pull Request template requirements. Always ensure all checklist items are met before merging.

---

## Debugging Workflow

When something is broken, follow this sequence:

1. **Reproduce** — confirm you can reproduce the bug consistently using `python main.py`.
2. **Compile Test** — confirm the bug happens (or doesn't happen) in the `pyinstaller` frozen bundle.
3. **Inspect logs** — Check `%USERPROFILE%\.whisperai\logs\whisperai.log` for stdout outputs when running the frozen `.exe`.
4. **Hypothesize** — form one specific theory before changing code.
5. **Fix** — make the minimal change that addresses the root cause.
6. **Verify** — run `pytest` and recompile.

---

*Think like an owner of this codebase, not a temporary contributor.*
