# scores.py -- Persistent high scores (JSON)
import json
import os

import config
import paths

RUN_KEY = "(Full Run)"

def _score_path():
    """should be a function that calls paths.user_file"""
    return paths.user_file("scores.json")

def load_scores():
    path = _score_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}