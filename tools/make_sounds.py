# tools/make_sounds.py -- Generate simple WAV effects (stdlib only)
import math
import os
import struct
import wave

RATE = 22050
OUT_DIR = os.path.join("assets", "sounds")


def tone(freq, duration, volume=0.5, shape="sine", slide_to=None):
    """Build one note as a list of float samples in the range -1..1."""
    frames = int(RATE * duration)
    attack = max(1, int(RATE * 0.008))
    release = max(1, int(RATE * 0.05))
    samples = []
    phase = 0.0

    for i in range(frames):
        ratio = i / frames
        current = freq if slide_to is None else freq + (slide_to - freq) * ratio
        phase += 2 * math.pi * current / RATE

        if shape == "square":
            value = 1.0 if math.sin(phase) >= 0 else -1.0
        elif shape == "triangle":
            value = 2 / math.pi * math.asin(math.sin(phase))
        else:
            value = math.sin(phase)

        envelope = min(1.0, i / attack) * min(1.0, (frames - i) / release)
        samples.append(value * envelope * volume)
    return samples


def silence(duration):
    return [0.0] * int(RATE * duration)


def write_wav(name, samples):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with wave.open(path, "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        data = b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767))
            for s in samples
        )
        handle.writeframes(data)
    print("wrote", path)


def build_all():
    # eat: two quick rising blips
    write_wav("eat.wav", tone(880, 0.055) + tone(1320, 0.07))

    # hit: falling square buzz
    write_wav("hit.wav", tone(320, 0.28, 0.55, "square", slide_to=110))

    # clear: happy arpeggio
    clear = []
    for note in (523, 659, 784, 1047):
        clear += tone(note, 0.11, 0.5, "triangle")
    write_wav("clear.wav", clear)

    # gameover: slow descending phrase
    over = []
    for note in (440, 349, 294, 220):
        over += tone(note, 0.20, 0.5, "square") + silence(0.03)
    write_wav("gameover.wav", over)

    # menu: tiny click
    write_wav("menu.wav", tone(660, 0.04, 0.35, "triangle"))

    # music: gentle 8 note loop, kept quiet on purpose
    melody = [392, 440, 494, 440, 392, 330, 294, 330]
    track = []
    for note in melody:
        track += tone(note, 0.26, 0.22, "triangle") + silence(0.06)
    write_wav("music.wav", track)


if __name__ == "__main__":
    build_all()
