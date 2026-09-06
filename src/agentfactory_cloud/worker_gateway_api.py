"""Optional local-lab HTTP transport for worker admission; no remote launch API."""
import asyncio
import json
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from .worker_gateway import GatewayDenied


PRIVATE = {'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'}


def worker_gateway_router(gateway):
    router = APIRouter(prefix='/worker', tags=['worker-admission-lab'])

    def error(status, code):
        raise HTTPException(status, detail={'code': code}, headers=PRIVATE)

    async def invoke(call):
        try:
            return await asyncio.to_thread(call)
        except GatewayDenied as exc:
            error(exc.status, exc.code)
        except Exception:
            error(503, 'worker_gateway_unavailable')

    async def authenticate(request):
        # This release qualifies only explicit loopback requests. Proxy headers
        # never opt a remote client into the lab; no browser Origin is accepted.
        if (request.client is None or request.client.host not in ('127.0.0.1', '::1')
                or request.url.hostname not in ('127.0.0.1', 'localhost', '::1')
                or request.headers.getlist('origin')
                or request.headers.getlist('forwarded')
                or any(name.lower().startswith('x-forwarded-') for name in request.headers)):
            error(403, 'worker_transport_unqualified')
        headers = request.headers.getlist('authorization')
        if len(headers) != 1 or not headers[0].startswith('Bearer '):
            error(401, 'worker_authentication_required')
        token = headers[0][7:]
        await invoke(lambda: gateway.authenticate(token))
        return token

    async def document(request, fields):
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > 1024:
                error(400, 'invalid_worker_request')
            raw.extend(chunk)
        try:
            def unique(pairs):
                result = {}
                for key, value in pairs:
                    if key in result:
                        raise ValueError()
                    result[key] = value
                return result
            data = json.loads(raw, object_pairs_hook=unique)
            if not isinstance(data, dict) or set(data) != set(fields):
                raise ValueError()
            if (not isinstance(data['request_id'], str) or not 1 <= len(data['request_id']) <= 128
                    or not data['request_id'].isascii()
                    or any(not (c.isalnum() or c in '-_:.') for c in data['request_id'])):
                raise ValueError()
            if 'fencing_token' in fields and (type(data['fencing_token']) is not int or data['fencing_token'] < 1):
                raise ValueError()
            return data
        except (ValueError, TypeError, UnicodeError, RecursionError):
            error(400, 'invalid_worker_request')

    @router.post('/admissions')
    async def claim(request: Request):
        token = await authenticate(request)
        data = await document(request, ('request_id',))
        result = await invoke(lambda: gateway.claim(token, data['request_id']))
        return JSONResponse(result, headers=PRIVATE)

    @router.post('/admissions/renew')
    async def renew(request: Request):
        token = await authenticate(request)
        data = await document(request, ('request_id', 'fencing_token'))
        result = await invoke(lambda: gateway.renew(token, data['request_id'], data['fencing_token']))
        return JSONResponse(result, headers=PRIVATE)

    return router
