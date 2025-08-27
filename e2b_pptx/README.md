## PowerPoint & Finance Dashboard Generator

This Streamlit app uses a LangChain agent to:
- Generate downloadable PowerPoint files using python-pptx (local execution)
- Generate finance dashboards. Non-Streamlit code runs in a secure Pyodide sandbox; Streamlit dashboards run locally via a temporary subprocess

### Architecture
- UI: Streamlit (`main.py`, `ui/streamlit_app.py`)
- Agent: LangGraph + Anthropic model (`core/agent.py`, `core/prompts.py`)
- Tools:
  - `tools/presentation.py`: Executes provided python-pptx code locally, collects any `.pptx` files, and exposes them for download. Outputs saved under `generated_presentations/`.
  - `tools/yf_stocks.py`: Generates finance code. Execution modes:
    - If the generated code does not use Streamlit: run with `PyodideSandbox` (WebAssembly) for isolated, stateful execution. No file I/O.
    - If the generated code uses Streamlit: write code to a temp dir and launch `streamlit run` on a free localhost port. A 5-minute auto-shutdown is enforced.

### Prerequisites
- Python 3.10+
- Deno (required by `langchain-sandbox` for Pyodide). Install from `https://docs.deno.com/runtime/getting_started/installation/`
- Anthropic API key (for the agent)

### Setup
```bash
# From project root
python3 -m venv e2b_pptx/.venv
source e2b_pptx/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r e2b_pptx/requirements.txt
```

Environment variables (create `e2b_pptx/.env`):
```env
ANTHROPIC_API_KEY=your_anthropic_api_key
LANGCHAIN_PROJECT=e2b-pptx
```

Note: E2B is no longer required. Any E2B values in `config/settings.py` are not used by the current flow.

### Run
```bash
cd e2b_pptx
streamlit run main.py
```
App will be available at `http://127.0.0.1:8501`.

### How it works
1) Chat with the agent in the Streamlit UI.
2) For presentation requests, the agent calls `create_presentation` with python-pptx code. The code is executed locally; any `.pptx` files are moved to `generated_presentations/` and exposed with download buttons.
3) For finance dashboards, the agent calls `generate_python_dashboard`:
   - Non-Streamlit code → executed in `PyodideSandbox` (stateful=True, allow_net=True). Returned outputs include stdout/stderr; no URLs or files.
   - Streamlit code → written to a temp folder and launched with `streamlit run` on an available port. The tool returns a local URL. A background timer terminates the process after 5 minutes.

### Limits & Notes
- Pyodide sandbox:
  - No file system access. Files written by the code aren’t accessible.
  - Network: prefer `httpx` over `requests` if external calls are required.
  - First run may incur a few seconds of startup latency.
- Streamlit subprocess:
  - Auto-shutdown after 5 minutes.
  - If a port is occupied, the tool selects the next free port.
- Presentations are saved under `generated_presentations/` and can be downloaded from the UI.

### Troubleshooting
- Missing packages (e.g., `yfinance`, `plotly`):
  - Ensure you installed `requirements.txt` in the active venv
- Deno not found:
  - Install Deno and ensure it’s on PATH. Restart your shell.
- Streamlit won’t start:
  - Check venv activation, run `python -m pip install -r requirements.txt`
  - Try another port: `streamlit run main.py --server.port 8502`
- Anthropic auth errors:
  - Confirm `ANTHROPIC_API_KEY` in `e2b_pptx/.env`

### References
- Streamlit docs: https://docs.streamlit.io
- python-pptx: https://python-pptx.readthedocs.io
- LangChain Sandbox: https://pypi.org/project/langchain-sandbox/
