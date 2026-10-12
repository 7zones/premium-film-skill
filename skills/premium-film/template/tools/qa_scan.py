#!/usr/bin/env python3
"""Scans a rendered video for the glitches people notice but a few stills miss:
  qa_scan.py <video.mp4> [--from S] [--to S] [--chunk FRAMES] [--dead 0.8] [--strips DIR]

  black / dips   frames much darker than both neighbours (one NaN pixel through bloom blacks a whole frame), or black
  jumps          one-frame spikes in frame-to-frame change: pops, instant-attack flashes, elements that appear with
                 no animation (an instant attack reads as a glitch; give hits a 3–4 frame attack)
  cuts           single huge changes (fine if intended; listed so you can confirm each one is)
  flicker        A-B-A blocks: a frame differs from both neighbours while the neighbours match. Catches text drawn a
                 pixel apart by different render tabs ("the text keeps glitching its position") — confirm on glyph
                 crops, because twinkles and blinking lights trigger it too
  dead spots     stretches where nothing moves for ≥ --dead seconds (a client flagged "1–2 seconds of dead picture";
                 something should always be gently moving: camera drift, light, particles)
  joins          with --chunk N: change across every chunk boundary vs its neighbours (a bad join jumps or freezes)
--strips DIR writes a frame strip (every frame, ±6 frames) for each flagged moment, to look at before believing it.
Needs ffmpeg + numpy (film-audio image, or a local Python with numpy)."""
import json
import os
import subprocess
import sys

import numpy as np

args = sys.argv[1:]
video = args[0]


def opt(name, default=None, cast=float):
    return cast(args[args.index(name) + 1]) if name in args else default


