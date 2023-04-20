import time
import json
from jose import jwt

from library.constants import JWTConfig
from app.routers.login_app import verify_token
from app.data_model import TokenInfo, response_data
from fastapi import APIRouter, Security, Depends, BackgroundTasks, Request, Query


background_task_app = APIRouter()

"""
background_task有三种方式
1、中间件(middleware)
2、依赖注入(Depends)
3、请求方法里(BackgroundTasks)
"""


def background_task_middleware(request: Request, response_body: bytes):
    """
    通过中间件(middleware)执行后台任务
    :param request:
    :param response_body:
    :return:
    """
    audit_data = request.state.audit_log
    if audit_data:
        response_body = json.loads(response_body)
        data = {
            'client_host': request.client.host,
            'request_url': request.url,
            'request_method': request.method,
            'action_type': audit_data.action_type,
            'request_body': audit_data.request_body,
            'code': response_body['code'],
            'message': response_body['message']
        }
        print(data)


def background_task_depends(background_task: BackgroundTasks, request: Request):
    """
    通过依赖注入(Depends)执行后台任务
    :param background_task:
    :param request:
    :return:
    """
    def insert_log():
        time.sleep(5)
        if token := request.headers.get('Authorization', '').replace('Bearer ', ''):
            payload = jwt.decode(token, JWTConfig.SECRET_KEY, algorithms=[JWTConfig.ALGORITHM])
            token_info = TokenInfo(**payload)
            data = {
                'client_host': request.client.host,
                'username': token_info.username,
            }
            print(data)

    background_task.add_task(insert_log)


def background_task_method():
    """
    在请求方法里(BackgroundTasks)执行后台任务
    :return:
    """
    time.sleep(4)
    print('I am background_task_test2')


@background_task_app.get("/background_task/test", dependencies=[Security(verify_token, scopes=["Read"]),
                                                                Depends(background_task_depends)],
                         description='通过依赖注入(Depends)执行后台任务')
async def test(s: str = Query(example='s'), s1: str = Query(example='s1')):
    return response_data(data=f'{s} {s1}')


@background_task_app.get('/background_task/test2',
                         dependencies=[Security(verify_token, scopes=["Read"])],
                         description="在请求方法里(BackgroundTasks)执行后台任务")
async def test2(background_task: BackgroundTasks, s: str = Query(example='s'), s1: str = Query(example='s1')):
    background_task.add_task(background_task_method)
    return response_data(data=f'{s} {s1}')
