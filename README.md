<div align="center">
  <img src="https://raw.githubusercontent.com/Parth-tab/WhisperAI-Speech-To-Text/main/resources/logo.png" alt="WhisperAI Logo" width="200"/>
  <h1>WhisperAI Speech-To-Text</h1>
  <p><strong>Type up to 4x faster with Context-Aware, Local AI Voice Dictation.</strong></p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
</div>

---

## ⚡ What is WhisperAI?
WhisperAI is an advanced, local-first voice dictation keyboard that converts natural speech into polished, context-aware text directly within any desktop application. Unlike standard dictation, WhisperAI understands when you stumble, stutter, or change your mind mid-sentence, outputting only your final intent.

## ✨ Core Features
*   **🧠 Auto-Edits & Cleanup:** Automatically removes filler words ("um", "uh", "like") and inserts proper punctuation based on your natural pauses.
*   **⏪ Backtrack Corrections:** Say *"Let's meet at 2... actually make it 3"* and WhisperAI instantly outputs *"Let's meet at 3."*
*   **🎯 Context & Syntax Awareness (Code Mode):** Detects if you're in an IDE like VS Code or Cursor and automatically converts spoken symbols into syntactically perfect code.
*   **🤫 Whisper Mode:** Highly sensitive microphone thresholding allows you to dictate softly in quiet environments without dropping words.
*   **📚 Personal Snippets & Dictionaries:** Map custom phrases to exact outputs via the built-in PyQt GUI.
*   **🔒 100% Local Privacy:** Both the ASR (Faster-Whisper) and LLM (Qwen 3B) run entirely on your local hardware. No audio is ever sent to the cloud.

## 🛠️ Requirements
*   **OS:** Windows 10/11
*   **CPU/GPU:** Intel Core i5 (12th Gen+) or equivalent. Nvidia GPU recommended for CUDA acceleration, or Intel Iris Xe (via Vulkan).
*   **RAM:** 16GB minimum (due to local LLM requirements).
*   **Python:** 3.10+

## 🚀 Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/Parth-tab/WhisperAI-Speech-To-Text.git
   cd WhisperAI-Speech-To-Text
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application:**
   ```bash
   python main.py
   ```
   *(Note: The application will download the required AI models on its first run, which may take a few minutes depending on your connection speed).*

## 📖 Usage
1.  Run the application. A small recording bubble will appear in the corner of your screen.
2.  Click inside any text field in any application (e.g., Slack, VS Code, Word).
3.  Hold down the hotkey (default: **Global Hotkey** configured in Settings) and start speaking.
4.  Release the hotkey. The transcribed, perfectly formatted text will be injected directly into your application.

## 🧩 Project Structure
```text
WhisperAI-Speech-To-Text/
├── src/                # Core application source code
│   ├── asr/            # Automatic Speech Recognition (Faster-Whisper)
│   ├── llm/            # Intent-extraction LLM Engine (Llama.cpp)
│   ├── core/           # App mediator, Pipeline, and Telemetry
│   ├── injection/      # Keyboard injection and Window detection
│   └── gui/            # PySide6 Desktop Interface
├── tests/              # Pytest suite
├── main.py             # Application entrypoint
└── requirements.txt    # Python dependencies
```

## 🤝 Contributing
We welcome community contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
