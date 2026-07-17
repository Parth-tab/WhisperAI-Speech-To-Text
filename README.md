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
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"/>
</div>

---

## Executive Summary

The premise of local AI has long been constrained by memory limitations. Desktop users demand near-instantaneous voice dictation, but deploying large language models on consumer hardware traditionally starves the system of resources. WhisperAI resolves this bottleneck. By implementing a **Split-Pass routing** architecture and **P-Core affinity**, we decouple the transcription layer (Faster-Whisper) from the intent-extraction engine (Qwen 2.5 1.5B Q4_K_M). 

The result? Intelligent, context-aware dictation that actively corrects stammers and syntactic errors, operating entirely within a strict memory footprint. Most importantly, this architecture ensures absolute **Zero-Trust Data Sovereignty**—no audio or text ever leaves your machine. 

For deep technical insights on our memory and routing strategies, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Getting Started

### Path A: For Users (1-Click Install)
Experience local, private dictation without touching a terminal.
1. Navigate to our [GitHub Releases](#).
2. Download the latest `WhisperAI_Setup.exe`.
3. Run the installer and launch the application.

### Path B: For Engineers (Lightning-Fast Onboarding)
We utilize `uv` for blistering fast dependency management.
```bash
git clone https://github.com/Parth-tab/WhisperAI-Speech-To-Text.git
cd WhisperAI-Speech-To-Text
uv venv
uv sync
python main.py
```

---

## Project Structure

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

## Contributing
We welcome community contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, CI/CD requirements, and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Troubleshooting
**Windows Defender SmartScreen Bypasses**
If Windows Defender SmartScreen prevents the application from launching, click **More info** and then **Run anyway**. This happens because our compiled binary is not signed by an expensive EV Code Signing Certificate. 
All logs for the runtime environment, including caught exceptions and output, are stored securely at `%USERPROFILE%\.whisperai\logs\whisperai.log`.

## Enterprise Deployment
To deploy WhisperAI across an enterprise environment while bypassing Group Policy restrictions and SmartScreen blocks on untrusted executables, you can compile the application from source on a trusted internal machine.
1. Install Python 3.10+ and clone the repository.
2. Run `uv sync` to install dependencies.
3. Compile with `pyinstaller WhisperAI.spec --clean`.
4. Deploy the newly compiled binary generated in the `dist` folder.
