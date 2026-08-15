# Non-Blocking PySide6 Floating Overlay

Because WhisperAI operates alongside any active Windows application, the UI runs as a frameless, non-activating floating overlay on the main Qt thread while all heavy inference (Whisper/LLM) executes in detached background worker threads (`QThread`) communicating via Qt signals. Blocking modal dialogs are strictly prohibited to avoid focus deadlocks and invisible window lockups.
