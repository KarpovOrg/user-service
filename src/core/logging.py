import sys

from pathlib import Path

from loguru import logger


SRC_DIR = Path(__file__).parent.parent
LOG_DIR = SRC_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    enqueue=True,
)

logger.add(
    LOG_DIR / "app.log", rotation="500 MB", retention="10 days", compression="zip"
)