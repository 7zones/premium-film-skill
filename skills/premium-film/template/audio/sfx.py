"""Procedural sound design (48 kHz stereo float32, shaped (n, 2)), for moments a recorded effect does not fit.
Every generator is deterministic (seeded): the same film always gets the same sound. Recorded effects (Pixabay,
licence noted in assets/SOURCES.md) often sound richer for impacts and whooshes; mix both."""
import numpy as np
from scipy import signal

SR = 48000


def _t(d):
    return np.arange(int(d * SR)) / SR


def _rng(seed):
    return np.random.default_rng(seed)


def _st(m, width=0.0, seed=0):
    """Mono → stereo with optional decorrelated width."""
    if width <= 0:
        return np.stack([m, m], 1)
    r = _rng(seed)
    d = int(SR * (0.004 + 0.008 * r.random()))
    right = np.concatenate([np.zeros(d), m[:-d]]) if d else m
    return np.stack([m * (1 + width * 0.0), right], 1)


def lp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "low")
    return signal.lfilter(b, a, x, axis=0)


def hp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "high")
    return signal.lfilter(b, a, x, axis=0)


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band")
    return signal.lfilter(b, a, x, axis=0)


def env_ad(n, a, d, curve=3.0):
    na = max(1, int(a * SR))
    e = np.ones(n)
    e[:na] = np.linspace(0, 1, na) ** 1.5
    rest = n - na
    e[na:] = np.exp(-np.linspace(0, curve, rest)) if rest > 0 else e[na:]
    return e


def reverb_tail(x, t60=2.2, mix=0.35, seed=3):
    """Cheap convolution reverb with an exponentially decaying noise IR."""
    r = _rng(seed)
    n = int(t60 * SR)
    ir = r.standard_normal((n, 2)) * np.exp(-6.9 * np.arange(n) / n)[:, None]
    ir = lp(ir, 7000)
    ir /= np.sqrt((ir ** 2).sum(0))
    L = len(x) + n
    wet = np.stack([np.pad(signal.fftconvolve(x[:, k], ir[:, k]), (0, L))[:L] for k in range(2)], 1)
    dry = np.pad(x, ((0, n), (0, 0)))[:L]
    return dry * (1 - mix) + wet * mix


