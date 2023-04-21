import json
import string
from jose import jwt
from typing import Union
from copy import deepcopy
from fastapi import APIRouter, Body
from datetime import datetime, timedelta
from fastapi import Depends, Security, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes

from app.response_status_code import ResponseStatusCode
from app.routers.verify_code_app import deal_verify_code
from app.data_model import response_data, SystemLoginOut, UpdatePasswordIn, TokenInfo, AuditLog


from library.util import aes_decrypt
from library.constants import AESConfig, JWTConfig


login_app = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/login", scopes={"Read": "只读权限", "Write": "写入权限"})


# faker data 真实情况需要查询数据库
users_info = {
    'admin': {
        'user_id': 1,
        'username': 'admin',
        'password': 'yO/tB92KdA+Om4Jmj0/sdQ=='
    },
    'test': {
        'user_id': 2,
        'username': 'test',
        'password': 'yO/tB92KdA+Om4Jmj0/sdQ=='
    }
}


def authenticate_user(username: str, password: str):
    """
    登录时校验账号
    :param username:
    :param password:
    :return:
    """
    # sql = f"""
    #     SELECT  id AS user_id
    #             ,username
    #             ,password
    #     FROM    {DataBase.}.{TableName.USER_INFO}
    #     WHERE   username = %s
    #     AND     password = %s
    # """
    # user_info = mysql_client.read_as_dict(sql=sql, params=[username, password])

    if not ((user_info := users_info.get(username, None)) and (user_info['password'] == password)):
        raise HTTPException(
            status_code=ResponseStatusCode.USER_PASSWORD_ERR.code,
            detail=ResponseStatusCode.USER_PASSWORD_ERR.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_info


def create_access_token(token_info: TokenInfo, expires_delta: Union[timedelta, None] = None):
    """
    生成JWT认证信息token
    :param token_info:
    :param expires_delta:
    :return:
    """
    to_encode = deepcopy(token_info)
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=1)
    to_encode.exp = expire

    encoded_jwt = jwt.encode(to_encode.dict(), JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM)
    return encoded_jwt


async def verify_token(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)) -> TokenInfo:
    """
    校验token
    :param security_scopes:
    :param token:
    :return:
    """
    try:
        payload = jwt.decode(token, JWTConfig.SECRET_KEY, algorithms=[JWTConfig.ALGORITHM])
    except Exception as e:
        raise HTTPException(status_code=ResponseStatusCode.TOKEN_ERR.code,
                            detail=ResponseStatusCode.TOKEN_ERR.message + ': ' + str(e))

    # TODO tokens_data 过期处理
    # if not tokens_data.get(payload['user_id'], None):
    #     raise HTTPException(status_code=ResponseStatusCode.UNAUTHORIZED_ERR.code,
    #                         detail=ResponseStatusCode.UNAUTHORIZED_ERR.message)

    # 校验scopes
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    token_scopes = payload.get("scopes", [])

    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=ResponseStatusCode.SCOPES_CODE_ERR.code,
                detail=ResponseStatusCode.SCOPES_CODE_ERR.message + f'Token权限: {token_scopes}, 接口权限: {security_scopes.scopes}',
                headers={"WWW-Authenticate": authenticate_value},
            )
    return TokenInfo(**payload)


def verify_password(password: str):
    """
    校验密码格式, 至少8位，数字、大小写字母、特殊字符组成
    :param password:
    :return:
    """
    password_decrypt = aes_decrypt(key=AESConfig.KEY, iv=AESConfig.IV, plaintext=password)

    a, b, c, d = False, False, False, False
    e = True
    for x in password_decrypt:
        if x in string.digits:                  # 数字
            a = True
        elif x in string.ascii_lowercase:       # 小写字母
            b = True
        elif x in string.ascii_uppercase:       # 大写字母
            c = True
        elif x in string.punctuation:           # 特殊字符
            d = True
        else:
            e = False

    if a and b and c and d and e and len(password_decrypt) >= 8:
        return True
    else:
        raise HTTPException(status_code=ResponseStatusCode.PASSWORD_ERR.code,
                            detail=ResponseStatusCode.PASSWORD_ERR.message)


@login_app.post("/login",
                response_model=SystemLoginOut,
                description="采用JWT认证，在Header添加Authorization字段传输token。")
async def login(request: Request,
                verify_code: Union[str, None] = Body(default=None, example='ot3R'),
                verify_code_token: Union[str, None] = Body(default=None, example='HsQK3Jsc6BmKg+TZYkjEjQ=='),
                form_data: OAuth2PasswordRequestForm = Depends()):
    request.state.audit_log = AuditLog(**{
        'action_type': '登录',
        'request_body': json.dumps({"username": form_data.username, 'password': form_data.password})
    })

    if verify_code and verify_code_token:                                       # 校验验证码
        deal_verify_code(verify_code, verify_code_token)

    user_info = authenticate_user(form_data.username, form_data.password)       # 校验账号密码
    data = {
        "user_id": user_info['user_id'],
        "username": user_info['username'],
        "password": user_info['password'],
        "scopes": form_data.scopes
    }
    access_token = create_access_token(token_info=TokenInfo(**data),            # 生成token
                                       expires_delta=timedelta(minutes=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES))

    result = {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_info['user_id'],
        "username": user_info['username']
    }
    return response_data(data=SystemLoginOut(**result).dict())


@login_app.get('/logout',
               dependencies=[Security(verify_token, scopes=[])],
               description="登出")
async def logout(request: Request):
    request.state.audit_log = AuditLog(**{
        'action_type': '登出',
        'request_body': None
    })
    return response_data(data=True)


@login_app.post("/update_password",
                dependencies=[Security(verify_token, scopes=["Write"])],
                description="密码至少8位，由数字、大小写字母、特殊字符组成")
async def update_password(request: Request, data: UpdatePasswordIn):
    request.state.audit_log = AuditLog(**{
        'action_type': '更新密码',
        'request_body': json.dumps(data.__dict__)
    })

    if data.verify_code and data.verify_code_token:
        deal_verify_code(data.verify_code, data.verify_code_token)                          # 校验验证码

    verify_password(password=data.new_password)                                             # 校验新密码
    user_info = authenticate_user(username=data.username, password=data.old_password)       # 校验旧密码
    users_info[data.username]['password'] = data.new_password
    return response_data(data=True)
