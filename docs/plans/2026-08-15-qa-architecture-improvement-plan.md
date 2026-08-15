# WhisperAI QA & Test Automation Architecture Improvement Plan (48 to 95/100)

**Goal:** Elevate WhisperAI's QA, Test Automation, and Code Coverage score from **48/100 (Grade D+)** to **95+/100 (Grade A+)** by systematically eliminating test coverage gaps, introducing high-fidelity fixtures, testing concurrency/hardware failure modes, and establishing automated CI/CD quality gates.

**Architecture:** A 6-phase engineering roadmap covering pytest hygiene, comprehensive unit test suites for 16 untested modules, headless virtual audio/Win32 fixtures, multi-stage pipeline integration, hardware/concurrency stress testing, and CI/CD gate automation.

**Tech Stack:** Python 3.10+, `pytest`, `pytest-cov`, `pytest-mock`, `hypothesis`, PySide6 (QtTest), `faster-whisper`, `llama-cpp-python`, `onnxruntime`, PyInstaller, Inno Setup, GitHub Actions.

---

## Target Scorecard

| Dimension | Baseline Score | Target Score | Key Deliverable |
|---|:---:|:---:|---|
| **1. Test Suite Coverage & Depth** | 42 / 100 | **96 / 100** | Full coverage for 16 untested modules; line coverage >= 85%. |
| **2. Test Infrastructure & Pytest Hygiene** | 55 / 100 | **98 / 100** | Strict `pyproject.toml` pytest configuration; zero scratch collection; warning filters. |
| **3. Mocking Fidelity & Isolation** | 50 / 100 | **94 / 100** | High-fidelity virtual audio generator, headless Win32 mock, ChatML GGUF mock. |
| **4. Edge Case & Hardware Resilience** | 38 / 100 | **92 / 100** | Rapid hotkey thrashing stress tests, device disconnect recovery, watchdog deadlock tests. |
| **5. Build & Packaging Verification** | 65 / 100 | **95 / 100** | Verified `.spec` runtime hooks, Inno Setup `AppMutex`, automated CI pipeline. |
| **COMPOSITE QA RATING** | **48 / 100** | **95+ / 100** | **Enterprise-Grade QA Architecture** |

---

## Phase 1: Pytest & Test Runner Configuration Hygiene

### Task 1.1: Configure `pyproject.toml` for Pytest & Coverage
- **Target File:** `pyproject.toml`
- **Objective:** Prevent test pollution from `scratch/`, configure warning suppressions, add test markers, and enforce test discovery bounds.
- **Specification:**
  ```toml
  [tool.pytest.ini_options]
  minversion = "8.0"
  testpaths = ["tests"]
  norecursedirs = ["scratch", "build", "dist", ".venv", "temp_*"]
  addopts = "-ra -q --ignore=scratch --cov=src --cov-report=term-missing"
  markers = [
      "slow: marks tests as slow (deselect with '-m \"not slow\"')",
      "hardware: marks tests requiring real audio/GPU hardware",
      "e2e: end-to-end integration tests",
  ]
  filterwarnings = [
      "ignore::DeprecationWarning:sounddevice.*",
      "ignore::DeprecationWarning:pkg_resources.*",
  ]
  ```

---

## Phase 2: Missing Subsystem Unit Test Suites (16 Modules)

### Task 2.1: Silero VAD Engine Test Suite
- **New Test File:** `tests/test_vad.py`
- **Target Module:** `src/audio/vad.py`
- **Tests to Implement:**
  1. `test_vad_initialization_and_model_loading`: Verifies session creation and initial zero-state tensor `(2, 1, 128)`.
  2. `test_vad_speech_detection_and_consecutive_frames`: Feeds synthetic high-probability frames; asserts `_speech_detected` becomes `True` after 3 consecutive frames.
  3. `test_vad_silence_timeout_after_speech`: Confirms silence timeout triggers only after 700ms silence *following* confirmed speech.
  4. `test_vad_grace_period_prevents_premature_cutoff`: Verifies that silence in the first 2.0s never triggers a timeout.
  5. `test_vad_safety_timeout_on_continuous_silence`: Verifies forced timeout after 5 minutes (300,000ms) if no speech is detected.
  6. `test_vad_chunk_resizing_and_padding`: Verifies proper slice/padding of arbitrary buffer lengths (e.g. 256 or 1024 samples) to 512 samples.

