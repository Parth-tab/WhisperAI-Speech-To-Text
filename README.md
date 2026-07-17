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

## ✨ Features

*   **Context-Aware Dictation:** Automatically analyzes the application you are currently typing in and adapts its vocabulary (e.g., coding syntax for IDEs, formal language for Outlook).
*   **Lazy-Load Models:** A commercial-grade runtime model fetcher. The application installer is lightweight (<100MB). Upon first boot, it fetches the necessary AI weights securely from the Hugging Face CDN.
*   **Silent Auto-Updater (Handoff Bootstrapper):** Never worry about being out of date. WhisperAI silently detects new releases and allows you to update via a single click in your system tray without interrupting your workflow.
*   **Universal Bluetooth Support:** Custom hardware probing heuristics guarantee seamless connection with Bluetooth Hands-Free Profile (HFP) headsets without deadlocking the Windows audio stack.

---

## 🚀 Installation & Usage

### 1. Standard Installation (For Users)
Experience local, private dictation without touching a terminal.
1. Navigate to our [GitHub Releases](../../releases/latest).
2. Download the latest `WhisperAISetup.exe`.
3. Run the installer. On first boot, a visual Progress Bar will appear as the app securely fetches the local AI models.

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