def boom(d=3.0, f0=62, f1=32, seed=1, noise=0.25):
    """Cinematic sub impact: pitch-dropping sine, a noise transient and a tail."""
    t = _t(d)
    f = f1 + (f0 - f1) * np.exp(-t * 5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * env_ad(len(t), 0.004, d, 4.5)
    r = _rng(seed)
    tr = lp(r.standard_normal(len(t)), 900) * env_ad(len(t), 0.001, 0.4, 9) * noise
    m = np.tanh((body + tr) * 1.6)
    return reverb_tail(_st(m, 0.3, seed), 2.6, 0.3, seed)


def hit(d=2.5, seed=2, bright=0.5):
    """Trailer hit: boom plus a metallic/noise crack."""
    b = boom(d, 70, 35, seed, 0.35)
    t = _t(d)
    r = _rng(seed + 9)
    crack = bp(r.standard_normal(len(t)), 1200, 6000) * env_ad(len(t), 0.001, 0.25, 7) * bright
    crack = reverb_tail(_st(crack, 0.5, seed), 2.0, 0.45, seed + 1)
    n = min(len(b), len(crack))
    return b[:n] * 0.9 + crack[:n] * 0.6


def whoosh(d=1.2, seed=3, lo=300, hi=4000, peak=0.6, pan=(-0.6, 0.6)):
    """Filtered-noise pass-by with a moving band and a stereo sweep."""
    t = _t(d)
    r = _rng(seed)
    n = r.standard_normal(len(t))
    pos = t / d
    e = np.exp(-((pos - peak) ** 2) / 0.045)
    # moving band: crude, chunked filtering
    out = np.zeros(len(t))
    chunks = 24
    for k in range(chunks):
        a, b_ = k * len(t) // chunks, (k + 1) * len(t) // chunks
        c = (a + b_) / 2 / len(t)
        f = lo + (hi - lo) * np.exp(-((c - peak) ** 2) / 0.08)
        seg = bp(n[max(0, a - 2000):b_], max(80, f * 0.35), min(18000, f * 1.6))[-(b_ - a):]
        out[a:b_] = seg
    out *= e
    p = pan[0] + (pan[1] - pan[0]) * pos
    L, R = out * np.sqrt((1 - p) / 2), out * np.sqrt((1 + p) / 2)
    return np.stack([L, R], 1) * 1.6


def riser(d=3.5, seed=4, f0=200, f1=2400):
    """Noise + pitch riser that ends abruptly (for builds into hits)."""
    t = _t(d)
    r = _rng(seed)
    f = f0 * (f1 / f0) ** (t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = (np.sin(ph) + 0.5 * np.sin(2 * ph + 0.3)) * 0.18
    nz = hp(r.standard_normal(len(t)), 800) * 0.5
    nz = np.concatenate([bp(nz[i:i + 4800], max(200, f[i] * 0.8), min(16000, f[i] * 4 + 400)) for i in range(0, len(t), 4800)])[: len(t)]
    e = (t / d) ** 2.2
    return _st((tone + nz) * e, 0.6, seed)


def reverse_swell(d=2.0, seed=5):
    x = boom(d, 90, 45, seed, 0.6)[: int(d * SR)][::-1]
    return x * np.linspace(0.2, 1, len(x))[:, None]


def ticks(d, rate, seed=6, f=3200, level=0.25):
    """Clock/data ticks at a rate (Hz)."""
    n = int(d * SR)
    out = np.zeros(n)
    r = _rng(seed)
    k = 0
    while True:
        i = int(k / rate * SR)
        if i >= n:
            break
        L = int(0.012 * SR)
        c = np.sin(2 * np.pi * (f * (0.9 + 0.2 * r.random())) * np.arange(L) / SR) * np.exp(-np.arange(L) / (0.0025 * SR))
        out[i:i + L] += c[: n - i]
        k += 1
    return _st(out * level, 0.4, seed)


def blip(f=1800, d=0.12, seed=7, level=0.4, down=False):
    t = _t(d)
    ff = f * (0.7 if down else 1.0) + (f * 0.3 if down else 0) * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(ff) / SR
    m = np.sin(ph) * env_ad(len(t), 0.002, d, 5) * level
    return reverb_tail(_st(m, 0.3, seed), 0.6, 0.2, seed)


def heartbeat(seed=8):
    """Deep lub-dub."""
    def thump(f0, d, g):
        t = _t(d)
        f = 38 + (f0 - 38) * np.exp(-t * 18)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), 0.003, d, 6) * g
    a = thump(80, 0.45, 1.0)
    b = thump(70, 0.4, 0.7)
    n = int(0.9 * SR)
    out = np.zeros(n)
    out[: len(a)] += a
    o = int(0.32 * SR)
    out[o:o + len(b)] += b[: n - o]
    return _st(np.tanh(out * 1.4), 0.0)


def glitch(d=0.6, seed=9, level=0.5):
    r = _rng(seed)
    n = int(d * SR)
    out = np.zeros(n)
    i = 0
    while i < n:
        L = int(SR * (0.008 + 0.05 * r.random()))
        kind = r.integers(0, 3)
        if kind == 0:
            seg = np.sign(np.sin(2 * np.pi * (200 + 3000 * r.random()) * np.arange(L) / SR))
        elif kind == 1:
            seg = r.standard_normal(L)
            seg = np.round(seg * 3) / 3
        else:
            seg = np.zeros(L)
        out[i:i + L] = seg[: n - i] * (0.3 + 0.7 * r.random())
        i += L
    out = bp(out, 300, 5000) * level
    return _st(out, 0.8, seed)


def shimmer(d=2.5, seed=10, base=880, level=0.25):
    """Bright gold sparkle: many short high sine grains with a reverb."""
    r = _rng(seed)
    n = int(d * SR)
    out = np.zeros(n)
    for k in range(int(60 * d)):
        i = int(r.random() * n * 0.8)
        f = base * 2 ** (r.integers(0, 4) + r.choice([0, 4 / 12, 7 / 12, 11 / 12]))
        L = int(SR * (0.06 + 0.2 * r.random()))
        g = np.sin(2 * np.pi * f * np.arange(L) / SR) * np.exp(-np.arange(L) / (0.05 * SR)) * (0.3 + 0.7 * r.random())
        out[i:i + L] += g[: n - i]
    out *= np.minimum(1, np.linspace(0, 3, n)) * np.linspace(1, 0.4, n)
    return reverb_tail(_st(out * level, 0.9, seed), 2.4, 0.55, seed)


