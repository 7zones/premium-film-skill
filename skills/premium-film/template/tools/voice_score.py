#!/usr/bin/env python3
"""Does a take still sound like the film's narrator? voice_score.py --ref <reference wavs...> -- <candidate wavs...>

  sim     speaker similarity (ECAPA cosine) to the mean of the reference lines; compare with the references' own
          leave-one-out spread printed first (a candidate well below it is a different-sounding narrator)
  pitch   median pitch in semitones against the references' median (+1 st or more already reads "younger/brighter")
  centre  spectral centroid in Hz (brightness; a dark, muffled take sits ~800 Hz against ~1000 Hz)
  dur     seconds

Ears beat numbers, but numbers catch what a quick listen misses: a user rejected takes 1–2.6 st above the original
as "not the correct voice — should be much deeper and calmer", and a formant-preserving pitch-down made similarity
WORSE (0.78 → 0.65). Use the score to shortlist, then let the person who owns the film pick by ear (in context).
Runs in the film-voice image: docker run --rm -v "$PWD":/p -w /p film-voice python tools/voice_score.py --ref … -- …"""
import os
import sys
import warnings

warnings.filterwarnings("ignore")
import librosa  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
import torch  # noqa: E402
from speechbrain.inference.speaker import EncoderClassifier  # noqa: E402

args = sys.argv[1:]
assert args[0] == "--ref" and "--" in args, __doc__
cut = args.index("--")
refs, cands = args[1:cut], args[cut + 1:]
enc = EncoderClassifier.from_hparams(source="/models/ecapa", savedir="/models/ecapa", run_opts={"device": "cpu"})


def load(f):
    x, sr = sf.read(f, dtype="float32")
    x = x if x.ndim == 1 else x.mean(1)
    return librosa.resample(x, orig_sr=sr, target_sr=16000) if sr != 16000 else x


def emb(x):
    with torch.no_grad():
        e = enc.encode_batch(torch.from_numpy(x)[None]).squeeze().numpy()
    return e / np.linalg.norm(e)


def pitch(x):
    f0, v, _ = librosa.pyin(x, fmin=55, fmax=320, sr=16000, frame_length=1024)
    return float(np.nanmedian(f0[v])) if np.any(v) else float("nan")


def centroid(x):
    c = librosa.feature.spectral_centroid(y=x, sr=16000)[0]
    rms = librosa.feature.rms(y=x)[0][: len(c)]
    return float(np.median(c[rms > 0.3 * rms.max()]))


R = [load(f) for f in refs]
E = np.stack([emb(x) for x in R])
mean = E.mean(0)
mean /= np.linalg.norm(mean)
loo = [float(E[i] @ ((E.sum(0) - E[i]) / np.linalg.norm(E.sum(0) - E[i]))) for i in range(len(E))] if len(E) > 2 else [1.0]
p0 = float(np.nanmedian([pitch(x) for x in R]))
print(f"references: {len(R)} lines; their own similarity median {np.median(loo):.3f} (p25 {np.percentile(loo, 25):.3f}); pitch {p0:.1f} Hz; "
      f"centre {np.median([centroid(x) for x in R]):.0f} Hz")
for f in cands:
    x = load(f)
    name = "/".join(os.path.normpath(f).split(os.sep)[-2:])
    print(f"{name:28s} sim {emb(x) @ mean:.3f}  pitch {12 * np.log2(pitch(x) / p0):+.2f} st  centre {centroid(x):5.0f} Hz  dur {len(x) / 16000:5.2f}s")
