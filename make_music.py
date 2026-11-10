"""Generates an original, royalty-free ambient loop (music.wav) for the loading screen.

Chord progression Am - F - C - G, soft pad + bass + arpeggio + simple echo.
Run:  python make_music.py
"""
import math, random, struct, wave

RATE = 22050
BPM = 84
BEAT = 60.0 / BPM
BARS = 16                      # 4 chords x 4 repeats
BAR_LEN = BEAT * 4
LENGTH = BARS * BAR_LEN        # ~45.7 seconds, loops seamlessly

def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12.0)

# chord roots (MIDI) and triads
CHORDS = [
    (57, [57, 60, 64]),  # Am
    (53, [53, 57, 60]),  # F
    (48, [48, 52, 55]),  # C
    (55, [55, 59, 62]),  # G
]

n = int(LENGTH * RATE)
buf = [0.0] * n

def add_note(freq, start, dur, amp, kind="sine", attack=0.02, release=0.3):
    s0 = int(start * RATE)
    s1 = min(n, int((start + dur + release) * RATE))
    w = 2 * math.pi * freq / RATE
    for i in range(s0, s1):
        t = (i - s0) / RATE
        if t < attack:
            env = t / attack
        elif t < dur:
            env = 1.0
        else:
            env = max(0.0, 1.0 - (t - dur) / release)
        ph = w * (i - s0)
        if kind == "pad":
            v = math.sin(ph) * 0.6 + math.sin(ph * 1.003) * 0.3 + math.sin(ph * 2.0) * 0.1
        elif kind == "pluck":
            v = math.sin(ph) * math.exp(-t * 3.0)
        else:
            v = math.sin(ph)
        buf[i % n] += v * env * amp

random.seed(7)
for bar in range(BARS):
    root, triad = CHORDS[bar % 4]
    t0 = bar * BAR_LEN
    # warm pad: full bar, slow attack
    for note in triad:
        add_note(midi(note), t0, BAR_LEN, 0.07, "pad", attack=0.8, release=0.8)
    # bass on beats 1 and 3
    add_note(midi(root - 12), t0, BEAT * 1.8, 0.16, "sine", attack=0.03, release=0.4)
    add_note(midi(root - 12), t0 + BEAT * 2, BEAT * 1.8, 0.13, "sine", attack=0.03, release=0.4)
    # arpeggio in eighth notes (skip the first 4 bars so it builds)
    if bar >= 4:
        pattern = [0, 1, 2, 1, 0, 2, 1, 2]
        for k in range(8):
            note = triad[pattern[k]] + 12 + (12 if (bar >= 8 and k % 4 == 3) else 0)
            add_note(midi(note), t0 + k * BEAT / 2, BEAT / 2, 0.09, "pluck", attack=0.005, release=0.25)

# simple echo (wraps around so the loop stays seamless)
delay = int(BEAT * 0.75 * RATE)
out = buf[:]
for i in range(n):
    out[i] += buf[(i - delay) % n] * 0.28 + buf[(i - 2 * delay) % n] * 0.12

peak = max(abs(v) for v in out) or 1.0
with wave.open("music.wav", "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(RATE)
    wf.writeframes(b"".join(struct.pack("<h", int(v / peak * 0.85 * 32767)) for v in out))
print("wrote music.wav", round(LENGTH, 1), "seconds")