### Task 2.2: Spoken Code Syntax Map Test Suite
- **New Test File:** `tests/test_syntax_map.py`
- **Target Module:** `src/utils/syntax_map.py`
- **Tests to Implement:**
  1. `test_multi_word_operator_precedence`: Verifies `"plus equals"` -> `"+="` (not `"+ ="`), `"greater than or equal to"` -> `">="`, `"double equals"` -> `"=="`.
  2. `test_delimiters_and_brackets`: Verifies `"open paren x close paren"` -> `"(x)"`, `"open brace close brace"` -> `"{}"`.
  3. `test_symbol_and_whitespace_replacements`: Verifies `"new line indent semicolon"` -> `"\n\t;"`.
  4. `test_case_insensitivity_and_word_boundaries`: Verifies `"EQUAL TO"` and preserves internal words like `"equality"`.

### Task 2.3: Spoken Self-Correction & Backtrack Detector Test Suite
- **New Test File:** `tests/test_backtrack.py`
- **Target Module:** `src/utils/backtrack_detector.py`
- **Tests to Implement:**
  1. `test_backtrack_markers_detection`: Tests all 8 markers (`actually`, `i mean`, `wait`, `no wait`, `no no`, `sorry`, `scratch that`, `let me rephrase`).
  2. `test_backtrack_xml_tag_wrapping`: Asserts `"Meet Wednesday actually Thursday"` -> `"<original>Meet Wednesday</original> <correction>actually Thursday</correction>"`.
  3. `test_backtrack_no_marker_returns_unchanged`: Verifies plain text passes through unmodified.
  4. `test_backtrack_multiple_markers_uses_last_match`: Verifies handling when multiple corrections occur in a single utterance.

### Task 2.4: Local SQLite Usage Statistics Store Test Suite
- **New Test File:** `tests/test_stats_store.py`
- **Target Module:** `src/data/stats_store.py`
- **Tests to Implement:**
  1. `test_stats_store_custom_db_initialization`: Verifies SQLite table creation with a temporary database path.
  2. `test_stats_store_log_session`: Verifies word/character count calculation, ISO timestamp insertion, and duration logging.
  3. `test_stats_store_get_totals_and_wpm_calculation`: Verifies average WPM formula: `(total_words / total_duration_sec) * 60.0`.
  4. `test_stats_store_empty_db_defaults`: Verifies `0` totals and `0.0` WPM when no sessions exist.

### Task 2.5: Dynamic Workspace File Indexer Test Suite
- **New Test File:** `tests/test_file_index.py`
- **Target Module:** `src/utils/file_index.py`
- **Tests to Implement:**
  1. `test_file_indexer_scan_workspace_depth_limit`: Creates a 6-level directory structure; asserts scan stops at depth 4.
  2. `test_file_indexer_ignores_standard_directories`: Verifies `.git`, `node_modules`, `venv`, `build`, `dist` are excluded.
  3. `test_file_indexer_max_file_cap`: Asserts scanning terminates cleanly if 10,000 files are reached.
  4. `test_file_indexer_cache_ttl_and_eviction`: Tests 60s TTL cache hits and 20-workspace LRU eviction.
  5. `test_file_indexer_fuzzy_find_file`: Verifies `"pipeline dot p y"` -> `"pipeline.py"` and `"app"` -> `"app.py"`.

