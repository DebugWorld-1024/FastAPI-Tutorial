from enum import Enum
from typing import Union
from fastapi import status
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from app.response_status_code import ResponseStatusCode


def response_data(*, code: int = ResponseStatusCode.OK.code,
                  message: str = ResponseStatusCode.OK.message,
                  data: Union[list, dict, str, bool, None] = None) \
        -> JSONResponse:
    """
    API 统一响应数据格式
    :param code: 状态码, 200: Success
    :param message: 接口错误信息
    :param data: 数据
    :return:
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'code': code,
            'message': message,
            'data': data,
        }
    )


class CodeEnum(str, Enum):
    success = "成功"
    fail = "失败"


class TokenInfo(BaseModel):
    user_id: int = Field(title="用户ID", example=1)
    username: str = Field(title="用户名", example="admin")
    # password: str = Field(title="密码", example="OryE/KAY1JwhSyX+tM5mFQ==")
    scopes: list = Field(title="scopes", example=["Backend"])
    exp: int = Field(default=None, title="Token 有效期")


class VerifyCodeOut(BaseModel):
    verify_image: str = Field(title="验证码", example='ot3R')
    verify_code_token: str = Field(title="验证码token", example='HsQK3Jsc6BmKg+TZYkjEjQ==')


class SystemLoginOut(BaseModel):
    access_token: str = Field(title='用户的token')
    token_type: str = Field(example='bearer')
    user_id: int = Field(title='用户ID')
    username: str = Field(title='用户名字')


class UpdatePasswordIn(BaseModel):
    verify_code: str = Field(default=None, title="验证码", example='ot3R')
    verify_code_token: str = Field(default=None, title="验证码token", example='HsQK3Jsc6BmKg+TZYkjEjQ==')
    username: str = Field(title='用户名', example='test')
    old_password: str = Field(title='旧密码', example='OryE/KAY1JwhSyX+tM5mFQ==')
    new_password: str = Field(title='新密码', example='OryE/KAY1JwhSyX+tM5mFQ==')


class UpdatePasswordOut(BaseModel):
    username: str = Field(title='用户名字', example='admin')