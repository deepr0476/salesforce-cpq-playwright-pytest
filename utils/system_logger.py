from __future__ import annotations

import logging
import sys
from pathlib import Path


class EliteFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(
            fmt="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] -> %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def configure_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    formatter = EliteFormatter()
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    
    root.addHandler(stream)
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
