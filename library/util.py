
import re
import time
import hmac
import socket
import base64
import random
import string
import decimal
import hashlib
import requests
import tempfile
import pandas as pd
from typing import Union
from datetime import datetime
from io import BytesIO, StringIO
from library.constants import TimeFMT

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from dateutil.relativedelta import relativedelta


def str_exchange_datetime(time_data: Union[str, datetime],
                          fmt: str = TimeFMT.FTM_SECOND,
                          exchange_type: int = 1) -> Union[str, datetime]:
    """
    字符串和日期时间相互转换
    :param time_data: 字符串/日期时间
    :param fmt: 日期时间格式
    :param exchange_type: 1: 字符串 to 日期时间、0: 日期时间 to 字符串
    :return:
    """
    return datetime.strptime(time_data, fmt) if exchange_type else time_data.strftime(fmt)


def str_exchange_timestamp(time_data: Union[str, int],
                           fmt: str = TimeFMT.FTM_SECOND,
                           exchange_type: int = 1) -> Union[str, int]:
    """
    字符串和时间戳互换，单位毫秒
    :param time_data: 字符串/时间戳
    :param fmt: 日期时间格式
    :param exchange_type: 1: 字符串 to 时间戳、0: 时间戳 to 字符串
    :return:
    """
    return int(time.mktime(time.strptime(time_data, fmt)) * 1000) if exchange_type \
        else datetime.fromtimestamp(time_data / 1000).strftime(fmt)


def timestamp_exchange_datetime(time_data: Union[int, datetime], exchange_type: int = 1) -> Union[int, datetime]:
    """
    时间戳和日期时间互换，单位是毫秒
    :param time_data: 时间戳/日期时间
    :param exchange_type: 1: 时间戳 to 日期、0: 日期 to 时间戳
    :return:
    """
    return datetime.fromtimestamp(time_data / 1000) if exchange_type else int(time_data.timestamp() * 1000)


def get_specify_time(time_data: str = None, fmt: str = TimeFMT.FTM_SECOND, **time_type) -> str:
    """
    字符串时间之间加减
    :param time_data: 时间格式
    :param fmt: 时间格式
    :param time_type: 时间加减 {"seconds": 1}: 日期加一秒, seconds、minutes、hours、days、weeks、months、years
    :return: 特定格式的时间字符串
    """
    time_data = str_exchange_datetime(time_data, fmt=fmt, exchange_type=1) if time_data else datetime.now()
    return (time_data + relativedelta(**time_type)).strftime(fmt)


def get_specify_datetime(time_data: datetime = None, **time_type) -> datetime:
    """
    日期时间之间加减时间
    :param time_data: 时间戳，单位毫秒
    :param time_type: {'seconds': 1}
    :return: 时间戳，单位毫秒
    """
    time_data = time_data or datetime.now()
    return time_data + relativedelta(**time_type)


def get_specify_timestamp(timestamp: int, **time_type) -> int:
    """
    时间戳之间加减时间
    :param timestamp: 时间戳，单位毫秒
    :param time_type: {'seconds': 1}
    :return: 时间戳，单位毫秒
    """
    time_data = timestamp_exchange_datetime(timestamp) + relativedelta(**time_type)
    return timestamp_exchange_datetime(time_data, exchange_type=0)


def random_datetime(start_datetime: datetime, end_datetime: datetime) -> datetime:
    """
    两个日期之间的随机一天[start_datetime, end_datetime)
    :param start_datetime: 开始时间
    :param end_datetime: 结束时间
    :return: datetime
    """
    start_stamp = timestamp_exchange_datetime(time_data=start_datetime, exchange_type=0)
    end_stamp = timestamp_exchange_datetime(time_data=end_datetime, exchange_type=0) - 1000
    random_timestamp = random.randint(start_stamp, end_stamp)
    return timestamp_exchange_datetime(time_data=random_timestamp)


def random_time(start_time: str, end_time: str, fmt: str = TimeFMT.FTM_SECOND) -> str:
    """
    两个日期之间的随机一天[start_datetime, datetime)
    :param start_time: 开始时间, datetime
    :param end_time: 结束时间, datetime
    :param fmt: 时间格式
    :return: datetime
    """
    start_timestamp = str_exchange_timestamp(time_data=start_time, fmt=fmt)
    end_timestamp = str_exchange_timestamp(time_data=end_time, fmt=fmt) - 1000
    random_timestamp = random.randint(start_timestamp, end_timestamp)
    return str_exchange_timestamp(time_data=random_timestamp, fmt=fmt, exchange_type=0)


def split_time(start_time: str, end_time: str, fmt: str = TimeFMT.FTM_SECOND, **time_type) -> list:
    """
    按照一定间隔切割字符串时间
    :param start_time: 起始时间
    :param end_time: 结束时间
    :param fmt: 时间格式
    :param time_type: 间隔类型
    :return:
    """
    flag = True
    data_list = list()
    from_time = start_time
    while flag:
        if (to_time := get_specify_time(time_data=from_time, fmt=fmt, **time_type)) >= end_time:
            to_time = end_time
            flag = False

        data_list.append([from_time, to_time])
        from_time = to_time

    return data_list


