"""Two-layer split of a photo rebuilt in depth, so camera moves never smear or open dark holes at depth edges:
the near layer is cut out along its depth discontinuities, and the far layer is the photo with the near layer
removed and filled in (LaMa), with its depth extended behind. A single depth surface smears and stretches around
people when the camera moves (it reads as a cheap "shadow" on every image); two layers do not.
  docker run --rm -v "$PWD":/p -w /p film-depth python tools/depth/layers.py public/plates/<name>.jpg[:threshold] ...
(reads the photo + public/depth/<name>.png from tools/depth/depth.py)
Writes public/<dir>/<name>-bg.jpg + public/depth/<name>-bg.png (far layer), public/depth/<name>-fg.png (near alpha) and
public/depth/<name>-fgd.png (near depth). Both depths are smoothed within their own layer, so each layer moves as a
clean relief (no stretched pixels at soft depth edges) and the parallax between them does the work."""
import sys, os, glob, numpy as np, cv2, torch
from PIL import Image
from simple_lama_inpainting import SimpleLama

torch.set_num_threads(os.cpu_count())
lama = SimpleLama()

for arg in sys.argv[1:]:
    path, _, thr = arg.partition(":")
    d = os.path.relpath(os.path.dirname(path), "public")
    name = os.path.splitext(os.path.basename(path))[0]
    img = np.array(Image.open(path).convert("RGB"))
    H, W = img.shape[:2]
    dep = cv2.imread(f"public/depth/{name}.png", cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
    dep = cv2.resize(dep, (W, H), interpolation=cv2.INTER_CUBIC)
    # the near layer = what stands off the surface behind it: depth minus a "what's behind" estimate (a wide,
    # flat opening keeps floors and walls, which run continuously, and removes figures and objects narrower
    # than it); a given number overrides the stand-off threshold
    t = float(thr) if thr else 0.07
    sw = 480
    ds = cv2.resize(dep, (sw, int(round(sw * H / W))), interpolation=cv2.INTER_AREA)
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(sw * 0.42) | 1, int(ds.shape[0] * 0.05) | 1))
    behind = cv2.morphologyEx(ds, cv2.MORPH_OPEN, ker)
    behind = cv2.GaussianBlur(behind, (0, 0), sw / 80)
    behind = cv2.resize(behind, (W, H), interpolation=cv2.INTER_CUBIC)
    near = ((dep - behind) > t).astype(np.uint8)
    # drop specks; keep only near regions that actually stand off what is behind them
    k = max(3, W // 400) | 1
    near = cv2.morphologyEx(near, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(near)
    keep = np.zeros_like(near)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] > W * H * 0.002: keep[lab == i] = 1
    near = keep
    # close gaps and fill enclosed holes (between an arm and a body) so the far layer never shows through them
    near = cv2.morphologyEx(near, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k * 3, k * 3)))
    inv = (1 - near).astype(np.uint8)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv)
    for i in range(1, n2):
        x, y, w, h, area = st2[i]
        touches = x == 0 or y == 0 or x + w == W or y + h == H
        if not touches and area < W * H * 0.03: near[lab2 == i] = 1
    # a close-up subject is wider than the "what's behind" estimate, so its middle (a face, a chest) can drop out of
    # the near layer and leave a ghost in the far one. A gap that is really "behind" meets the near layer at a depth
    # step; a false hole continues the near surface smoothly. Fill every non-near region (up to a quarter of the
    # frame) whose depth along its border with the near layer matches the near side.
    inv = (1 - near).astype(np.uint8)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv)
    ring = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1))
    near_ring = cv2.dilate(near, ring)
    for i in range(1, n2):
        if st2[i, cv2.CC_STAT_AREA] > W * H * 0.25 or st2[i, cv2.CC_STAT_AREA] < W * H * 0.001:
            continue
        comp = (lab2 == i).astype(np.uint8)
        inner = comp.astype(bool) & near_ring.astype(bool)
        outer = cv2.dilate(comp, ring).astype(bool) & near.astype(bool)
        if inner.sum() > 20 and outer.sum() > 20 and np.median(dep[outer]) - np.median(dep[inner]) < t * 0.6:
            near[comp.astype(bool)] = 1
    # the far layer: remove the near layer (plus its edge halo) and fill it in
    halo = max(6, W // 320)
    hole = cv2.dilate(near, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * halo + 1, 2 * halo + 1)))
    s = 1920 / W
    small = cv2.resize(img, (1920, int(round(H * s))), interpolation=cv2.INTER_AREA)
    msmall = cv2.resize(hole * 255, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST)
    filled = np.array(lama(Image.fromarray(small), Image.fromarray(msmall).convert("L")))[: small.shape[0], : small.shape[1]]
    filled = cv2.resize(filled, (W, H), interpolation=cv2.INTER_CUBIC)
    a = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), halo / 2)[..., None]
    bg = (img * (1 - a) + filled * a).astype(np.uint8)
    # its depth: the far depth extended under the hole
    dbg = cv2.inpaint((dep * 255).astype(np.uint8), hole, max(3, halo), cv2.INPAINT_TELEA)
    dbg = cv2.GaussianBlur(dbg.astype(np.float32), (0, 0), W / 90)
    # the near layer's depth, smoothed within the layer only (normalised blur), so its edges keep their own depth
    m = near.astype(np.float32)
    sig = W / 70
    num = cv2.GaussianBlur(dep * m, (0, 0), sig)
    den = cv2.GaussianBlur(m, (0, 0), sig)
    fgd = np.where(den > 1e-3, num / np.maximum(den, 1e-3), dep)
    fgd = np.maximum(fgd, dbg / 255 + 0.02)  # always in front of what is behind it
    # the near layer's alpha, feathered by a couple of pixels
    fg = cv2.GaussianBlur(near.astype(np.float32), (0, 0), max(1.0, W / 1600)) * 255
    Image.fromarray(bg).save(f"public/{d}/{name}-bg.jpg", quality=93)
    Image.fromarray(np.clip(dbg, 0, 255).astype(np.uint8)).save(f"public/depth/{name}-bg.png")
    Image.fromarray(np.clip(fgd * 255, 0, 255).astype(np.uint8)).save(f"public/depth/{name}-fgd.png")
    Image.fromarray(fg.astype(np.uint8)).save(f"public/depth/{name}-fg.png")
    print(name, f"stand-off {t:.2f}", f"near {near.mean() * 100:.0f}% of frame")
