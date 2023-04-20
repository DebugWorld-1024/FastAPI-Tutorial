import os
import json
import time
import asyncio
import uvicorn
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI, Request, Response
from starlette.background import BackgroundTask
from fastapi.exceptions import HTTPException, ValidationError, RequestValidationError
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html

from app.data_model import response_data
from app.response_status_code import ResponseStatusCode
from app.routers import login_app, verify_code_app, file_app, background_task_app


app = FastAPI(title="FastAPI Tutorial", version="v1.0", docs_url=None, redoc_url=None)          # Swagger交互文档运行本地js
app.mount(path="/static", name="static",                                                        # Swagger本地js位置
          app=StaticFiles(directory=os.path.join(os.path.split(os.path.realpath(__file__))[0], 'static')))


# 路由
prefix = '/v1'
app.include_router(login_app.login_app, prefix=prefix, tags=['登录操作'])
app.include_router(verify_code_app.verify_code_app, prefix=prefix, tags=['验证码'])
app.include_router(file_app.file_app, prefix=prefix, tags=['文件操作'])
app.include_router(background_task_app.background_task_app, prefix=prefix, tags=['后台任务'])


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    重写主动抛出的HTTPException异常
    :param request: 请求信息
    :param exc: 异常信息
    :return: 响应信息
    """
    content = {
        'code': exc.status_code,
        'message': str(exc.detail),
        "data": None
    }
    return JSONResponse(status_code=200, content=content, headers=exc.headers,)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    重写校验Request参数的异常
    :param request: 请求信息
    :param exc: 异常信息
    :return: 响应信息
    """
    content = {
        'code': ResponseStatusCode.REQUEST_VALIDATION_ERR.code,
        'message': ResponseStatusCode.REQUEST_VALIDATION_ERR.message + ': ' + str(exc.errors()),
        "data": None
    }
    return JSONResponse(status_code=200, content=content)


@app.exception_handler(ValidationError)
async def response_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    重写校验response_model的异常
    :param request: 请求信息
    :param exc: 异常信息
    :return: 响应信息
    """
    content = {
        'code': ResponseStatusCode.RESPONSE_VALIDATION_ERR.code,
        'message': ResponseStatusCode.RESPONSE_VALIDATION_ERR.message + ': ' + str(exc.errors()),
        "data": None
    }
    return JSONResponse(status_code=200, content=content)


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    重写未知异常, Exception不跳转到中间件
    :param request: 请求信息
    :param exc: 异常信息
    :return: 响应信息
    """
    content = {
        'code': ResponseStatusCode.ERROR.code,
        'message': str(exc),
        "data": None
    }
    background = BackgroundTask(background_task_app.background_task_middleware, request,
                                bytes(json.dumps(content), encoding='utf-8'))
    return JSONResponse(status_code=200, content=content, background=background)


@app.middleware('http')
async def add_process_time_header(request: Request, call_next):
    """
    记录每个Request运行时间(ms), 添加到header
    :param request:
    :param call_next:
    :return:
    """

    # request_body = dict()
    # request_body = await request.receive()
    #
    # async def set_body():
    #     return request_body
    #
    # request._receive = set_body

    request.state.audit_log = None
    start_time = time.time() * 1000
    response = await call_next(request)
    process_time = time.time() * 1000 - start_time
    response.headers['X-Process-Time'] = str(process_time)                                  # 添加自定义的以“X-”开头的请求头
    # return response

    response_body = b""
    async for item in response.body_iterator:                                               # 获取响应数据
        response_body += item

    response.background = BackgroundTask(background_task_app.background_task_middleware,
                                         request, response_body)                            # 后台运行，防止阻塞
    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=response.headers,
        media_type=response.media_type,
        background=response.background
    )


@app.get('/health', tags=['健康检查'], response_model=str)
async def health():
    def run():
        return 'OK'
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, run)              # 通过线程异步运行
    return response_data(data=result)


def custom_openapi():
    """
    remove swagger 422 response
    :return:
    """
    if not app.openapi_schema:
        app.openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            terms_of_service=app.terms_of_service,
            contact=app.contact,
            license_info=app.license_info,
            routes=app.routes,
            tags=app.openapi_tags,
            servers=app.servers,
        )
        for _, method_item in app.openapi_schema.get('paths').items():
            for _, param in method_item.items():
                responses = param.get('responses')
                # remove 422 response, also can remove other status code
                if '422' in responses:
                    del responses['422']
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == '__main__':
    # "workers" flag is ignored when reloading is enabled.
    uvicorn.run("app.main:app", host='127.0.0.1', port=8000, workers=2, reload=True)

