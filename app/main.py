import asyncio
import uvicorn
from fastapi import FastAPI, Request, Response

from app.data_model import response_data
from app.routers import verify_code_app


# app = FastAPI(title="FastAPI Tutorial", version="v1.0")        # Swagger交互文档运行本地js
app = FastAPI()

# 路由
prefix = '/v1'
app.include_router(verify_code_app.verify_code_app, prefix=prefix, tags=['验证码'])
# app.include_router(login_app.login_app, prefix=prefix, tags=['登录'])


@app.get('/health', tags=['健康检查'], response_model=str)
async def health():
    def run():
        return 'OK'
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, run)              # 通过线程异步运行
    return response_data(data=result)


if __name__ == '__main__':
    # "workers" flag is ignored when reloading is enabled.
    uvicorn.run("app.main:app", host='127.0.0.1', port=8000, workers=2, reload=True)
