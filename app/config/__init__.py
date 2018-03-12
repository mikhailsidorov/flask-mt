import os

if os.environ.get('ENV_TYPE') == 'DEV':
    from config.dev import Config
else:
    from config.base import BaseConfig as Config
