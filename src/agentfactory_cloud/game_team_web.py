"""Local operator-bound team proposal; no live provider or stop endpoint."""
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from pathlib import Path
from .game_team import GameTeams

class AssessTeam(BaseModel):
    model_config=ConfigDict(extra="forbid")
    expected_digest: str=Field(pattern=r"^[a-f0-9]{64}$")
    confirmed: StrictBool


def install_routes(app, briefs):
    teams=GameTeams(briefs)
    def actor(request):
        p=request.state.local_principal
        if p is None or not ({"local","*"}&p.tenants):raise HTTPException(403,"Team access is unavailable.")
        return p.actor
    @app.get("/game-team")
    def page():return FileResponse(Path(__file__).parent/"static/game-team.html")
    @app.get("/api/briefs/{ident}/team")
    def view(ident:str,request:Request):
        return JSONResponse(teams.view(ident,actor(request)),headers={"Cache-Control":"no-store"})
    @app.post("/api/briefs/{ident}/team/assess")
    def assess(ident:str,request:Request,body:AssessTeam):
        if body.confirmed is not True:raise HTTPException(400,"Confirm the gap assessment first.")
        return JSONResponse(teams.assess(ident,actor(request),body.expected_digest),headers={"Cache-Control":"no-store"})
