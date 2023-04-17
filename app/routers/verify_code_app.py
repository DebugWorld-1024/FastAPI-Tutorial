
import base64
import random
import string
from io import BytesIO
from captcha.image import ImageCaptcha
from fastapi import APIRouter, HTTPException

from library.constants import AESConfig
from library.util import aes_decrypt, aes_encrypt
from app.response_status_code import ResponseStatusCode
from app.data_model import VerifyCodeOut, response_data


verify_code_app = APIRouter()


def deal_verify_code(verify_code: str, verify_code_token: str):
    """
    校验验证码
    :param verify_code:
    :param verify_code_token:
    :return:
    """
    if aes_decrypt(key=AESConfig.KEY, iv=AESConfig.IV, plaintext=verify_code_token).lower() == verify_code.lower():
        return True
    else:
        raise HTTPException(status_code=ResponseStatusCode.VERIFY_CODE_ERR.code,
                            detail=ResponseStatusCode.VERIFY_CODE_ERR.message)


@verify_code_app.get("/verify_code", response_model=VerifyCodeOut, description="生成四位验证码，包含数字+大写字母+小写字母")
async def get_verify_code():
    characters = string.digits + string.ascii_uppercase + string.ascii_lowercase
    captcha_str = ''.join(random.sample(characters, 4))
    img = ImageCaptcha(160, 60).generate_image(captcha_str)

    fmt = 'png'
    output_buffer = BytesIO()
    img.save(output_buffer, format=fmt)
    byte_data = output_buffer.getvalue()
    base64_str = base64.b64encode(byte_data).decode('utf-8')

    data = {
        'verify_image': f'data:image/{fmt};base64,{base64_str}',
        'verify_code_token': aes_encrypt(key=AESConfig.KEY, iv=AESConfig.IV, plaintext=captcha_str)
    }
    return response_data(data=VerifyCodeOut(**data).dict())
