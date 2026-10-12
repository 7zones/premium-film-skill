#!/usr/bin/env python3
"""Measures a music track before you cut to it: music_scan.py <track> [--bpm 120] [--bars]
Prints the tempo, a straight beat grid fitted to the detected beats (t0, beat length, residual), the most likely
downbeat phase and the bar times, the key, and the track's shape every 4 s as sparklines (loudness, drums, sub,
brightness, onsets). --bars adds a per-bar table (loudness, percussion, harmony, sub, highs) with phrase marks.

Why measure: an LLM asked to describe a track invents structure (it "heard" stop-time hits that don't exist), though
its mood calls (dark vs heroic) were consistent. Cut only on measured downbeats; place the picture's big moments on
bar lines. Runs in the film-audio image."""
import sys

import librosa
import numpy as np

args = sys.argv[1:]
f = args[0]
bpm0 = float(args[args.index("--bpm") + 1]) if "--bpm" in args else 120.0
y, sr = librosa.load(f, sr=22050, mono=True)
dur = len(y) / sr
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, start_bpm=bpm0, tightness=200, units="time")
tempo = float(np.atleast_1d(tempo)[0])
d = np.diff(beats)
k = np.round((beats - beats[0]) / np.median(d))
t0, ibi = np.linalg.lstsq(np.vstack([np.ones_like(k), k]).T, beats, rcond=None)[0]
res = beats - (t0 + k * ibi)
print(f"{f}: {dur:.1f} s, tempo {tempo:.1f} bpm; grid t0 {t0:.4f} s, beat {ibi:.5f} s ({60 / ibi:.3f} bpm), residual p95 {np.percentile(np.abs(res), 95) * 1000:.0f} ms")
oenv = librosa.onset.onset_strength(y=y, sr=sr)
times = librosa.times_like(oenv, sr=sr)
scores = [np.interp(t0 + np.arange(ph, int((dur - t0) / ibi), 4) * ibi, times, oenv).mean() for ph in range(4)]
ph = int(np.argmax(scores))
bar0, bar = t0 + ph * ibi, 4 * ibi
print(f"downbeat phase {ph} (onset means {', '.join(f'{s:.2f}' for s in scores)}): first bar at {bar0:.3f} s, bar = {bar:.4f} s")
print("bars:", ", ".join(f"{i}:{bar0 + i * bar:.2f}" for i in range(int((dur - bar0) / bar) + 1)))
# key (Krumhansl profiles on the harmonic part)
H, P = librosa.effects.hpss(y)
chroma = librosa.feature.chroma_cqt(y=H, sr=sr).mean(1)
keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
maj = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
mnr = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
sc = [(np.corrcoef(np.roll(maj, i), chroma)[0, 1], keys[i] + " major") for i in range(12)] + [(np.corrcoef(np.roll(mnr, i), chroma)[0, 1], keys[i] + " minor") for i in range(12)]
print("key ~", max(sc)[1])
B = " ▁▂▃▄▅▆▇█"
hop, sec = 512, 4
fr = sr / hop
n = int(dur / sec)
per = lambda x: [float(np.mean(x[int(i * sec * fr):int((i + 1) * sec * fr)])) for i in range(n)]
spark = lambda v, lo=None, hi=None: "".join(B[int(np.clip((x - (min(v) if lo is None else lo)) / ((max(v) if hi is None else hi) - (min(v) if lo is None else lo) + 1e-9), 0, 1) * 8)] for x in v)
S = np.abs(librosa.stft(y, hop_length=hop))
freqs = librosa.fft_frequencies(sr=sr)
rows = {
    "loud": per(20 * np.log10(librosa.feature.rms(y=y, hop_length=hop)[0] + 1e-6)),
    "drums": per(20 * np.log10(librosa.feature.rms(y=P, hop_length=hop)[0] + 1e-6)),
    "sub": per(20 * np.log10(S[freqs < 120].mean(0) + 1e-6)),
    "bright": per(librosa.feature.spectral_centroid(S=S, sr=sr)[0]),
    "onsets": per(librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)),
}
print("  time  |" + "".join(f"{(i * sec) // 60}" if (i * sec) % 60 == 0 else ("·" if (i * sec) % 20 == 0 else " ") for i in range(n)) + "|  (one char = 4 s)")
for name, v in rows.items():
    print(f"  {name:6s}|{spark(v, -40 if name in ('loud', 'drums') else None)}|")
if "--bars" in args:
    def db(x):
        return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-7)
    print(" bar   start   loud  perc  harm  sub<100  hi>4k")
    for i in range(int((dur - bar0) / bar)):
        a = bar0 + i * bar
        s = slice(int(a * sr), int((a + bar) * sr))
        fa, fb = int(a * sr / hop), int((a + bar) * sr / hop)
        sub = 20 * np.log10(S[freqs < 100, fa:fb].mean() + 1e-7)
        hi = 20 * np.log10(S[freqs > 4000, fa:fb].mean() + 1e-7)
        print(f"{i:4d} {a:7.2f} {db(y[s]):6.1f} {db(P[s]):5.1f} {db(H[s]):5.1f} {sub:7.1f} {hi:6.1f}{'  <phrase' if i % 8 == 0 else ''}")