### Task 2.6: IDE Active Context Bridge Test Suite
- **New Test File:** `tests/test_ide_bridge.py`
- **Target Module:** `src/injection/ide_bridge.py`
- **Tests to Implement:**
  1. `test_ide_bridge_process_file_tags_success`: Mocks `file_indexer` to assert `"in file pipeline"` -> `"@pipeline.py"`.
  2. `test_ide_bridge_invalid_pid_or_workspace_fallback`: Asserts raw text is returned unchanged when PID is <= 0 or workspace is unknown.
  3. `test_ide_bridge_unmatched_file_preserves_text`: Asserts unknown file hints are kept as plain text.

### Task 2.7: Runtime Asset Path Resolution Test Suite
- **New Test File:** `tests/test_paths.py`
- **Target Module:** `src/utils/paths.py`
- **Tests to Implement:**
  1. `test_get_asset_path_dev_environment`: Asserts resolution against project root when `sys._MEIPASS` is absent.
  2. `test_get_asset_path_frozen_meipass`: Mocks `sys._MEIPASS` and verifies paths resolve to the temporary PyInstaller bundle directory.

### Task 2.8: Team Sync & Cloud Dictionary Test Suite
- **New Test File:** `tests/test_teams_sync.py`
- **Target Modules:** `src/teams/auth.py`, `src/teams/api_client.py`, `src/teams/sync.py`
- **Tests to Implement:**
  1. `test_auth_token_save_and_retrieve`: Verifies secure token storage in config.
  2. `test_api_client_request_headers_and_error_handling`: Tests Bearer auth headers, timeouts, and JSON error responses.
  3. `test_team_sync_dictionary_merge`: Tests merging remote team words into the local custom dictionary with deduplication.

---

## Phase 3: High-Fidelity Test Fixtures & Concurrency Framework

### Task 3.1: Create `tests/conftest.py` Fixture Library
- **Target File:** `tests/conftest.py`
- **Fixtures to Implement:**
  1. `virtual_audio_generator`: Generates 16kHz float32 mono sine wave bursts with configurable duration and SNR.
  2. `mock_faster_whisper_engine`: Returns a mock `WhisperModel` yielding synthetic segments with word probabilities and realistic timing.
  3. `mock_llama_cpp_engine`: Returns a mock `Llama` instance yielding ChatML formatted responses matching prompts.
  4. `headless_win32_environment`: Patches `win32gui`, `ctypes.windll.user32`, and `pyperclip` to simulate foreground windows, caret positions, and clipboard buffers in headless CI.

### Task 3.2: Multi-Stage Pipeline Integration Tests
- **New Test File:** `tests/test_pipeline_stages.py`
- **Target Module:** `src/core/pipeline.py`
- **Tests to Implement:**
  1. `test_pipeline_snippet_stage_bypasses_llm`: Tests exact phrase replacement without LLM overhead.
  2. `test_pipeline_command_mode_stage`: Tests highlighted text transformation via `Ctrl+C` capture and LLM rewriting.
  3. `test_pipeline_code_mode_stage`: Tests syntax map and `@file` expansion in IDE processes (`code.exe`).
  4. `test_pipeline_backtrack_stage`: Tests XML tag insertion for verbal self-corrections.
  5. `test_pipeline_llm_cleanup_fast_path_bypass`: Verifies `needs_llm_cleanup` bypasses LLM for clean inputs.
  6. `test_pipeline_stage_exception_fallback`: Verifies that an exception in any stage falls back gracefully to raw pre-filtered text without crashing.

---

## Phase 4: Hardware Resilience & Concurrency Stress Testing

### Task 4.1: Concurrency & Stress Test Suite
- **New Test File:** `tests/test_concurrency_stress.py`
- **Target Modules:** `src/core/app.py`, `src/hotkey/listener.py`, `src/core/watchdog.py`
- **Tests to Implement:**
  1. `test_rapid_hotkey_toggle_thrashing`: Emits 500 rapid press/release events with 10ms intervals; asserts zero thread leaks, lock deadlocks, or unhandled exceptions.
  2. `test_audio_worker_device_disconnect_and_cascade_recovery`: Simulates a PortAudio stream crash; asserts `_on_recording_failed` emits non-blocking tray alert and safely joins worker thread.
  3. `test_watchdog_thread_hang_and_deadlock_recovery`: Simulates an unhandled blocking call in worker thread (>30s); asserts watchdog triggers `_on_deadlock` and re-initializes pipeline.
  4. `test_hibernation_wake_up_race_condition`: Simulates rapid hotkey presses during active background model reloading; asserts clean state synchronization.

