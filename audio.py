# audio.py -- Sound effects and music, safe on machines with no audio
import os

import pygame

import config

SOUND_FILES = {
    "eat": "eat.wav",
    "hit": "hit.wav",
    "clear": "clear.wav",
    "gameover": "gameover.wav",
    "menu": "menu.wav",
}
MUSIC_NAMES = ("music.ogg", "music.wav", "music.mp3")


class Audio:
    def __init__(self):
        self.ready = False
        self.muted = False
        self.sounds = {}
        self.music_path = None
        self._init_mixer()
        if self.ready:
            self._load_sounds()
            self._find_music()

    def _init_mixer(self):
        try:
            pygame.mixer.pre_init(config.AUDIO_FREQ, -16, 1,
                                  config.AUDIO_BUFFER)
            pygame.mixer.init()
            self.ready = True
        except pygame.error:
            self.ready = False   # no sound card / driver: play silently

    def _load_sounds(self):
        for key, filename in SOUND_FILES.items():
            path = os.path.join(config.SOUND_DIR, filename)
            if not os.path.isfile(path):
                continue
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(config.SFX_VOLUME)
                self.sounds[key] = sound
            except pygame.error:
                continue

    def _find_music(self):
        for name in MUSIC_NAMES:
            path = os.path.join(config.SOUND_DIR, name)
            if os.path.isfile(path):
                self.music_path = path
                return

    # ---------- playback ----------
    def play(self, key):
        """Play one effect. Engine event names map straight to keys."""
        if not self.ready or self.muted:
            return
        sound = self.sounds.get(key)
        if sound:
            sound.play()

    def start_music(self):
        if not self.ready or not self.music_path or self.muted:
            return
        try:
            pygame.mixer.music.load(self.music_path)
            pygame.mixer.music.set_volume(config.MUSIC_VOLUME)
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    def stop_music(self):
        if self.ready:
            pygame.mixer.music.stop()

    def toggle_mute(self):
        self.muted = not self.muted
        if not self.ready:
            return self.muted
        if self.muted:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()
        return self.muted