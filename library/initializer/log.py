
import os
import logging
from library.config.config import load_config
from logging.handlers import RotatingFileHandler


class Log(object):
    """
    Usage:
        >>> from library.initializer.log import Log
        >>> logger = Log().get_logger(log_name='test')
        >>> logger.warning('This is warning')
        >>> logger.info('This is info')
    """
    def __init__(self, log_config: dict = load_config("app.log_config")):
        # 屏幕输出
        base_config = {
            'format': log_config['format'],
            'level': log_config['level'],
            'datefmt': log_config['datefmt']
        }
        logging.basicConfig(**base_config)

        # # Mac、Linux、Windows都兼容
        # log_dir = os.path.join(os.path.split(os.path.realpath(__file__))[0], '../../', 'logs')
        # if not os.path.exists(log_dir):
        #     os.makedirs(log_dir)
        #
        # # 文件输出
        # file_config = {
        #     'filename': os.path.join(log_dir, log_config['filename']),
        #     'maxBytes': log_config['maxBytes'],
        #     'backupCount': log_config['backupCount'],
        #     'encoding': log_config['encoding']
        # }
        #
        # self.logger_handler = RotatingFileHandler(**file_config)
        # self.logger_handler.setFormatter(fmt=logging.Formatter(log_config['format']))

    @classmethod
    def get_logger(cls, name=None):
        """
        Log() 实例化
        :param name: 如果name相同，则id(logger)相同。
        :return:
        """
        logger = logging.getLogger(name=name)
        # logger.addHandler(self.logger_handler)
        return logger
