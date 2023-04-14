
import os
import yaml


# 使用yaml的模式
def load_config(config_name: str, file_path: str = os.getenv('CONFIG_PATH', None)):
    """
    读取yaml里的配置信息
    :param config_name: db.redis_config
    :param file_path:
    :return:
    """
    file_path = file_path or os.path.join(os.path.split(os.path.realpath(__file__))[0], 'config.yaml')
    with open(f'{file_path}', 'r') as f:
        config_data = yaml.load(f.read(), Loader=yaml.FullLoader)

    for item in config_name.split('.'):
        if item:
            config_data = config_data[item]

    return config_data
