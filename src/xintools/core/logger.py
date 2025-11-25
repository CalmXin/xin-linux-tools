from datetime import datetime

from loguru import logger as _logger

from xintools.core.constants import BASE_DIR


def _setup_logger():
    log_file_path = BASE_DIR / f"data/logs/app_{datetime.now().strftime('%Y_%m_%d')}.log"
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    _logger.add(
        str(log_file_path),
        rotation="10 MB",  # 每个文件最大10MB
        retention="30 days",
        compression="zip"  # 压缩旧日志为 zip
    )
    return _logger


logger = _setup_logger()
