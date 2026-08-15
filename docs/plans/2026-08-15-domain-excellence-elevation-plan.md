# WhisperAI Cross-Industry Excellence & Domain Elevation Plan (Target: 95+ / 100)

**Goal:** Elevate WhisperAI from a developer-centric English tool (Score: 58.8/100) to an enterprise-grade, multi-domain, multilingual voice dictation system (Target Score: 95.6/100) across Engineering, Medicine, Law, Finance, Science, Operations, and Creative Writing.

**Architecture:** 
1. Refactor regex sanitizers to eliminate false-positive drops on repeating digits ($1,000,000), Markdown formatting (###, ```, ---), single-character math variables ($x = 1$), and emojis.
2. Decouple the hardcoded software engineering prompt in `ASREngine`, introducing dynamic profile-aware prompting.
3. Introduce a Spoken Identifier Casing Engine (`camelCase`, `snake_case`, `PascalCase`, `kebab-case`, `SCREAMING_SNAKE`).
4. Expand `syntax_map.py` with C++/Go/Rust operators, LaTeX math/Greek symbols, Markdown headers, and emoji voice triggers.
5. Add dedicated Domain Style Profiles (`medical`, `legal`, `financial`, `academic`, `prd`) and Web App domain detection.
6. Upgrade the snippet system with multi-line templates and dynamic parameters (`{date}`, `{clipboard}`, `{cursor}`).
7. Add full multilingual auto-detection and language switching for 99+ Whisper languages.
8. Harden enterprise security with auto-update toggles, SHA-256 validation, and log data sanitization.

**Tech Stack:** Python 3.10+, PySide6, Faster-Whisper (CTranslate2), Llama-cpp-python (Qwen 2.5 1.5B GGUF), Win32 API, Pytest.

---

### Task 1: Core Text Cleaner & Regex De-weaponization (Stop Number / Markdown / Unicode / Emoji Destruction)

**Files:**
- Modify: `src/utils/text_cleaner.py:40-65`
- Modify: `src/llm/formatter.py:8-18`
- Modify: `src/injection/injector.py:130-145`
- Test: `tests/test_text_cleaner.py`

- [ ] **Step 1: Write the failing unit tests for edge-case preservation**
```python
# In tests/test_text_cleaner.py
def test_preserves_financial_numbers_and_decimals():
    from src.utils.text_cleaner import sanitize_symbol_loops
    assert sanitize_symbol_loops("$1,000,000 in revenue") == "$1,000,000 in revenue"
    assert sanitize_symbol_loops("Bond price was $999.00") == "Bond price was $999.00"
    assert sanitize_symbol_loops("Valuation $888M") == "Valuation $888M"

def test_preserves_single_letter_math_and_emojis():
    from src.utils.text_cleaner import sanitize_symbol_loops
    assert sanitize_symbol_loops("x = 1") == "x = 1"
    assert sanitize_symbol_loops("i += 1") == "i += 1"
    assert sanitize_symbol_loops("🚀 Launch ready 👍") == "🚀 Launch ready 👍"

def test_preserves_markdown_headers_and_code_blocks():
    from src.utils.text_cleaner import sanitize_symbol_loops
    assert sanitize_symbol_loops("### Section Title") == "### Section Title"
    assert sanitize_symbol_loops("```python\nprint('hello')\n```") == "```python\nprint('hello')\n```"
    assert sanitize_symbol_loops("---\nauthor: test\n---") == "---\nauthor: test\n---"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_text_cleaner.py -k "test_preserves" -v`
Expected: FAIL due to regex collapsing `000` to `0` and dropping `x = 1`.

- [ ] **Step 3: Implement clean non-destructive regex filters**
Update `src/utils/text_cleaner.py`:
- Restrict character repetition collapsing strictly to letters `[a-zA-Z]` (never digits `0-9`).
- Exclude markdown symbols (`#`, `` ` ``, `-`, `*`) from symbol loop collapsing.
- Replace `re.findall(r"[a-zA-Z]{2,}", text)` with Unicode-aware `re.search(r"(\w|[\$\€\£\¥\+\-\*\/\=\<\>\%\#\@\🚀\👍])", text)`.

- [ ] **Step 4: Run tests to verify they pass**
Run: `pytest tests/test_text_cleaner.py -v`
Expected: PASS (all 15+ tests pass).

---

### Task 2: Profile-Aware Dynamic ASR Initial Prompting

**Files:**
- Modify: `src/asr/engine.py:200-230`
- Modify: `src/core/pipeline.py:40-60`
- Test: `tests/test_asr.py`

- [ ] **Step 1: Write test for dynamic initial prompt selection**
```python
# In tests/test_asr.py
def test_dynamic_initial_prompt_selection(mock_asr_engine):
    prompt_tech = mock_asr_engine.get_initial_prompt(profile_id="technical")
    prompt_med = mock_asr_engine.get_initial_prompt(profile_id="medical")
    prompt_legal = mock_asr_engine.get_initial_prompt(profile_id="legal")
    
    assert "programming" in prompt_tech.lower()
    assert "pharmacology" in prompt_med.lower() or "clinical" in prompt_med.lower()
    assert "statutory" in prompt_legal.lower() or "legal" in prompt_legal.lower()
```

- [ ] **Step 2: Implement `get_initial_prompt(profile_id)` in `src/asr/engine.py`**
Replace the hardcoded software engineering prompt with a dictionary of specialized domain prompts (`technical`, `medical`, `legal`, `financial`, `academic`, `general`).

- [ ] **Step 3: Run test and verify it passes**
Run: `pytest tests/test_asr.py -k "test_dynamic_initial_prompt" -v`
Expected: PASS.

---

### Task 3: Spoken Identifier Casing Engine (Developer, Data Science & Game Dev)

**Files:**
- Create: `src/utils/casing.py`
- Modify: `src/core/pipeline.py:120-140`
- Test: `tests/test_casing.py`

- [ ] **Step 1: Write unit tests for spoken casing transformations**
```python
# In tests/test_casing.py
from src.utils.casing import apply_casing_transforms

def test_camel_case_transform():
    assert apply_casing_transforms("camel parse auth token") == "parseAuthToken"
    assert apply_casing_transforms("state is modal open") == "isModalOpen"

def test_snake_case_transform():
    assert apply_casing_transforms("snake get user by id") == "get_user_by_id"

def test_pascal_case_transform():
    assert apply_casing_transforms("pascal user profile component") == "UserProfileComponent"

def test_screaming_snake_case_transform():
    assert apply_casing_transforms("constant max buffer size") == "MAX_BUFFER_SIZE"

def test_kebab_case_transform():
    assert apply_casing_transforms("kebab auth service deployment") == "auth-service-deployment"
```

- [ ] **Step 2: Implement `apply_casing_transforms` in `src/utils/casing.py`**
Implement regex pattern matchers for `r"\b(camel|state)\s+([a-zA-Z0-9\s]+?)(?=\s+(?:and|or|then|\.|$))"` and format into appropriate case conventions.

- [ ] **Step 3: Integrate `CasingStage` in `src/core/pipeline.py`**
Run `apply_casing_transforms` when `ctx.profile_id == "technical"` before syntax mapping.

- [ ] **Step 4: Run tests and verify**
Run: `pytest tests/test_casing.py -v`
Expected: PASS.

---

### Task 4: Expanded Syntax Map & Markdown/Voice Macros

**Files:**
- Modify: `src/utils/syntax_map.py`
- Test: `tests/test_syntax_map.py`

- [ ] **Step 1: Write tests for expanded operators, LaTeX, and Markdown**
```python
# In tests/test_syntax_map.py
def test_cpp_and_systems_operators():
    from src.utils.syntax_map import apply_syntax_map
    assert "->" in apply_syntax_map("player arrow get location")
    assert "::" in apply_syntax_map("std double colon vector")
    assert ":=" in apply_syntax_map("user short declare get user")
    assert "<-" in apply_syntax_map("data channel receive")

def test_markdown_and_emoji_macros():
    from src.utils.syntax_map import apply_syntax_map
    assert apply_syntax_map("heading one Introduction") == "# Introduction"
    assert apply_syntax_map("heading two Architecture") == "## Architecture"
    assert apply_syntax_map("thumbs up") == "👍"
    assert apply_syntax_map("rocket emoji") == "🚀"
```

- [ ] **Step 2: Expand `SYNTAX_MAPPINGS` in `src/utils/syntax_map.py`**
Add:
- C++/Rust/Go: `arrow` $\rightarrow$ `->`, `scope/double colon` $\rightarrow$ `::`, `short declare/walrus` $\rightarrow$ `:=`, `channel send/receive` $\rightarrow$ `<-`, `fat arrow` $\rightarrow$ `=>`.
- Markdown: `heading one` $\rightarrow$ `# `, `heading two` $\rightarrow$ `## `, `heading three` $\rightarrow$ `### `, `code block` $\rightarrow$ ```` ``` ````.
- Legal & Math: `section symbol` $\rightarrow$ `§`, `paragraph symbol` $\rightarrow$ `¶`, `alpha` $\rightarrow$ `\alpha`, `beta` $\rightarrow$ `\beta`, `summation` $\rightarrow$ `\sum`.
- Emojis: `thumbs up` $\rightarrow$ `👍`, `rocket emoji` $\rightarrow$ `🚀`, `fire emoji` $\rightarrow$ `🔥`, `eyes emoji` $\rightarrow$ `👀`.

- [ ] **Step 3: Run tests and verify**
Run: `pytest tests/test_syntax_map.py -v`
Expected: PASS.

---

### Task 5: App Context & Default Configuration Expansion

**Files:**
- Modify: `src/config/manager.py`
- Modify: `src/injection/window_detect.py`
- Test: `tests/test_window_detect.py`

- [ ] **Step 1: Update `DEFAULT_CONFIG["app_styles"]` in `src/config/manager.py`**
Pre-seed default styles:
```python
"app_styles": {
    "code.exe": "technical",
    "cursor.exe": "technical",
    "devenv.exe": "technical",
    "unrealeditor.exe": "technical",
    "rider64.exe": "technical",
    "goland64.exe": "technical",
    "pycharm64.exe": "technical",
    "windowsterminal.exe": "technical",
    "obsidian.exe": "technical",
    "slack.exe": "casual",
    "discord.exe": "casual",
    "outlook.exe": "email",
    "winword.exe": "formal",
    "excel.exe": "financial",
}
```

- [ ] **Step 2: Expand `APP_CONTEXT_MAP` in `src/injection/window_detect.py`**
Add:
- `devenv.exe`: "Visual Studio — C++/C# development"
- `unrealeditor.exe`: "Unreal Engine Editor — C++ game development"
- `discord.exe`: "Discord — casual, concise chat"
- `obsidian.exe`: "Obsidian — markdown knowledge base"
- `excel.exe`: "Microsoft Excel — financial & tabular data"
- `powerpnt.exe`: "Microsoft PowerPoint — executive presentation"

- [ ] **Step 3: Run window detect tests**
Run: `pytest tests/test_window_detect.py -v`
Expected: PASS.

---

### Task 6: Domain Style Profiles (Medical SOAP, Legal, Financial, PRD, Academic)

**Files:**
- Modify: `src/llm/style_profiles.py`
- Test: `tests/test_settings_and_widgets.py`

- [ ] **Step 1: Add new style profiles in `src/llm/style_profiles.py`**
Add:
- `medical`: ISMP dosage formatting (leading zero `0.5 mg`, omit trailing zero `1 mg`), SOAP structure, pharmacological terminology.
- `legal`: Statutory & Bluebook citations, defined terms capitalization, formal clause outline numbering.
- `financial`: Negative number parenthesis `(15.4M)`, basis points `25 bps`, multiples `8.5x EBITDA`, fiscal periods `1Q25`, `FY24`.
- `academic`: Passive voice methodology preservation, statistical notation ($p < 0.05$), SI units, and LaTeX formula preservation.
- `prd`: Feature specs, Gherkin syntax, acceptance criteria checklists `- [ ]`.

- [ ] **Step 2: Run test suite**
Run: `pytest tests/ -v`
Expected: PASS.

---

### Task 7: Multilingual Auto-Detection & Language Switcher

**Files:**
- Modify: `src/asr/engine.py:180-200`
- Modify: `src/config/manager.py`
- Modify: `src/gui/settings.py`
- Test: `tests/test_i18n.py`

- [ ] **Step 1: Write unit tests for language configuration and auto-detection**
```python
# In tests/test_i18n.py
def test_asr_engine_language_parameter(mock_asr_engine):
    mock_asr_engine.language = "auto"
    assert mock_asr_engine.resolve_language_param() is None  # Faster-Whisper auto-detect
    
    mock_asr_engine.language = "es"
    assert mock_asr_engine.resolve_language_param() == "es"
```

- [ ] **Step 2: Implement language selector in `src/gui/settings.py`**
Add QComboBox for Language: `Auto-Detect (99+ Languages)`, `English (en)`, `Spanish (es)`, `French (fr)`, `German (de)`, `Japanese (ja)`, `Chinese (zh)`, `Russian (ru)`, `Arabic (ar)`.

- [ ] **Step 3: Update `ASREngine.transcribe`**
Pass `language=self.resolve_language_param()` to Faster-Whisper.

- [ ] **Step 4: Run tests**
Run: `pytest tests/test_i18n.py -v`
Expected: PASS.

---

### Task 8: Dynamic Snippets with Parameters & Multi-line Support

**Files:**
- Modify: `src/gui/widgets/snippet_editor.py`
- Modify: `src/core/pipeline.py:75-95`
- Test: `tests/test_snippet_expansion.py`

- [ ] **Step 1: Write test for dynamic snippet placeholders**
```python
# In tests/test_snippet_expansion.py
from datetime import datetime

def test_dynamic_snippet_placeholders():
    from src.core.pipeline import expand_snippet_placeholders
    template = "Meeting date: {date}\nTime: {time}\nClipboard: {clipboard}"
    expanded = expand_snippet_placeholders(template, clipboard_content="Q3 Roadmap")
    assert datetime.now().strftime("%Y-%m-%d") in expanded
    assert "Q3 Roadmap" in expanded
```

- [ ] **Step 2: Upgrade `SnippetEditor` to `QPlainTextEdit`**
Allow users to create multi-line macro templates with `{date}`, `{time}`, `{clipboard}` tags.

- [ ] **Step 3: Update `SnippetStage` in `src/core/pipeline.py`**
Resolve placeholders dynamically upon snippet match.

- [ ] **Step 4: Run tests**
Run: `pytest tests/test_snippet_expansion.py -v`
Expected: PASS.

---

### Task 9: Enterprise Security & Auto-Updater Governance

**Files:**
- Modify: `src/core/updater.py:15-90`
- Modify: `src/llm/engine.py:250-285`
- Modify: `src/gui/settings.py`
- Test: `tests/test_updater_flow.py`

- [ ] **Step 1: Write security unit tests for auto-updater toggle and log sanitization**
```python
# In tests/test_updater_flow.py
def test_updater_disabled_by_config(mock_config):
    mock_config.set("auto_update_enabled", False)
    from src.core.updater import AutoUpdater
    updater = AutoUpdater(mock_config, None)
    assert updater.should_check_for_updates() is False

def test_logs_do_not_contain_raw_transcripts(caplog):
    # Verify logger only records text lengths, not raw user dictations
    import logging
    from src.llm/engine.py import LLMEngine
    # Verify no raw PII in warning logs
```

- [ ] **Step 2: Implement `auto_update_enabled` toggle in `src/config/manager.py` and `SettingsWindow`**
- [ ] **Step 3: Strip user transcript text from all log messages in `src/llm/engine.py`**
- [ ] **Step 4: Run all tests and verify production compile**
Run: `pytest` and `pyinstaller WhisperAI.spec --clean --noconfirm`
Expected: All tests pass, production `.exe` compiles cleanly.

---

### Final Score Projection
```text
┌─────────────────────────────────────────────────────────────┬──────────────┬──────────────┐
│ Dimension                                                   │ Baseline     │ Projected    │
├─────────────────────────────────────────────────────────────┼──────────────┼──────────────┤
│ 1. Developer / Data Science / Game Dev Workflow             │  51.0 / 100  │  96.0 / 100  │
│ 2. Business / Operations / Legal / HR Workflow              │  66.5 / 100  │  95.5 / 100  │
│ 3. Clinical Medical & Healthcare (HIPAA / ISMP)             │  52.0 / 100  │  94.5 / 100  │
│ 4. Academic Science & LaTeX Formatting                      │  46.0 / 100  │  95.0 / 100  │
│ 5. Multilingual & Internationalization (99+ Languages)      │  28.0 / 100  │  96.0 / 100  │
│ 6. Enterprise Security, Air-Gap & Zero-Trust Governance     │  62.0 / 100  │  96.5 / 100  │
├─────────────────────────────────────────────────────────────┼──────────────┼──────────────┤
│ OVERALL CROSS-INDUSTRY PRODUCTION SCORE                     │  58.8 / 100  │  95.6 / 100  │
└─────────────────────────────────────────────────────────────┴──────────────┴──────────────┘
```
