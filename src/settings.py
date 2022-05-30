import os
from os.path import join, dirname
from dotenv import load_dotenv
from pydantic import BaseSettings

# load_dotenv(verbose=True)
#
dotenv_path = join(dirname(__file__), '../.env')
load_dotenv(dotenv_path)


class Settings(BaseSettings):
    # Twitter API
    API_KEY: str
    API_SECRET: str
    ACCESS_TOKEN: str
    ACCESS_TOKEN_SECRET: str

    BEARER_TOKEN: str

    DATA_DIR: str = join(dirname(__file__), '../data')

    # Logger
    LOGGER_LEVEL: str
    LOG_SAVE_DIR: str = join(dirname(__file__), '../data/logs')

    # class Config:
    #     case_sensitive = True
    #     _base_dir = os.path.dirname(os.path.abspath(__file__))
    #     env_file = f'{_base_dir}/../.env'


settings = Settings()
