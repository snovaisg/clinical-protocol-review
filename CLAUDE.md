# CLAUDE.md

## Project Structure

- `streamlit_app.py` — Local Streamlit app (uses `.env` for API key, writes reports to disk)
- `app_hf.py` — Hugging Face Spaces Streamlit app (sidebar API key, in-memory ZIP download)
- `agents/` — LangChain-based review agents (PI, Site Physician, Health Authority, Protocol Generator)
- `utils/` — Document processor, risk assessor, scoring engine
- `mcp_interface/` — Model Context Protocol server and tools
- `templates/` — ICH protocol templates
- `example-protocols/` — Sample protocol PDFs (local only, not deployed to HF)

## Hugging Face Spaces Deployment

The app is deployed at: https://huggingface.co/spaces/snovaisg/clinical-protocol-reviewer

### HF Space local repo

The Space is cloned at `/tmp/hf-space-test/` and has its own git remote pointing to HF. It is a Docker-based Space (SDK: docker) running Streamlit on port 8501.

### Workflow for updating the HF Space

When making changes to `app_hf.py` or any file that affects the HF Space:

1. **Edit both copies** — update the file in this project AND in `/tmp/hf-space-test/`
2. **Commit and push the Space repo**:
   ```bash
   cd /tmp/hf-space-test
   git add <changed-files>
   git commit -m "Description of change"
   git push origin main
   ```
3. The Space rebuilds automatically after each push. Monitor build logs at the Space URL.

### Key differences from local app

- No `.env` file — users provide their OpenAI API key via sidebar
- No `example-protocols/` in the Space — HF rejects binary files in git pushes. The "Use Example Protocol" button is gated behind `os.path.exists()` so it simply doesn't appear.
- No `FileHandler` logging — only `StreamHandler` (no persistent filesystem on HF)
- Reports are generated as in-memory ZIPs instead of writing to disk
- `.streamlit/config.toml` disables XSRF protection and CORS (required for file uploads behind HF's reverse proxy)

### Files in the Space repo (`/tmp/hf-space-test/`)

- `Dockerfile` — Builds the Docker image, installs deps, runs `app_hf.py`
- `README.md` — HF metadata header (title, SDK, app_port, etc.)
- `requirements.txt` — Python dependencies (mirrors `pyproject.toml`)
- `.streamlit/config.toml` — Disables XSRF/CORS for HF compatibility
- `app_hf.py`, `agents/`, `utils/`, `mcp_interface/`, `templates/` — App code

### Adding new Python dependencies

Add to both `pyproject.toml` (this project) and `requirements.txt` (HF Space). Also update `/tmp/hf-space-test/requirements.txt`.
