# Contributing to WhisperAI

Thank you for your interest in contributing to WhisperAI! WhisperAI is an enterprise-grade, 100% local, context-aware voice intelligence platform for Windows.

To preserve stability, real-time performance, and our **95.6/100 cross-industry benchmark score**, all contributors must strictly adhere to the engineering guidelines outlined below.

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 🛑 Core Architectural Constraints (HARD RULES)

Pull requests violating any of these core architectural rules will be automatically rejected during CI or code review.

### 1. PyInstaller Asset Resolution (`get_asset_path`)
* WhisperAI is packaged as a single-file executable via PyInstaller, which extracts runtime assets into a temporary directory (`sys._MEIPASS`).
* **NEVER use bare relative paths** (e.g., `open("resources/data.json")` or `QIcon("assets/logo.png")`) or naive `__file__` path arithmetic.
* **ALWAYS use `src.utils.paths.get_asset_path(relative_path)`** for all asset and resource loading.
* If you introduce a new static resource directory, you must also register it in `WhisperAI.spec` under `datas_list`.

### 2. The PySide6 Main Thread (Zero Blocking)
* The UI runs exclusively on the Qt main thread.
* **NEVER run blocking operations** in the main thread (e.g., ASR transcription, LLM token generation, model downloading, file hashing, or `time.sleep()`).
* Heavy operations must always be dispatched to background workers (`QThread` or `ThreadPoolExecutor`) and communicate back to the UI via Qt Signals.

### 3. Strict Ban on Blocking Modals in Floating UIs
* WhisperAI uses floating, frameless desktop overlays (`FramelessWindowHint`, `WindowStaysOnTopHint`) such as the Flow Bubble.
* You are **permanently banned** from calling blocking modal dialogs (e.g., `QMessageBox.critical()`, `QMessageBox.warning()`, `QDialog.exec()`).
* Blocking modal dialogs frequently lose window focus on Windows and spawn invisibly behind other windows, causing a permanent deadlock on the main event loop.
* All error reporting and UI notices must use non-blocking tray notifications (e.g., `self.tray.showMessage()`) or inline visual status indicators.

### 4. 1.5B LLM "Split-Pass" Architecture
* WhisperAI pairs `faster-whisper` with a quantized Qwen 2.5 1.5B model. While 1.5B models are fast and memory-efficient, they will hallucinate or degrade if prompted to execute too many formatting tasks simultaneously.
* **Do not rely solely on system prompts** for complex formatting (such as numbered lists, code block indentation, math formulas, or spoken identifier casing).
* **Always implement a "Split-Pass" strategy:** Use deterministic, rule-based regex pre/post-processing modules (e.g., in `src/utils/casing.py`, `src/utils/syntax_map.py`, and `src/utils/text_cleaner.py`) before or after LLM inference.

### 5. Hardware Integrity & Boot-Only C-Level Polling
* Windows WASAPI and Bluetooth Hands-Free Profile (HFP) driver enumeration can trigger Python Global Interpreter Lock (GIL) deadlocks.
* You are strictly forbidden from placing heavy C-library re-initializations (e.g., `sounddevice._terminate()`, `Pa_Initialize()`) inside frequent UI event loops, button clicks, or hotkey handlers.
* Audio hardware state must be cached at application boot or processed inside detached background threads.

### 6. Zero-PII Logging Rule
* WhisperAI enforces 100% local, air-gapped data sovereignty (HIPAA & GDPR compliant).
* **Never log raw dictation text** to application logs or console output (e.g., avoid `logger.info(f"Dictation: {text}")`).
* Always log character counts or metadata only (e.g., `logger.info(f"Processed transcript of length {len(text)}")`).

---

## 🛠️ Development Workflow

### Prerequisites
* Windows 10/11 (64-bit)
* Python 3.10+
* [uv](https://github.com/astral-sh/uv) (Recommended) or `pip`
* Microsoft Visual C++ Redistributable (2015–2022)

### Setting Up the Environment
```powershell
# Clone the repository
git clone https://github.com/Parth-tab/WhisperAI-Speech-To-Text.git
cd WhisperAI-Speech-To-Text

# Create and activate virtual environment with uv
uv venv
.venv\Scripts\activate
uv sync

# Run the local application
python src/main.py
```

### Git Commit Conventions
We use structured conventional commit messages:
```text
type(scope): concise summary (max 72 chars)

[optional body — explain WHY, not WHAT]
```
**Allowed Types:** `feat` | `fix` | `refactor` | `perf` | `test` | `docs` | `chore`

---

## ✅ Pull Request Requirements

Before creating a Pull Request, run the mandatory verification commands locally:

```powershell
# 1. Run the entire test suite (all 156 tests must pass)
pytest

# 2. Compile the production binary
pyinstaller WhisperAI.spec --clean --noconfirm
```

A Pull Request will only be reviewed and merged once:
1. `pytest` passes with **156/156 tests green (0 errors)**.
2. `pyinstaller` successfully builds `dist/WhisperAI.exe` without compilation errors.
3. All items in [`.github/pull_request_template.md`](.github/pull_request_template.md) are checked off.

Thank you for helping keep WhisperAI fast, reliable, and private! 🚀
