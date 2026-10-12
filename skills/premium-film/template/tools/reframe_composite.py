#!/usr/bin/env python3
"""Lays a real photo back over the wide canvas Codex drew around it (tools/imagegen.sh reframe), so the person stays
exactly the original photograph and only the new surroundings are generated.
  docker run --rm -v "$PWD":/p -w /p film-audio python tools/reframe_composite.py \
      <canvas.png> <photo.jpg> <mask.png> <out.jpg> <full|person> [out_width]
full:   the whole photo goes back (its edges feathered into the canvas), for a pure extension;
person: only the person goes back (Apple subject mask from tools/mac/subject_mask.swift), for a new background.
The photo is found in the canvas by SIFT matches on the person and a RANSAC similarity fit; the canvas is
colour-matched to the photo around the seam and given the photo's grain."""
import sys

import cv2
import numpy as np

canvas_p, photo_p, mask_p, out_p, mode = sys.argv[1:6]
out_w = int(sys.argv[6]) if len(sys.argv) > 6 else 0

G = cv2.imread(canvas_p, cv2.IMREAD_COLOR)
O = cv2.imread(photo_p, cv2.IMREAD_COLOR)
M = cv2.imread(mask_p, cv2.IMREAD_GRAYSCALE)
assert G is not None and O is not None and M is not None
M = cv2.resize(M, (O.shape[1], O.shape[0]), interpolation=cv2.INTER_LINEAR)

# --- where the photo sits in the canvas: match on the person (the background may have been replaced)
sift = cv2.SIFT_create(nfeatures=8000)
k = min(1.0, 1600 / max(O.shape[:2]))
Os = cv2.resize(O, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
Ms = cv2.resize(M, (Os.shape[1], Os.shape[0]))
detect_mask = (cv2.dilate(Ms, np.ones((25, 25), np.uint8)) > 40).astype(np.uint8) * 255 if mode == "person" else None
ko, do = sift.detectAndCompute(cv2.cvtColor(Os, cv2.COLOR_BGR2GRAY), detect_mask)
kg, dg = sift.detectAndCompute(cv2.cvtColor(G, cv2.COLOR_BGR2GRAY), None)
pairs = cv2.BFMatcher(cv2.NORM_L2).knnMatch(do, dg, k=2)
good = [m for m, n in (p for p in pairs if len(p) == 2) if m.distance < 0.72 * n.distance]
src = np.float32([ko[m.queryIdx].pt for m in good]) / k  # photo pixels
dst = np.float32([kg[m.trainIdx].pt for m in good])  # canvas pixels
A, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=3.0, maxIters=20000, confidence=0.999)
n_in = int(inl.sum())
scale = float(np.hypot(A[0, 0], A[1, 0]))
rot = float(np.degrees(np.arctan2(A[1, 0], A[0, 0])))
resid = np.linalg.norm((src[inl.ravel() == 1] @ A[:, :2].T + A[:, 2]) - dst[inl.ravel() == 1], axis=1)
print(f"matches {len(good)}, inliers {n_in}, photo→canvas scale {scale:.4f}, rotation {rot:.2f}°, residual median {np.median(resid):.2f}px")
assert n_in >= 30, "the canvas does not contain the photo closely enough"

# --- output frame: the photo stays upright at its own resolution; the canvas is turned to fit it (Codex may
# draw the scene a degree off) and the largest 16:9 window inside the turned canvas is kept
th = np.radians(rot)
Ainv = cv2.invertAffineTransform(A)  # canvas → photo
cw, ch = G.shape[1] / scale, G.shape[0] / scale  # canvas size in photo pixels
kfit = min(cw / (cw * abs(np.cos(th)) + ch * abs(np.sin(th))), ch / (cw * abs(np.sin(th)) + ch * abs(np.cos(th))))
W0 = cw * kfit
H0 = W0 * 9 / 16
if H0 > ch * kfit:
    H0 = ch * kfit
    W0 = H0 * 16 / 9
