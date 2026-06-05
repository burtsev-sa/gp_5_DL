import json
import logging
from pathlib import Path


def logger():
    folder = Path(__file__).parent
    cfg = json.loads((folder / 'config.json').read_text(encoding="utf-8"))

    if not cfg.get('logging_enabled', True):
        return logging.getLogger('logs')

    log_file = folder / cfg.get('log_file')

    logging.basicConfig(level=cfg.get('log_level', 'INFO').upper(), 
                        format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s',
                        handlers = [logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler()], force=True)
    return logging.getLogger('logs')


