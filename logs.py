import logging
import sys
from pathlib import Path

def setup_logging():
    # Check if logging is already configured
    if logging.getLogger().hasHandlers():
        return
        
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler for ERROR and above only
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)  # Only show errors in console
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs (INFO and above)
    file_handler = logging.FileHandler(log_dir / "bot.log", encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler for ERROR and above (separate file)
    error_handler = logging.FileHandler(log_dir / "errors.log", encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Set disnake logger to only show errors
    logging.getLogger('disnake').setLevel(logging.ERROR)
