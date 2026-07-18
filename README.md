<div align="center">
  <img src="resources/banner.png" alt="WhisperAI Cinematic Banner" width="800"/>
</div>

<div align="center">
  <!-- Group 1: CI/CD -->
  <img src="https://img.shields.io/badge/Build-Passing-brightgreen" alt="Build"/>
  <img src="https://img.shields.io/badge/Tests-Passing-brightgreen" alt="Tests"/>
  <img src="https://img.shields.io/badge/Memory_Circuit_Breaker-Active-blue" alt="Circuit Breaker"/>
  <br/>
  <!-- Group 2: Code Quality -->
  <img src="https://img.shields.io/badge/Ruff-Enabled-orange" alt="Ruff"/>
  <img src="https://img.shields.io/badge/MyPy-Strict-blue" alt="MyPy"/>
  <br/>
  <!-- Group 3: Metadata -->
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python Version"/>
  <img src="https://img.shields.io/badge/License-MIT%20%2F%20Apache%202.0-blue.svg" alt="License"/>
</div>

---

## 🎙️ What is WhisperAI?

The premise of local AI has long been constrained by memory limitations. Desktop users demand near-instantaneous voice dictation, but deploying large language models on consumer hardware traditionally starves the system of resources. 

**WhisperAI resolves this bottleneck.** It is a fast, context-aware, 100% local voice dictation application for Windows that intelligently injects transcribed, grammatically corrected text into any active window.

### 🧠 How it Works: The "Split-Pass" Architecture
We decouple the acoustic transcription layer from the intent-extraction engine to maintain a strict memory footprint:
1. **Acoustic Layer:** We utilize `faster-whisper` (C-translate2) for ultra-fast, robust transcription.
2. **Intent Layer:** We route the raw transcript into a heavily quantized Qwen 2.5 1.5B (GGUF) local LLM via `llama.cpp`. This engine actively corrects stammers, formats contextually (e.g., code vs. prose), and removes hallucinations.
3. **P-Core Affinity:** The entire pipeline is pinned to your CPU's Performance Cores, avoiding E-Core latency penalties common in Windows 11 task scheduling.

**Zero-Trust Data Sovereignty:** Absolutely no audio or text ever leaves your machine. Your voice remains yours. Period. 

---

## 🏗️ System Structure

WhisperAI follows a strict, domain-driven `src/` layout to cleanly separate acoustic processing, language generation, and the graphical user interface.

```text
WhisperAI/
├── src/                # Core application source code
│   ├── asr/            # Automatic Speech Recognition (Faster-Whisper)
│   ├── llm/            # Intent-extraction LLM Engine (Llama.cpp)
│   ├── core/           # App mediator, Pipeline, and Telemetry
│   ├── injection/      # Keyboard injection and Window detection
│   ├── gui/            # PySide6 Desktop Interface
│   ├── utils/          # Path helpers, validators, logic extractors
│   ├── assets/         # Branding, images, UI resources
│   ├── main.py         # Application entrypoint
│   └── helper.py       # Win32 hardware heuristics
├── tests/              # Pytest suite & CI profiling tests
├── resources/          # Static configuration assets & JSON schemas
├── installer/          # Inno Setup configurations
├── WhisperAI.spec      # PyInstaller build configuration
└── pyproject.toml      # Dependency & linting configuration
```

---

## ✨ Detailed Features & Capabilities

*   **Context-Aware Dictation (Active Window Detection):**
    *   WhisperAI intelligently probes the Windows API to determine which application is currently in focus via `src/injection/window_detect.py`.
    *   It dynamically swaps terminology (e.g., heavily biasing towards `snake_case` programming syntax if an IDE is active, or formal prose if Outlook is active) resulting in highly accurate, zero-correction dictation.

*   **Lazy-Load Model Architecture (Hugging Face CDN):**
    *   To prevent the distribution of multi-gigabyte monolithic executables, WhisperAI ships as a lightweight `<100MB` binary.
    *   Upon first execution, the `DownloaderDialog` automatically provisions the necessary quantized models (`Qwen 2.5` and `Whisper`) from secure Hugging Face endpoints directly into `%USERPROFILE%\.whisperai\models`, preventing repository and installer bloat.

*   **Silent Auto-Updater (The Handoff Bootstrapper):**
    *   Powered by the `src/core/updater.py` module, WhisperAI checks for new releases on GitHub via a non-blocking background thread.
    *   When an update is detected, it downloads the new payload silently and executes a seamless process handoff—bypassing Windows OS-level file lock restrictions on running executables without interrupting the user.

*   **Universal Bluetooth Duplex Support (Anti-Deadlock Heuristics):**
    *   Windows WASAPI heavily struggles with Bluetooth Hands-Free Profile (HFP) dynamic device enumeration, frequently causing Python Global Interpreter Lock (GIL) deadlocks.
    *   WhisperAI utilizes a custom C-Types bridge (`src/helper.py`) to perform boot-time caching and case-insensitive heuristic matching to instantly align audio input/output streams without freezing the UI.

*   **Flow Bubble (Non-Blocking GUI):**
    *   A custom, frameless `PySide6` desktop overlay provides real-time visual feedback (Listening, Processing, Idle) via animated pulses.
    *   Built purely with asynchronous Qt Signals, it never steals window focus and operates flawlessly without blocking modal dialogs.

---

## 🚀 Installation & Usage

### 1. Standard Installation (For Users)
Experience local, private dictation without touching a terminal.
1. Download the `WhisperAISetup.exe` file directly from the root directory of this repository.
2. Run the installer. On first boot, a visual Progress Bar will appear as the app securely fetches the local AI models.

<div align="center">
  <img src="resources/lazy_loader.png" alt="Lazy Loader UI" width="400"/>
</div>

### 2. ⚠️ The Windows SmartScreen Warning
Because WhisperAI is an open-source project, we do not utilize a $500/year Enterprise EV Code Signing Certificate. As a result, Windows Defender SmartScreen will initially flag the installer as an "Unrecognized app".

**How to bypass safely:**
1. When the blue SmartScreen window appears, click **"More info"**.
2. A new button will appear at the bottom. Click **"Run anyway"**.

<div align="center">
  <img src="resources/smartscreen_bypass.png" alt="SmartScreen Bypass Guide" width="400"/>
</div>

### 3. Build from Source (For Developers)
We utilize `uv` for blistering fast dependency management.
```bash
git clone https://github.com/Parth-tab/WhisperAI-Speech-To-Text.git
cd WhisperAI-Speech-To-Text
uv venv
uv sync
python src/main.py
```

---

## 🔒 Security & Contribution

*   **Security:** Read our [Zero-Exploit Policy](SECURITY.md) to understand how we protect against malicious tensor weights and how to report vulnerabilities privately.
*   **Contributing:** We welcome contributions! Please strictly adhere to our PySide6 UI constraints and Git LFS policies outlined in [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License
This project is licensed under the MIT License, while downstream machine learning models (Qwen, Whisper) retain their respective Apache 2.0 / MIT licenses. See the [LICENSE](LICENSE) file for complete details.
