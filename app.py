"""
AI Functions Workshop - Databricks App Backend

Serves the Next.js static frontend and provides API endpoints for:
- Triggering setup jobs per industry
- Polling job run status
- Fetching workshop context (catalog, schema, warehouse)
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from databricks.sdk import WorkspaceClient

app = FastAPI(title="AI Functions Workshop", docs_url=None, redoc_url=None)

# ---------------------------------------------------------------------------
# Databricks SDK client (uses ambient credentials from the Databricks App runtime)
# ---------------------------------------------------------------------------
def get_client() -> WorkspaceClient:
    return WorkspaceClient()


WORKSHOP_CATALOG = os.getenv("WORKSHOP_CATALOG", "main")
WORKSHOP_SCHEMA_PREFIX = os.getenv("WORKSHOP_SCHEMA_PREFIX", "ai_functions_workshop")


# ---------------------------------------------------------------------------
# API routes (registered before static file catch-all)
# ---------------------------------------------------------------------------

class SetupRequest(BaseModel):
    industry: str
    job_id: Optional[str] = None  # If provided, re-use this job instead of searching


@app.get("/api/config")
async def get_config():
    """Returns workspace config for display in the frontend."""
    try:
        client = get_client()
        me = client.current_user.me()
        return {
            "catalog": WORKSHOP_CATALOG,
            "schema_prefix": WORKSHOP_SCHEMA_PREFIX,
            "username": me.user_name,
        }
    except Exception as exc:
        return {"catalog": WORKSHOP_CATALOG, "schema_prefix": WORKSHOP_SCHEMA_PREFIX, "error": str(exc)}


@app.post("/api/setup")
async def trigger_setup(req: SetupRequest):
    """Triggers the setup job for the given industry. Returns the run_id for polling."""
    valid = {"gaming", "dnb", "telco", "fins", "mfg"}
    if req.industry not in valid:
        raise HTTPException(status_code=400, detail=f"industry must be one of {sorted(valid)}")

    client = get_client()

    # Find the setup job by name pattern
    job_id = req.job_id
    if not job_id:
        jobs = client.jobs.list(name="AI Functions Workshop - Setup")
        job_list = list(jobs)
        if not job_list:
            raise HTTPException(status_code=404, detail="Setup job not found. Run 'databricks bundle deploy' first.")
        # Pick the most recently modified job
        job_list.sort(key=lambda j: j.created_time or 0, reverse=True)
        job_id = str(job_list[0].job_id)

    waiter = client.jobs.run_now(
        job_id=int(job_id),
        notebook_params={"industry": req.industry},
    )
    return {"run_id": waiter.run_id, "job_id": job_id}


@app.get("/api/setup/status/{run_id}")
async def get_run_status(run_id: int):
    """Polls the status of a job run."""
    client = get_client()
    try:
        run = client.jobs.get_run(run_id=run_id)
        state = run.state
        return {
            "run_id": run_id,
            "life_cycle_state": state.life_cycle_state.value if state and state.life_cycle_state else None,
            "result_state": state.result_state.value if state and state.result_state else None,
            "state_message": state.state_message if state else None,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Static file serving (Next.js export in frontend/out/)
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).parent / "frontend" / "out"

if STATIC_DIR.exists():
    # Mount assets (JS, CSS, images) under /_next
    app.mount("/_next", StaticFiles(directory=STATIC_DIR / "_next"), name="next_assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Serve any route from the Next.js static export."""
        # Try the exact path first (e.g. /structured-extraction/index.html)
        candidates = [
            STATIC_DIR / full_path,
            STATIC_DIR / full_path / "index.html",
            STATIC_DIR / f"{full_path}.html",
            STATIC_DIR / "index.html",  # fallback to SPA root
        ]
        for candidate in candidates:
            if candidate.is_file():
                return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")
else:
    @app.get("/", include_in_schema=False)
    async def serve_placeholder():
        return JSONResponse(
            {
                "message": "Frontend not built yet. Run: cd frontend && npm install && npm run build",
                "api_docs": "/docs",
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
