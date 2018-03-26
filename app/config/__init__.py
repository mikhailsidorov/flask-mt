import os

ENV_TYPE = os.environ.get('ENV_TYPE')

if os.environ.get('ENV_TYPE') == 'DEV':
    from config.dev import Config
elif ENV_TYPE == 'TESTING':
    from config.testing import Config
else:
    from config.base import BaseConfig as Config
