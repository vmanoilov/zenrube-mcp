from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any

from zenrube.experts.semantic_router import SemanticRouterExpert
from zenrube.experts.expert_registry import ExpertRegistry
from zenrube.experts_module import get_expert

app = FastAPI(title="ZenRube API", version="1.0.0")

semantic_router = SemanticRouterExpert()
expert_registry = ExpertRegistry()

class RouteRequest(BaseModel):
    prompt: str

class RouteResponse(BaseModel):
    routes: List[str]
    raw: Any

class RunRequest(BaseModel):
    expert: str
    prompt: str

class RunResponse(BaseModel):
    result: str

@app.post("/route", response_model=RouteResponse)
def route(req: RouteRequest):
    try:
        result = semantic_router.run(req.prompt)
        routes = []

        if isinstance(result, dict):
            if "route" in result:
                routes = result["route"] if isinstance(result["route"], list) else [result["route"]]
            elif "expert" in result:
                routes = result["expert"] if isinstance(result["expert"], list) else [result["expert"]]

        if not routes:
            routes = ["general_handler"]

        return RouteResponse(routes=routes, raw=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run", response_model=RunResponse)
def run(req: RunRequest):
    try:
        try:
            expert = expert_registry.load_expert(req.expert)
            output = expert.run(req.prompt)
            return RunResponse(result=str(output))
        except Exception:
            expert_def = get_expert(req.expert)
            output = expert_def.build_prompt(req.prompt)
            return RunResponse(result=str(output))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/experts")
def list_experts():
    try:
        reg = list(expert_registry.list_available_experts())
        from zenrube.experts_module import list_experts as core_list
        core = list(core_list())
        return sorted(set(reg + core))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
