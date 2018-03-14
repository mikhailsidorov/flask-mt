import os
from config.base import BaseConfig


class Config(BaseConfig):
    DEBUG = os.environ.get("FLASK_DEBUG") or 0
    TASK_DEBUG = os.environ.get('TASK_DEBUG') or False