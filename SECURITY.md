# Security Policy

## Supported Versions

Currently, only the latest release (`v1.1.0` and above) is supported with active security patches.

| Version | Supported          |
| ------- | ------------------ |
| >= 1.1.0| :white_check_mark: |
| < 1.1.0 | :x:                |

---

## 🛡️ Zero-Trust Data Sovereignty
WhisperAI is engineered with absolute **Zero-Trust Data Sovereignty**. 
* **No Cloud Telemetry:** Your voice data, transcriptions, and contextual inputs never leave your local hardware. 
* **Air-Gapped Capable:** After the initial download of the AI models, the application can operate entirely offline without degrading transcription accuracy.

## ⚠️ Supply Chain Attacks & Malicious Tensor Weights (The "Zero-Exploit" Policy)
The most critical threat vector for local AI applications is the sideloading of compromised model weights. 

**Strict Directive:** You must **only** download the `faster-whisper` and `Qwen` models via the official Hugging Face CDN endpoints hardcoded into the WhisperAI downloader. 
* **Do NOT sideload unverified `.bin`, `.pt`, or `.safetensors` files from third-party sources or untrusted forums.** 
* Malicious actors can embed arbitrary code inside pickled tensor weights. Loading compromised models can lead to instant Remote Code Execution (RCE) on your local machine.

## 🐛 Reporting a Vulnerability

We take all security vulnerabilities seriously. 

**Do NOT open a public issue for security vulnerabilities.**

Instead, please use GitHub's **Private Vulnerability Reporting**:
1. Go to the [Security tab](../../security) of this repository.
2. Click on **Report a vulnerability**.
3. Provide a detailed summary of the exploit (e.g., arbitrary code execution via compromised models, memory corruption in the C-bindings, etc.) and a Proof of Concept (PoC) if applicable.

You can expect an initial response within 48 hours. If the vulnerability is validated, we will work with you to patch the application and issue a CVE if necessary.
