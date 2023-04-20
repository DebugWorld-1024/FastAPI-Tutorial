
class Position:
    """redis 查询方向"""
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'


class Method:
    GET = 'GET'
    POST = 'POST'


class TimeFMT:
    """时间格式"""
    TFM_DATE = '%Y-%m-%d'
    TFM_HOUR = '%Y-%m-%d %H'
    TFM_MINUTE = '%Y-%m-%d %H:%M'
    FTM_SECOND = '%Y-%m-%d %H:%M:%S'


class DataBase:
    """数据库"""
    pass


class TableName:
    """数据表"""
    pass


class MailReceiver:
    """邮箱收件人"""
    MailReceiver1 = 'xxx@Foxmail.com'
    MailReceiver2 = 'xxx@Foxmail.com'

    RECEIVERS = [MailReceiver1, MailReceiver2]


class AESConfig:
    """ AES 密钥 """
    KEY = 'Ziltuj2C2JYz2nADUiecTRJibOHlQHuc'
    IV = 'dKIBF3rrjBfYrcZ9'


class JWTConfig:
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1 * 24 * 60
    SECRET_KEY = "bjqWLWEmaWBznBJYHM6QP3z5WOXiHVuvp2DavZqdGBOD2rtmLzyHb7LjPrXIk9r6"


class TimeZone:
    """时区"""
    pass
