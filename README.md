# Autonomous Blog Generation Agent

Production-grade content generation engine built with a staged architecture:

1. Environment setup and dependency management with UV
2. Multi-agent DAG orchestration with LangGraph
3. Microservice API layer with FastAPI
4. Observability and tracing with LangSmith

## Architecture Mapping

### Stage 1: Environment Setup (UV)
- Dependency source of truth: [pyproject.toml](pyproject.toml)
- Install and sync:

```bash
uv sync
```

### Stage 2: Multi-Agent DAG (LangGraph)
Graph implementation: [app/graph/workflow.py](app/graph/workflow.py)

Current flow:
- `router` decides both `needs_web_search` and `needs_translation`
- `web_search` (Tavily) runs when fresh web evidence is required
- `llm_knowledge` runs when direct model knowledge is sufficient
- `brainstorming` generates blog title and final section headings
- `content_generation` writes the full blog draft
- `image_generator` always runs after content generation
- `translator` runs only if `needs_translation` from `router` is true
- `seo_reducer` trims and optimizes output (meta description + keywords)
- `save_memory` persists state transitions through AsyncSqliteSaver checkpoints

Conditional routes:
- After `router`: `web_search` -> `brainstorming`, else `llm_knowledge` -> `brainstorming`
- After `image_generator`: `translator` -> `seo_reducer`, else directly `seo_reducer`
- Final path: `seo_reducer` -> `save_memory` -> end

### Stage 3: Microservice API (FastAPI)
API router: [app/api/blog.py](app/api/blog.py)
App entrypoint: [app/main.py](app/main.py)

Primary generation endpoint:
- `POST /api/v1/generate_blog`

Backward-compatible alias:
- `POST /api/v1/generate`

Example request:

```json
{
	"topic": "The Future of AI in Healthcare",
	"target_language": "english"
}
```

### Stage 4: Observability (LangSmith)
LangSmith is enabled via environment variables and run metadata attached in API calls.

Required `.env` values:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=autonomous-blog-agent
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
HF_API_KEY=your_huggingface_key
```

## Run Locally

Start FastAPI with UV:

```bash
uv run uvicorn app.main:app --reload
```

Open:
- App UI: `http://127.0.0.1:8000/`
- Swagger: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

## Frontend

The UI is served by FastAPI (no Streamlit).

- HTML: [app/static/index.html](app/static/index.html)
- CSS: [app/static/styles.css](app/static/styles.css)
- JS: [app/static/app.js](app/static/app.js)
