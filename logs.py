import logging
import sys
from pathlib import Path

def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "bot.log", encoding='utf-8'),
            logging.FileHandler(log_dir / "errors.log", encoding='utf-8')
        ]
    )

    errors_log = logging.FileHandler(log_dir / "errors.log", encoding='utf-8')
    errors_log.setLevel(logging.ERROR)
    errors_log.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logging.getLogger().addHandler(errors_log)
