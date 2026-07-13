# Changelog

## Phase 5: Deployment

This release includes the final deployment optimizations, successfully compiling the architecture into a single `.exe`.

## Key Optimizations & Features

### Core Optimizations
*   **Phase 3 Streaming:** Fully integrated Phase 3 streaming, ensuring ultra-low latency audio processing and real-time transcription feedback.
*   **Context Caching:** Implemented intelligent context caching. This minimizes redundant processing and significantly improves inference speed by reusing context where appropriate.
*   **Explicit Disfluency Tokens:** Added handling for explicit disfluency tokens (e.g., "uh", "um"). The model now gracefully handles and filters out these tokens to produce cleaner transcripts.

### Reliability
*   **Auto-Healing Watchdog:** Deployed an auto-healing watchdog implementation. The watchdog actively monitors critical application components and automatically restarts them in the event of failures or deadlocks, guaranteeing continuous operation.

## User Instructions

### Flow Bubble UI
The new Flow Bubble UI provides a non-intrusive, always-on-top indicator of the application's state.
*   **Interacting:** Simply drag the bubble to reposition it anywhere on your screen.
*   **Status:** The bubble changes color and pulses to indicate whether it is actively listening, processing, or idle.

### Contextual Dictation
Contextual dictation analyzes the application you are currently typing in and adapts its vocabulary appropriately (e.g., coding terms for IDEs, formal language for emails).
*   **Usage:** No special configuration is needed. Start dictating, and the engine will seamlessly adapt to the active window context.

### Command Mode Macros
Command Mode allows you to execute predefined macros using your voice.
*   **Activation:** Use your configured push-to-talk key or wake word to enter Command Mode.
*   **Usage:** Say the name of a macro (e.g., "Delete line", "Format document") and the application will execute the corresponding keystrokes or actions automatically.
