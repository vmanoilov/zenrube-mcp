# zenrube/http/fs_agent_server.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from zenrube.agent_runtime.fs_loop import FsAgentLoop

app = FastAPI(title="ZenRube FS-Agent Server", version="1.0.0")


# -----------------------------
#   Request Models
# -----------------------------

class FsLoopRequest(BaseModel):
    goal: str


# -----------------------------
#   Endpoints
# -----------------------------

@app.post("/fs/loop")
def run_fs_loop(req: FsLoopRequest):
    """
    Run the filesystem autonomous loop.
    """
    try:
        loop = FsAgentLoop(root="/workspaces/ZenRube")   # <-- FIXED (no execute_plan_fn)
        result = loop.run(req.goal)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "ZenRube FS-Agent Server",
        "endpoints": ["/fs/loop"]
    }