def metal_shing(d=1.4, seed=11, level=0.35):
    """Blade drawn: a bright inharmonic ring with a rising noise scrape."""
    t = _t(d)
    r = _rng(seed)
    parts = [(2350, 1.0), (3710, 0.6), (5120, 0.45), (6890, 0.3)]
    ring = sum(np.sin(2 * np.pi * f * t + r.random() * 6) * g for f, g in parts) * np.exp(-t * 2.8)
    scrape = bp(r.standard_normal(len(t)), 3000, 12000) * np.exp(-((t - 0.25) ** 2) / 0.02) * 0.5
    m = (ring * 0.25 + scrape) * np.minimum(1, t / 0.03)
    return reverb_tail(_st(m * level, 0.7, seed), 2.0, 0.4, seed)


def drone(d, seed=12, f=55, level=0.2):
    t = _t(d)
    r = _rng(seed)
    m = sum(np.sin(2 * np.pi * f * k * (1 + 0.002 * r.standard_normal()) * t + r.random() * 6) / k for k in (1, 2, 3, 5))
    air = lp(r.standard_normal(len(t)), 1200) * 0.15
    e = np.minimum(1, t / 2) * np.minimum(1, (d - t) / 2)
    return _st((m * 0.3 + air) * e * level, 0.8, seed)


def lock_clunk(seed=13, level=0.6):
    d = 1.2
    t = _t(d)
    r = _rng(seed)
    thunk = np.sin(2 * np.pi * (140 * np.exp(-t * 20) + 60) * t) * np.exp(-t * 18)
    click = bp(r.standard_normal(len(t)), 1500, 8000) * np.exp(-t * 90) * 0.6
    m = (thunk + click) * level
    return reverb_tail(_st(m, 0.2, seed), 0.9, 0.25, seed)


def shatter(d=1.6, seed=14, level=0.5):
    r = _rng(seed)
    n = int(d * SR)
    out = np.zeros(n)
    for k in range(140):
        i = int(abs(r.normal(0.06, 0.18)) * SR)
        if i >= n:
            continue
        L = int(SR * (0.02 + 0.08 * r.random()))
        f = 2500 + 7000 * r.random()
        g = np.sin(2 * np.pi * f * np.arange(L) / SR) * np.exp(-np.arange(L) / (0.012 * SR)) * r.random()
        out[i:i + L] += g[: n - i]
    burst = hp(r.standard_normal(n), 2000) * np.exp(-np.arange(n) / (0.05 * SR)) * 0.8
    m = (out * 0.35 + burst) * level
    return reverb_tail(_st(m, 0.9, seed), 1.4, 0.35, seed)


def radio_sweep(d=2.0, seed=15, level=0.18):
    """Tuning across the dial: band-passed static with a sweeping whistle."""
    t = _t(d)
    r = _rng(seed)
    st = bp(r.standard_normal(len(t)), 400, 5000) * 0.5
    f = 900 + 1800 * np.sin(np.pi * t / d)
    wh = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.15
    e = np.sin(np.pi * t / d) ** 1.5
    return _st((st + wh) * e * level, 0.6, seed)


def pop(seed=16, level=0.3, f=900):
    d = 0.18
    t = _t(d)
    ff = f * (1 + 1.5 * np.exp(-t * 60))
    m = np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-t * 40) * level
    return _st(m, 0.3, seed)


def typing(d, seed=17, rate=11, level=0.25):
    r = _rng(seed)
    n = int(d * SR)
    out = np.zeros(n)
    tt = 0.0
    while tt < d:
        i = int(tt * SR)
        L = int(0.03 * SR)
        k = bp(r.standard_normal(L), 1500, 7000) * np.exp(-np.arange(L) / (0.004 * SR)) * (0.5 + 0.5 * r.random())
        out[i:i + L] += k[: n - i]
        tt += (1 / rate) * (0.6 + 0.8 * r.random())
    return _st(out * level, 0.5, seed)


def tape_shuttle(d=3.0, seed=18, level=0.25):
    """VCR fast search: warbling chirps and motor whine."""
    t = _t(d)
    r = _rng(seed)
    f = 900 + 300 * np.sin(2 * np.pi * 7 * t) + 200 * r.standard_normal(len(t)).cumsum() / SR * 0
    chirp = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.5 * (np.sin(2 * np.pi * 13 * t) > 0))) / SR) * 0.15
    motor = np.sin(2 * np.pi * 180 * t) * 0.1 + bp(r.standard_normal(len(t)), 2000, 6000) * 0.25
    e = np.minimum(1, t / 0.15) * np.minimum(1, (d - t) / 0.3)
    return _st((chirp + motor) * e * level, 0.5, seed)
