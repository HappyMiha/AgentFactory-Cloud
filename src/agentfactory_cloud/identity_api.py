"""Optional router. Mount only under the product's reviewed transport boundary."""
import json
from fastapi import APIRouter, Header, HTTPException, Request, Response

from .access import AccessDenied

PRIVATE={'Cache-Control':'no-store','Referrer-Policy':'no-referrer'}


def identity_router(service):
    router=APIRouter(prefix='/identity',tags=['identity'])

    def error(status,code):
        raise HTTPException(status,detail={'code':code},headers=PRIVATE)

    def invoke(action):
        try:return action()
        except AccessDenied as exc:error(exc.status,exc.code)

    async def document(request,fields):
        raw=bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw)>4096:error(400,'invalid_request')
        try:
            def unique(pairs):
                result={}
                for key,value in pairs:
                    if key in result:raise ValueError()
                    result[key]=value
                return result
            value=json.loads(raw,object_pairs_hook=unique)
            if not isinstance(value,dict) or set(value)!=set(fields):raise ValueError()
            for key in fields:
                if key=='confirmed':
                    if type(value[key]) is not bool:raise ValueError()
                elif not isinstance(value[key],str) or not 1<=len(value[key])<=256:raise ValueError()
            return value
        except (ValueError,TypeError,UnicodeError,RecursionError):
            error(400,'invalid_request')  # Never echo supplied credentials or JSON.

    def peer(request):
        # Forwarded headers are not trusted. Proxy setup belongs to the host.
        if request.client is None:error(400,'invalid_client_context')
        return request.client.host

    def principal(request,authorization):
        if len(request.headers.getlist('authorization'))!=1 or authorization is None or not authorization.startswith('Bearer '):
            error(401,'authentication_required')
        return invoke(lambda:service.authenticate(authorization[7:]))

    def private(response):
        response.headers.update(PRIVATE)

    @router.post('/sessions')
    async def login(request:Request,response:Response):
        private(response);body=await document(request,{'account_id','secret'})
        token=invoke(lambda:service.login(body['account_id'],body['secret'],client_key=peer(request)))
        return {'access_token':token,'token_type':'Bearer','expires_in':service.session_ttl}

    @router.get('/session')
    def session(request:Request,response:Response,authorization:str|None=Header(default=None)):
        private(response);actor=principal(request,authorization)
        return {'account_id':actor.account_id,'authenticated':True}

    @router.delete('/session',status_code=204)
    def logout(request:Request,response:Response,authorization:str|None=Header(default=None)):
        private(response);actor=principal(request,authorization)
        invoke(lambda:service.logout(actor,client_key=peer(request)))

    @router.post('/recovery')
    async def recovery(request:Request,response:Response):
        private(response);body=await document(request,{'account_id','secret'})
        return invoke(lambda:service.recover(body['account_id'],body['secret'],client_key=peer(request)))

    @router.post('/account/deletion',status_code=202)
    async def delete(request:Request,response:Response,authorization:str|None=Header(default=None),
                     x_identity_confirm:str|None=Header(default=None)):
        private(response);actor=principal(request,authorization);body=await document(request,{'login_secret','confirmed'})
        if body['confirmed'] is not True or x_identity_confirm!='true':error(400,'confirmation_required')
        return invoke(lambda:service.request_deletion(actor,body['login_secret'],client_key=peer(request)))

    return router
