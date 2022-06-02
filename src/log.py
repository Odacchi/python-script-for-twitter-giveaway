import logging
from logging.handlers import RotatingFileHandler

from settings import settings

logger = logging.getLogger(__name__)

logger.setLevel(settings.LOGGER_LEVEL)
sh = logging.StreamHandler()
sh.setLevel(settings.LOGGER_LEVEL)

# フォーマッタを定義する（第一引数はメッセージのフォーマット文字列、第二引数は日付時刻のフォーマット文字列）
fmt = logging.Formatter(
    "[%(asctime)s][%(levelname)s](%(name)s:%(filename)s:%(lineno)s) %(message)s",
    "%Y-%m-%dT%H:%M:%S"
)

# フォーマッタをハンドラに紐づける
sh.setFormatter(fmt)
logger.addHandler(sh)

_ERROR_LOG_FILE = f'{settings.LOG_SAVE_DIR}/error.log'

# ローテーションのタイミングを1MByte
max_bytes = 1 * 1024 * 1024
# 保持する旧ファイル数
backup_count = 4
err_h = RotatingFileHandler(
    _ERROR_LOG_FILE,  # logフォルダが存在しないとエラーになるので注意
    maxBytes=max_bytes,
    backupCount=backup_count,
    encoding='utf-8')
err_h.setLevel(logging.WARN)
err_h.setFormatter(fmt)

logger.addHandler(err_h)
