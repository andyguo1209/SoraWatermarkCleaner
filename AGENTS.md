# Repository Guidelines

## Project Structure & Module Organization
- `sorawm/` contains the cleaning pipeline: `core.py` orchestrates tasks, `watermark_detector.py` loads YOLOv11 weights, `server/` exposes FastAPI, and `utils/` hosts shared helpers.
- `frontend/` drives the Streamlit UI (`pages/`, `navigation.py`, `styles.py`); static assets and weights live in `resources/`, while sample inputs stay in `data/`.
- Training inputs sit under `datasets/` and configuration notebooks in `notebooks/`; keep experiments referenced by dataset name.
- Generated artefacts (`output/`, `logs/`, `working_dir/`, database files) are runtime-only—inspect locally, never commit.

## Build, Test, and Development Commands
- `uv sync` installs the locked Python 3.12 environment from `pyproject.toml` and `uv.lock`.
- `uv run python example.py` processes `resources/dog_vs_sam.mp4` end-to-end; update paths when showcasing new clips.
- `uv run streamlit run app.py` launches the UI; `uv run python quick_start.py` seeds the DB then starts backend and front end together.
- `uv run python start_server.py` spins up the FastAPI service on port 5344 for integration testing.
- `uv run pytest` runs the full suite; scope to CPU-only checks with `uv run pytest sorawm/iopaint/tests -k cpu`.

## Coding Style & Naming Conventions
- Follow PEP 8 with four-space indents; annotate public methods and keep module constants uppercase.
- Name modules and files `lowercase_with_underscores`; Streamlit session keys stay snake_case, API payload keys mimic upstream camelCase.
- Document non-obvious logic inline and stage shared utilities in `sorawm/utils/` before reuse.

## Testing Guidelines
- Prefer pytest parametrization for new datasets; store fixtures in `datasets/` and reference via relative paths.
- Gate GPU-dependent tests with `@pytest.mark.skipif` and explain the hardware requirement in the docstring.
- Capture before/after frames or PSNR metrics in `outputs/<timestamp>/` and attach to the PR summary.

## Commit & Pull Request Guidelines
- Use Conventional Commits (`feat:`, `fix:`, `chore:`) under 70 characters; group files by area (e.g., `feat: ui navigation tweaks`).
- PRs should describe user impact, link issues or experiment notes, and call out required models or environment variables.
- Confirm evaluation artefacts, weights, and `.auth_state.json` remain untracked; add screenshots or run logs for substantive changes.

## Security & Configuration Tips
- Load database credentials, `UNIVERSAL_VERIFICATION_CODE`, and provider keys from the environment; never embed secrets in code.
- Allow the app to download `best.pt` and LaMa weights automatically, then verify checksums before promoting builds.
- Document ffmpeg, CUDA, or inference tuning in `PERFORMANCE_OPTIMIZATION.md` so deployments stay reproducible.