t_from, t_to, chunk, dead_s, strips = opt("--from", 0.0), opt("--to", None), opt("--chunk", None, int), opt("--dead", 0.8), opt("--strips", None, str)
probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate,width,height:format=duration", "-of", "json", video], capture_output=True, text=True, check=True).stdout)
num, den = probe["streams"][0]["r_frame_rate"].split("/")
fps = float(num) / float(den)
W, H = 960, 540
cmd = ["ffmpeg", "-v", "error", "-ss", str(t_from)] + (["-to", str(t_to)] if t_to else []) + ["-i", video, "-vf", f"scale={W}:{H}:flags=area,format=gray", "-f", "rawvideo", "-"]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
B = 12  # block size for the A-B-A test
luma, diff, aba = [], [], {}  # aba: frame index → flat indices of A-B-A blocks
prev2 = prev1 = None
n = 0
while True:
    raw = proc.stdout.read(W * H)
    if len(raw) < W * H:
        break
    f = np.frombuffer(raw, np.uint8).astype(np.float32)
    f = f.reshape(H, W)
    luma.append(float(f.mean()))
    diff.append(float(np.abs(f - prev1).mean()) if prev1 is not None else 0.0)
    if prev2 is not None:  # is prev1 an A-B-A outlier between prev2 and f?
        a = np.abs(prev1 - prev2).reshape(H // B, B, W // B, B).mean((1, 3))
        c = np.abs(prev1 - f).reshape(H // B, B, W // B, B).mean((1, 3))
        ac = np.abs(prev2 - f).reshape(H // B, B, W // B, B).mean((1, 3))
        hits = (a > 4) & (c > 4) & (ac < 0.3 * np.minimum(a, c))
        # a glyph or edge drawn a pixel apart flips a run of neighbouring blocks; film grain over bright mid-tones
        # flips single scattered blocks by chance, so a block counts only with a flipped neighbour
        pad = np.pad(hits, 1)
        nb = sum(np.roll(np.roll(pad, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)[1:-1, 1:-1]
        hits &= nb > 0
        if hits.any():
            aba[n - 1] = np.flatnonzero(hits)
    prev2, prev1 = prev1, f
    n += 1
proc.wait()
t0 = t_from
T = lambda i: t0 + i / fps
luma, diff = np.array(luma), np.array(diff)
print(f"{video}: {n} frames at {fps:g} fps from {t0:.2f} s")
found = []


def report(kind, i, note):
    found.append((kind, i))
    print(f"  {kind:8s} {T(i):8.3f} s  frame {int(round(T(i) * fps)):6d}  {note}")


# black frames and single-frame dips
for i in range(1, n - 1):
    if luma[i] < 2.0 and (luma[i - 1] > 6 or luma[i + 1] > 6):
        report("black", i, f"luma {luma[i]:.1f} between {luma[i - 1]:.1f} and {luma[i + 1]:.1f}")
    elif luma[i] < 0.6 * min(luma[i - 1], luma[i + 1]) and min(luma[i - 1], luma[i + 1]) > 8:
        report("dip", i, f"luma {luma[i]:.1f} between {luma[i - 1]:.1f} and {luma[i + 1]:.1f}")
# one-frame jumps and hard cuts
for i in range(2, n - 2):
    win = np.concatenate([diff[max(1, i - 15):i - 1], diff[i + 2:i + 16]])
    med = float(np.median(win)) if len(win) else 0.0
    if diff[i] > 40:
        report("cut", i, f"change {diff[i]:.1f} (a hard cut: intended?)")
    elif diff[i] > max(6.0, 8 * med) and diff[i + 1] < 0.5 * diff[i]:
        report("jump", i, f"change {diff[i]:.1f} vs typical {med:.2f} (a pop or an instant flash)")
# A-B-A flicker that REPEATS in place: render-tab flicker flips the same text back and forth again and again, while a
# thin object moving across the frame (a ring, a streak) makes one A-B-A per spot as it passes. So only blocks hit
# ≥ 3 times within 2 s count; they are grouped into time ranges.
by_block = {}
for i, blocks in aba.items():
    for b in blocks:
        by_block.setdefault(int(b), []).append(i)
rep = set()
for b, idx in by_block.items():
    idx.sort()
    for k in range(len(idx) - 2):
        if idx[k + 2] - idx[k] <= 2 * fps:
            rep.update(idx[k:k + 3])
hit = sorted(rep)
if hit:
    groups, start, last = [], hit[0], hit[0]
    for i in hit[1:]:
        if i - last > fps * 0.5:
            groups.append((start, last))
            start = i
        last = i
    groups.append((start, last))
    for a, b in groups:
        k = sum(1 for i in hit if a <= i <= b)
        report("flicker", a, f"to {T(b):.2f} s: {k} frames where the same spots flip back and forth — check titles/glyphs on a crop (blinking lights also do this)")
# dead spots
still = diff < 0.15
run = 0
for i in range(1, n + 1):
    if i < n and still[i]:
        run += 1
        continue
    if run >= dead_s * fps:
        report("dead", i - run, f"nothing moves for {run / fps:.2f} s (to {T(i):.2f} s)")
    run = 0
# chunk joins
if chunk:
    for j in range(chunk, n, chunk):
        i = int(round((j / fps - t0) * fps))
        if 2 < i < n - 3:
            nb = np.median(np.concatenate([diff[i - 3:i], diff[i + 1:i + 4]]))
            if diff[i] > 3 * max(nb, 0.3) or (nb > 0.5 and diff[i] < 0.25 * nb):
                report("join", i, f"change {diff[i]:.2f} across the chunk join vs {nb:.2f} around it")
print(f"{len(found)} findings" + ("" if found else " — clean"))
if strips and found:
    os.makedirs(strips, exist_ok=True)
    for kind, i in found[:40]:
        t = max(0.0, T(i) - 6 / fps)
        out = os.path.join(strips, f"{kind}-{T(i):08.3f}.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", video, "-vf", "trim=end_frame=13,scale=480:-1,tile=13x1", "-frames:v", "1", out], check=False)
    print("strips in", strips)
