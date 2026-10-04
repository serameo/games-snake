# assets.py -- Image loading with safe fallbacks
import os

import pygame

import config

IMAGE_FILES = {
    "head": "head.png",
    "body": "body.png",
    "tail": "tail.png",
    "fruit": "fruit.png",
    "wall": "wall.png",
}


def load_images(cell_size):
    """Return {key: Surface}. Missing or broken files are skipped."""
    images = {}
    for key, filename in IMAGE_FILES.items():
        path = os.path.join(config.IMAGE_DIR, filename)
        if not os.path.isfile(path):
            continue
        try:
            surface = pygame.image.load(path).convert_alpha()
            images[key] = pygame.transform.smoothscale(
                surface, (cell_size, cell_size))
        except pygame.error:
            continue
    return images