# Contributing to WhisperAI

Thank you for your interest in contributing to WhisperAI! This document outlines the strict engineering constraints and workflow requirements for this repository. 

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 🛑 Core Architectural Constraints (HARD RULES)

To maintain application stability and performance, all contributors **must** adhere to the following architecture rules. Pull requests that violate these will be immediately rejected.

### 1. The PySide6 Main Thread (No Blocking)
The UI runs entirely on the main thread. 
* **NEVER run blocking operations** (Whisper transcription, LLM generation, model downloading, or synchronous network requests) in the main thread. 
* Heavy workloads must be dispatched to background threads (`QThread` or `ThreadPoolExecutor`) and communicated back via Qt Signals.

### 2. No Blocking Modals in Floating UIs
WhisperAI relies heavily on floating UI overlays (e.g., the Flow Bubble) that use `FramelessWindowHint`.
* You are **permanently banned** from using blocking modal dialogs (e.g., `QMessageBox.critical`, `QMessageBox.warning`). 
* Modal dialogs easily lose window focus and spawn invisibly behind other applications, permanently deadlocking the main thread. 
* All UI error handling must use non-blocking background notifications (e.g., `self.tray.showMessage()`).

### 3. C-Level Hardware Polling is Boot-Only
* You are strictly forbidden from placing heavy C-library re-initializations (e.g., `sounddevice._terminate()`, `Pa_Initialize()`) inside frequent UI event loops or button clicks. 
* Hardware state must be cached on application boot to prevent Python GIL deadlocks caused by Windows WASAPI hardware enumeration.

---

## 💾 The Git LFS Trap (Audio Files)
Audio files are large binaries that rapidly exhaust Git repository storage and cloning bandwidth.
* **Never commit raw audio files** (`.wav`, `.mp3`, `.flac`) from your debugging or testing sessions directly into the main repository.
* If audio files are absolutely required for continuous integration or test suites, they must explicitly be routed through **Git Large File Storage (Git LFS)**.

---

## ✅ Pull Request Requirements

Before submitting a Pull Request, you must verify your changes against our CI/CD pipelines locally. A task is NOT complete until it passes both tests:

1. **Unit & Integration Tests:** 
   ```bash
   pytest
   ```
   *All tests must pass without fatal errors.*

2. **Production Compilation Verification:** 
   ```bash
   pyinstaller WhisperAI.spec --clean
   ```
   *The application must successfully bundle into a single `.exe` in the `dist/` directory. Ensure you have used `src.utils.paths.get_asset_path()` for all resources, as bare relative paths (e.g., `./assets/logo.png`) will crash the compiled binary.*
