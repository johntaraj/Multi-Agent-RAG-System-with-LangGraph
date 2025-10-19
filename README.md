# LangGraph Multi-Agent: Augmentor Agent

try here : https://multi-agent-rag-system-with-langgraph.streamlit.app/


<img width="1000" height="800" alt="image" src="https://github.com/user-attachments/assets/ea83948c-4fd9-4ef8-934e-2a34c865fca9" />

An AI-powered research and content generation assistant built with LangGraph/LangChain and Streamlit. The system orchestrates multiple specialized agents (Planner -> Researcher -> Prompt Augmentor -> Generator) to plan searches, gather context from the web, refine your request, and produce a final result. Debug outputs for each stage are written to `debug_output/` for transparency and troubleshooting.

Highlights:
- Multi-agent pipeline: planner, researcher, augmentor, generator
- Google Gemini models via `langchain_google_genai`
- Web search via Tavily (`tavily-python`)
- Streamlit UI with file uploads (PDF/TXT/PY)
- Optional LangGraph graph orchestration (experimental) and a sequential backend


## Quick Start

Prerequisites:
- Python 3.10+ (3.11 recommended)
- Google API key for Gemini (`GOOGLE_API_KEY`)
- Tavily API key (`TAVILY_API_KEY`)

1) Clone and enter the project
```
git clone https://github.com/<your-username>/<your-repo>.git
cd LangGraph_Multi_Agent
```

2) Create and activate a virtual environment
- Windows (PowerShell)
```
python -m venv .venv
.venv\Scripts\Activate.ps1
```
- macOS/Linux
```
python -m venv .venv
source .venv/bin/activate
```

3) Install dependencies
```
pip install -r requirements.txt
```

4) Configure environment variables
Create a `.env` file in `LangGraph_Multi_Agent/` with:
```
# Required
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key

# Optional (for LangSmith tracing/debugging)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
```

Security note: do NOT commit `.env`. Add it to `.gitignore` before pushing to GitHub:
```
# .gitignore
.env
.venv/
debug_output/
__pycache__/
```

5) Run the Streamlit app (recommended)
```
streamlit run app.py
```
Open the provided local URL in your browser.


## How It Works

Agent steps:
- Planner: creates a small search plan for your request
- Researcher: runs web search (Tavily) and aggregates sources/content
- Prompt Augmentor: rewrites your prompt using gathered context, or asks clarifying questions
- Generator: produces the final response using Gemini

Debugging: each step writes a JSON file into `debug_output/`:
- `1_planner_output.json`
- `2_researcher_output.json`
- `3_augmentor_output.json`
- `4_generator_output.json`


## Usage (Streamlit UI)

1) Enter your request in the chat input.
2) Optionally upload files (PDF/TXT/PY). The UI will show how many files are attached.
3) In the sidebar, choose the Gemini models (defaults provided):
   - `gemini-2.5-flash` or `gemini-2.5-flash-lite`
4) Submit and watch the assistant plan, research, and generate.
5) Click "Sources" to view links collected during research.

Notes:
- File-based RAG hooks are scaffolded in the researcher but minimal by default. Extend as needed for your use case.
- The app shows follow-up questions when the augmentor determines more info is needed.


## Project Structure

```
LangGraph_Multi_Agent/
- app.py            # Streamlit UI
- backend.py        # Sequential pipeline orchestration used by the UI
- agents.py         # Agent logic + debug file writes
- tools.py          # Tavily search tool
- main.py           # Graph-based CLI prototype (experimental)
- requirements.txt  # Python dependencies
- .env              # Environment variables (do not commit)
- debug_output/     # JSON outputs for each step
```


## Configuration

- Models: the Streamlit sidebar lets you pick Gemini models per agent (planner/augmentor/generator). Defaults: `gemini-2.5-flash`.
- Temperature: agents use temperature 0 in code for deterministic outputs; adjust in `agents.py` if needed.
- Search: Tavily results count is configured in `tools.py` (`k=5`).


## CLI (Experimental)

There is a graph-based CLI prototype in `main.py` that compiles a LangGraph and streams step outputs. It currently requires minor refactoring to pass model names into nodes; the recommended interface is the Streamlit app via `app.py`.

Run (if you choose to experiment):
```
python main.py
```


## Troubleshooting

- Missing or invalid API key
  - Ensure `GOOGLE_API_KEY` and `TAVILY_API_KEY` are present in `.env` and the venv is active.
- Tavily 401/403
  - Verify your Tavily key and usage limits; set `TAVILY_API_KEY` in `.env`.
- Gemini model errors
  - Confirm the selected model exists and is available to your Google API key.
- Nothing shows up in the UI
  - Check the Streamlit terminal output for errors; see `debug_output/*.json`.