---

## Phase 5: GUI, Dialogs & Auto-Updater Test Suite

### Task 5.1: Floating Pill & Overlay UI Tests
- **New Test File:** `tests/test_gui_bubble.py`
- **Target Module:** `src/gui/flow_bubble.py`, `src/gui/overlay.py`
- **Tests to Implement:**
  1. `test_flow_bubble_state_machine`: Verifies geometry and opacity changes across `IDLE`, `RECORDING`, `PROCESSING`.
  2. `test_flow_bubble_win32_no_activate_style`: Verifies `WS_EX_NOACTIVATE` and `WS_EX_TOOLWINDOW` flags are applied.
  3. `test_flow_bubble_manual_drag_and_persistence`: Verifies mouse drag events update `config_manager`.

### Task 5.2: Downloader Wizard & Auto-Updater Tests
- **New Test File:** `tests/test_downloader_dialog.py` & `tests/test_updater_flow.py`
- **Target Modules:** `src/gui/downloader_dialog.py`, `src/core/updater.py`
- **Tests to Implement:**
  1. `test_downloader_dialog_tqdm_progress_translation`: Verifies monkey-patched `tqdm` emits valid Qt progress percentages.
  2. `test_auto_updater_release_detection_and_tray_alert`: Mocks GitHub API response to verify update notification balloon.
  3. `test_auto_updater_download_and_inno_setup_command`: Verifies download to `%TEMP%` and silent Inno Setup invocation flags (`/VERYSILENT /SUPPRESSMSGBOXES`).

---

## Phase 6: Packaging, Spec Hardening & Automated CI/CD Gates

### Task 6.1: PyInstaller Specification Hardening
- **Target File:** `WhisperAI.spec`
- **Changes:**
  - Wire `hookspath=['hooks']` and `runtime_hooks=['rthooks/rthook_llama_cpp.py']`.
  - Add explicit hidden imports: `['scipy.signal', 'sqlite3', 'packaging.version', 'dataclasses']`.
  - Add Inno Setup `AppMutex=WhisperAI_App_Mutex` in `installer/setup.iss` to prevent installation over running instances.

### Task 6.2: GitHub Actions Automated CI Pipeline
- **New File:** `.github/workflows/ci.yml`
- **Workflow Steps:**
  1. Setup Python 3.10 on `windows-latest`.
  2. Install dependencies + test tools (`pytest`, `pytest-cov`, `ruff`, `mypy`, `hypothesis`).
  3. Static lint check (`ruff check src/ tests/`) and type check (`mypy src/`).
  4. Run full test suite with coverage enforcement: `pytest tests/ --cov=src --cov-fail-under=85`.
  5. Compile production bundle: `pyinstaller WhisperAI.spec --clean --noconfirm`.
  6. Smoke-test frozen executable: `dist\WhisperAI.exe --version`.

---

## Execution Checklist & Score Trajectory

| Phase | Description | Estimated Tests | Target Score Impact |
|:---:|---|:---:|:---:|
| **Phase 1** | Pytest Configuration & Warning Suppression | +0 | 48 -> 55 |
| **Phase 2** | Unit Tests for 16 Untested Modules | +45 tests | 55 -> 78 |
| **Phase 3** | High-Fidelity Test Fixtures & Stage Integration | +20 tests | 78 -> 86 |
| **Phase 4** | Concurrency, Hardware & Stress Tests | +15 tests | 86 -> 91 |
| **Phase 5** | GUI, Downloader & Auto-Updater Tests | +12 tests | 91 -> 94 |
| **Phase 6** | Build Hardening & GitHub Actions CI Gate | +2 checks | **95+ / 100** |
