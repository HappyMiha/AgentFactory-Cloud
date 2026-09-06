"""Local read-only guidance composed behind the existing Core HTTP boundary."""
from pathlib import Path
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from agent_factory.http_auth import LocalHTTPBoundary
from .connection_guidance import guidance

def install_routes(app, workspace):
    if not any(m.cls is LocalHTTPBoundary for m in app.user_middleware):
        raise ValueError('Connection guidance requires the Core HTTP boundary')
    @app.get('/connections')
    def page():
        return FileResponse(Path(__file__).parent/'static/connections.html', headers={'Cache-Control':'no-store'})
    @app.get('/api/connection-guidance')
    def view(request:Request):
        principal=request.state.local_principal
        if principal is None or not ({'local','*'} & principal.tenants):
            raise HTTPException(403,'Connection guidance is unavailable.')
        if request.query_params:raise HTTPException(400,'No account information is accepted here.')
        try: result=guidance(actor=principal.actor,workspace=workspace)
        except (ValueError,KeyError,TypeError,OSError):
            raise HTTPException(503,'Connection guidance is unavailable.') from None
        return JSONResponse(result,headers={'Cache-Control':'no-store'})