cc = Ainv @ np.array([G.shape[1] / 2, G.shape[0] / 2, 1.0])  # canvas centre, in photo pixels
s_o = min(1.0, 3840 / W0) if not out_w else out_w / W0
W = int(round(W0 * s_o / 2)) * 2
H = int(round(W * 9 / 16 / 2)) * 2
P = np.float32([[s_o, 0, W / 2 - s_o * cc[0]], [0, s_o, H / 2 - s_o * cc[1]]])  # photo → output
B = np.vstack([P, [0, 0, 1]]) @ np.vstack([Ainv, [0, 0, 1]])  # canvas → output
Gb = cv2.warpAffine(G, B[:2], (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
A_out = P
Ow = cv2.warpAffine(O, A_out, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
inside = cv2.warpAffine(np.full(O.shape[:2], 255, np.uint8), A_out, (W, H), flags=cv2.INTER_NEAREST)
feather = max(6, int(W * (0.004 if mode == "person" else 0.02)))
if mode == "person":
    # stay a few pixels inside his outline, so none of the photo's old background (a bright slide) survives
    # along the edge; the canvas's own rendering of that edge takes over there
    m = cv2.warpAffine(M, A_out, (W, H), flags=cv2.INTER_LINEAR)
    m = cv2.erode(m, np.ones((3, 3), np.uint8), iterations=max(2, int(W * 0.002)))
else:
    m = cv2.erode(inside, np.ones((3, 3), np.uint8), iterations=feather)
alpha = cv2.GaussianBlur(m.astype(np.float32) / 255.0, (0, 0), feather / 2.0)
alpha *= (inside > 0)
a3 = alpha[..., None]

# --- colour: match the canvas to the photo in the band around the seam (Lab mean/std)
# full: the seam band, where both show the same background; person: the person, whom both show
band = ((alpha > 0.05) & (alpha < 0.95)) if mode == "full" else (alpha > 0.95)
if band.sum() > 500:
    gl = cv2.cvtColor(np.clip(Gb, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    ol = cv2.cvtColor(np.clip(Ow, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    for c in range(3):
        gm, gs = gl[..., c][band].mean(), gl[..., c][band].std() + 1e-3
        om, os_ = ol[..., c][band].mean(), ol[..., c][band].std() + 1e-3
        k_ = float(np.clip(os_ / gs, 0.8, 1.25))
        gl[..., c] = (gl[..., c] - gm) * k_ + om
        print(f"  Lab[{c}] canvas {gm:6.1f}±{gs:5.1f} → photo {om:6.1f}±{os_:5.1f}")
    Gb = cv2.cvtColor(np.clip(gl, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)

# --- grain: give the upscaled canvas the photo's own fine noise
def hf_std(img, sel):
    g = cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    return float((g - cv2.GaussianBlur(g, (0, 0), 1.2))[sel].std())
sel = (alpha > 0.98)
if sel.sum() > 1000:
    target, have = hf_std(Ow, sel), hf_std(Gb, alpha < 0.02)
    extra = max(0.0, target**2 - have**2) ** 0.5
    rng = np.random.default_rng(7)
    noise = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.6)
    noise *= extra / (noise.std() + 1e-6)
    Gb += noise[..., None]
    print(f"  grain photo {target:.2f}, canvas {have:.2f} → +{extra:.2f}")

out = Ow * a3 + Gb * (1 - a3)
cv2.imwrite(out_p, np.clip(out, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 93])
# where the photo's corners and the person sit in the output, for framing the shot
corners = np.float32([[0, 0], [O.shape[1], 0], [O.shape[1], O.shape[0]], [0, O.shape[0]]]) @ A_out[:, :2].T + A_out[:, 2]
ys, xs = np.nonzero(cv2.warpAffine(M, A_out, (W, H)) > 128)
print(f"wrote {out_p} {W}x{H}; photo corners {np.round(corners).astype(int).tolist()}; person box x {xs.min()}–{xs.max()}, y {ys.min()}–{ys.max()}")