def md5hex(data: str) -> str:
    """
    MD5加密算法，返回32位小写16进制符号
    :param data: 需要加密的数据
    :return:
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    elif not isinstance(data, str):
        data = str(data).encode("utf-8")
    m = hashlib.md5()
    m.update(data)
    return m.hexdigest()


def hmac_sha256(secret: str, s: str) -> str:
    """
    散列消息认证码
    :param secret: 密钥
    :param s: 字符串
    :return:
    """
    return hmac.new(secret.encode('utf-8'), s.encode('utf-8'), hashlib.sha256).hexdigest()


def format_headers(headers_str: str) -> dict:
    """
    str to dict
    :param headers_str: headers的字符串形式
    :return: headers的dict形式
    """
    headers = dict()
    headers_list = headers_str.split('\n')
    for header in headers_list:
        header = header.strip()
        if header == '':
            continue
        header_list = header.split(': ')
        if len(header_list) == 1:
            headers[header_list[0].replace(':', '')] = ''
        elif len(header_list) == 2:
            headers[header_list[0]] = header_list[1]
        else:
            raise Exception('headers 解析出错')
    return headers


def cut(data_list: list, num: int) -> list:
    """
    把一个list按照指定长度切割
    :param data_list:
    :param num:
    :return:
    """
    return [data_list[i:i+num] for i in range(0, len(data_list), num)]


def random_string(n: int) -> str:
    """
    获取指定长度的随机字符串(字母和数字)
    :param n: 长度
    :return:
    """
    return "".join(random.choice(string.printable[0:62]) for _ in range(n))


def string_to_file(s: str):
    """
    字符串数据转成文件对象
    :param s:
    :return:
    """
    file_obj = tempfile.NamedTemporaryFile()
    file_obj.write(s.encode())
    file_obj.flush()                    # 确保string立即写入文件
    file_obj.seek(0)                    # 将文件读取指针返回到文件开头位置
    return file_obj


def df_to_buffer(df: pd.DataFrame, text_type: str):
    """
    # TODO 统一返回数据格式
    df数据 转 IO数据
    :param df:
    :param text_type: 目前仅支持csv、xlsx格式
    :return:
    """
    assert text_type in ['csv', 'xlsx'], '参数 text_type 不正确'
    buffer = None
    if text_type == 'csv':
        buffer = StringIO()
        buffer.write(df.to_csv(index=False))
    if text_type == 'xlsx':
        buffer = BytesIO()
        df.to_excel(buffer, engine='xlsxwriter', index=False)      # xlsxwriter 比 openpyxl快，但是xlsxwriter以后不维护了
    return buffer


def get_local_ip() -> Union[dict, None]:
    """
    获取内网和外网的ip信息
    ps: 获取外网信息需要联网
    :return:
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        return {
            "LAN": s.getsockname()[0],                                                  # 内网ip信息
            "WAN": requests.get('https://ifconfig.me/ip', timeout=5).text.strip()       # 外网ip信息
        }
    except Exception as e:
        from library.initializer.log import Log
        Log().get_logger().error(str(e))
        return None


def float_to_str(f: float, prec: int = 38) -> str:
    """
    Convert the given float to a string,
    without resorting to scientific notation
    :param f:
    :param prec:
    :return:
    """
    context = decimal.getcontext()
    context.prec = prec
    return format(context.create_decimal(repr(f)), 'f')


def str_split_int(s: str) -> list:
    """
    把字符串里的整数和字符拆开
    :param s:
    :return:
    """
    return re.findall('\\d+|[A-Za-z]+', s)


def slack_message(project_name: str, message: str, url: str = None) -> bool:
    """
    向slack发送信息
    :param project_name: 业务名字
    :param message: 信息内容
    :param url: slack url
    :return: bool
    """
    try:
        url = url or ""
        text = f'通知 *_* 通知:\n【业务名字】: {project_name}\n【信息内容】: {message}'
        requests.post(url=url, json={'text': text})
        return True
    except Exception as e:
        from library.initializer.log import Log
        Log().get_logger().error(str(e))
        return False


def aes_encrypt(key: str, iv: str, plaintext: str, block_size: int = 16, style: str = 'pkcs7') -> str:
    """
    AES.CBC加密
    :param key:
    :param iv:
    :param plaintext:
    :param block_size:
    :param style:
    :return:
    """
    aes = AES.new(key=key.encode(), mode=AES.MODE_CBC, iv=iv.encode())
    encrypt_bytes = aes.encrypt(pad(data_to_pad=plaintext.encode(), block_size=block_size, style=style))
    return str(base64.b64encode(encrypt_bytes), encoding='utf-8')


def aes_decrypt(key: str, iv: str, plaintext: str, block_size: int = 16, style: str = 'pkcs7') -> str:
    """
    AES.CBC解密
    :param key:
    :param iv:
    :param plaintext:
    :param block_size:
    :param style:
    :return:
    """
    aes = AES.new(key=key.encode(), mode=AES.MODE_CBC, iv=iv.encode())
    return unpad(padded_data=aes.decrypt(base64.b64decode(plaintext)), block_size=block_size, style=style).decode()
