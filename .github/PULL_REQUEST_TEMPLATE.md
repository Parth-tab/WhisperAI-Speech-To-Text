## 📋 Description
<!-- Provide a concise summary of what changes were made and the architectural rationale behind them. -->

## 🛠️ Type of Change
- [ ] 🐛 Bug fix (non-breaking change fixing an issue)
- [ ] ✨ New feature (domain syntax, casing transform, style profile, or widget)
- [ ] ⚡ Performance optimization (latency reduction, memory circuit breakers)
- [ ] 📚 Documentation & DevOps polish
- [ ] ♻️ Refactoring (no functional changes)

## ✅ Mandatory Pre-Submission Checklist
Before submitting this Pull Request, ensure that all of the following commands and checks have passed locally:

- [ ] **Tests:** Ran `pytest` and confirmed all **156 tests pass with 0 errors**.
- [ ] **Production Compilation:** Ran `pyinstaller WhisperAI.spec --clean --noconfirm` and confirmed `dist/WhisperAI.exe` builds cleanly.
- [ ] **Asset Resolution:** All file paths, icons, and models load via `src.utils.paths.get_asset_path()`.
- [ ] **Non-Blocking UI:** No blocking operations (`time.sleep()`, synchronous inference, modal dialogs like `QMessageBox`) were added to the Qt main thread.
- [ ] **Split-Pass Strategy:** Implemented complex formatting via rule-based regex / syntax maps rather than overloading the 1.5B LLM prompt.
- [ ] **Hardware Integrity:** No C-level hardware polling (`sd._terminate()`, `Pa_Initialize()`) in event callbacks.
- [ ] **Data Privacy:** Verified that no raw user dictation text is logged to disk.

## 🔗 Related Issues
Closes #
