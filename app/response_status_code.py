from enum import Enum
from typing import Tuple


class ResponseStatusCode(Tuple[int, str], Enum):
    OK = (200, "成功")
    ERROR = (5000, "未知错误")

    IMAGE_CODE_ERR = (5001, "图形验证码错误")
    USER_PASSWORD_ERR = (5002, '账号或密码错误')
    UNAUTHORIZED_ERR = (5003, "用户未登录")
    TOKEN_ERR = (5004, "登录Token有误")
    SCOPES_CODE_ERR = (5005, "权限有误")
    PASSWORD_ERR = (5006, "密码不符合规范")

    REQUEST_VALIDATION_ERR = (6000, "Request参数有误")
    RESPONSE_VALIDATION_ERR = (7000, "Response参数有误")

    @property
    def code(self):
        """
        获取状态码
        :return:
        """
        return self.value[0]

    @property
    def message(self):
        """
        获取状态码信息
        :return:
        """
        return self.value[1]
