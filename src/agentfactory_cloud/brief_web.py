"""Loopback creator intake, using Core local access; not a hosted tenant service."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt

from agent_factory.http_auth import COOKIE, LocalAccess, LocalHTTPBoundary
from .game_briefs import BriefConflict, BriefStore, FIELDS, LocalBriefModel
from .scope_plans import ScopePlans, LABELS, ENGINES, TARGETS
from .game_team_web import install_routes as install_team_routes
from .connection_guidance_web import install_routes as install_guidance_routes


class Command(BaseModel):
    model_config = ConfigDict(extra='forbid')
    command_id: str = Field(min_length=8, max_length=80, pattern=r'^[a-zA-Z0-9-]+$')


class Create(Command):
    original_text: str = Field(min_length=1, max_length=6000)


class Revision(Command):
    expected_revision: Annotated[StrictInt, Field(ge=1)]


class Edit(Revision):
    fields: dict[str, str]
    answers: dict[str, str] = Field(default_factory=dict)


class Login(BaseModel):
    model_config = ConfigDict(extra='forbid')
    token: str = Field(max_length=4096)


class ScopeDraft(Command):
    expected_brief_revision: Annotated[StrictInt, Field(ge=1)]


class ScopeEdit(ScopeDraft):
    expected_plan_revision: Annotated[StrictInt, Field(ge=1)]
    scope: dict


class ScopeAgree(ScopeDraft):
    expected_plan_revision: Annotated[StrictInt, Field(ge=1)]
    confirmed: StrictBool


class BodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] not in {'POST', 'PUT', 'PATCH'}:
            return await self.app(scope, receive, send)
        chunks = []; size = 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            size += len(message.get('body', b''))
            if size > 65536:
                return await JSONResponse({'detail': 'This request is too large.'}, status_code=413)(scope, receive, send)
            chunks.append(message)
            if not message.get('more_body', False):
                break
        async def replay():
            return chunks.pop(0) if chunks else await receive()
        await self.app(scope, replay, send)


def create_app(folder: Path, *, model=None):
    store = BriefStore(folder)
    plans = ScopePlans(store)
    access = LocalAccess()
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.brief_store = store
    app.add_middleware(BodyLimit)
    app.add_middleware(LocalHTTPBoundary, access=access)
    static = Path(__file__).parent / 'static'
    app.mount('/static', StaticFiles(directory=static), name='static')
    install_team_routes(app, store)
    install_guidance_routes(app, folder)

    def actor(request):
        return request.state.local_principal.actor

    @app.exception_handler(BriefConflict)
    async def conflict(request, error):
        return JSONResponse({'detail': str(error)}, status_code=409)

    @app.exception_handler(KeyError)
    async def missing(request, error):
        return JSONResponse({'detail': 'That idea or version is unavailable to this operator.'}, status_code=404)

    @app.exception_handler(ValueError)
    async def invalid(request, error):
        return JSONResponse({'detail': str(error)}, status_code=400)

    @app.get('/')
    def index():
        return FileResponse(static / 'brief.html')

    @app.get('/first-playable')
    def scope_page():
        return FileResponse(static / 'scope.html')

    @app.get('/api/briefs/{ident}/scope')
    def scope_latest(ident: str, request: Request):
        return {'plan': plans.latest(ident, actor(request)), 'labels': LABELS,
                'engines': ENGINES, 'targets': TARGETS}

    @app.post('/api/briefs/{ident}/scope')
    def scope_create(ident: str, request: Request, body: ScopeDraft):
        return plans.write(ident, actor(request), body.expected_brief_revision, body.command_id)

    @app.get('/api/briefs/{ident}/scope/{plan_id}')
    def scope_read(ident: str, plan_id: str, request: Request,
                   revision: Annotated[int | None, Query(ge=1)] = None):
        plan = plans.get(plan_id, actor(request), revision=revision)
        if plan['brief_id'] != ident:
            raise KeyError('Scope plan unavailable.')
        return plan

    @app.post('/api/briefs/{ident}/scope/{plan_id}/edit')
    def scope_edit(ident: str, plan_id: str, request: Request, body: ScopeEdit):
        return plans.write(ident, actor(request), body.expected_brief_revision, body.command_id,
                           ident=plan_id, expected_plan=body.expected_plan_revision, scope=body.scope)

    @app.post('/api/briefs/{ident}/scope/{plan_id}/agree')
    def scope_agree(ident: str, plan_id: str, request: Request, body: ScopeAgree):
        if body.confirmed is not True:
            raise ValueError('Review and confirm the saved scope first.')
        return plans.write(ident, actor(request), body.expected_brief_revision, body.command_id,
                           ident=plan_id, expected_plan=body.expected_plan_revision, agree=True)

    @app.post('/auth/login')
    def login(request: Request, body: Login):
        cookie = access.login(request.state.local_policy, body.token)
        if not cookie:
            raise HTTPException(401, 'Local access key was not accepted.')
        response = JSONResponse({'ok': True})
        response.set_cookie(COOKIE, cookie, httponly=True, samesite='strict',
                            secure=request.url.scheme == 'https', max_age=request.state.local_policy.ttl)
        return response

    @app.post('/auth/logout')
    def logout(request: Request):
        access.logout(request.cookies.get(COOKIE))
        response = JSONResponse({'ok': True}); response.delete_cookie(COOKIE)
        return response

    @app.get('/api/briefs')
    def items(request: Request):
        return {'items': store.list(actor(request)), 'fields': FIELDS, 'local_ai_enabled': model is not None,
                'model': model.model if model else None, 'profile': 'local-single-operator',
                'authentication_required': bool(request.state.local_policy.token),
                'build_enabled': False, 'publish_enabled': False}

    @app.post('/api/briefs')
    def create(request: Request, body: Create):
        return store.create(body.original_text, actor(request), body.command_id)

    @app.get('/api/briefs/{ident}')
    def read(ident: str, request: Request, revision: Annotated[int | None, Query(ge=1)] = None):
        return store.get(ident, actor(request), revision=revision)

    @app.post('/api/briefs/{ident}/edit')
    def edit(ident: str, request: Request, body: Edit):
        previous = store.get(ident, actor(request))
        proposal = {'fields': body.fields, 'assumptions': previous['assumptions'],
                    'questions': [q for q in previous['questions'] if q['field'] not in body.answers]}
        return store.save(ident, actor(request), body.expected_revision, body.command_id, proposal, answers=body.answers)

    @app.post('/api/briefs/{ident}/suggest')
    def suggest(ident: str, request: Request, body: Revision):
        try:
            return store.suggest(ident, actor(request), body.expected_revision, body.command_id, model)
        except (BriefConflict, ValueError, KeyError):
            raise
        except Exception:
            # Provider/OS errors can contain local paths or private text. Keep them local.
            raise HTTPException(503, 'Local AI is unavailable. Your saved idea is unchanged; you can edit it yourself.') from None

    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True, help='Private data directory outside the source checkout')
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--enable-local-ai', action='store_true', help='Explicitly permit bounded local inference on button press')
    parser.add_argument('--model', default='qwen2.5-coder:7b')
    args = parser.parse_args()
    model = LocalBriefModel(args.model) if args.enable_local_ai else None
    import uvicorn
    uvicorn.run(create_app(args.data, model=model), host='127.0.0.1', port=args.port, workers=1)


if __name__ == '__main__':
    main()
