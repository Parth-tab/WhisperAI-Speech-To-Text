# Contributing to WhisperAI

Thank you for your interest in WhisperAI. To maintain the structural integrity and performance of this application, all contributions are held to rigorous standards.

## Mandatory Reading
Before proposing any changes, you **must** read and understand our core architectural documents:
- [AGENTS.md](AGENTS.md): The engineering philosophy, architecture constraints, and operational rules for this project.
- [ARCHITECTURE.md](ARCHITECTURE.md): The technical breakdown of our Split-Pass routing, P-Core affinity, and memory management constraints.

## Universal Standards
We hold human contributors to the exact same standards as our AI agents. Whether you are human or silicon, you must:
1. **Adhere to the Architecture**: Follow the precise folder conventions and dependency rules outlined in `AGENTS.md`.
2. **Never Break the Bundler**: All file loading must utilize `src.utils.paths.get_asset_path()`. Bare relative paths are strictly prohibited and will fail PyInstaller builds.

## CI Profiling & Testing Rules
Before marking any pull request as ready for review, you must enforce the CI profiling rules locally:
1. Run the test suite: `pytest`
2. Compile the executable to verify production viability: `pyinstaller WhisperAI.spec --clean`

A task is not considered complete until both the test suite passes flawlessly and the binary compiles without warnings or errors.

## Code Quality
- Ensure `ruff` and `mypy` compliance.
- Keep commits atomic and descriptive, following conventional commit formats (e.g., `feat:`, `fix:`).

By submitting a pull request, you confirm that you have read `AGENTS.md` and that your code passes all mandatory CI checks.
