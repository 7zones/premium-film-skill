"""Depth maps for 2.5D camera moves through photographs: Depth Anything V2 (Large) → 8-bit PNG, near = white.
  docker run --rm -v "$PWD":/p -w /p film-depth python tools/depth/depth.py public/depth public/plates/city.jpg [...]
Writes public/depth/<name>.png at the photo's size. Use with src/three/depth.tsx (DepthPlate / DepthCloud), and split
photos with people or objects in front into two layers (tools/depth/layers.py) before moving the camera much."""
import os
import sys

import cv2
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

name = "depth-anything/Depth-Anything-V2-Large-hf"
proc = AutoImageProcessor.from_pretrained(name)
model = AutoModelForDepthEstimation.from_pretrained(name).eval()
torch.set_num_threads(os.cpu_count())
out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)
for f in sys.argv[2:]:
    img = Image.open(f).convert("RGB")
    with torch.no_grad():
        # a larger working size keeps edges (shelves, faces) crisp
        inp = proc(images=img, return_tensors="pt", size={"height": 770, "width": 1372}, keep_aspect_ratio=True)
        d = model(**inp).predicted_depth[0].numpy()
    d = cv2.resize(d, img.size, interpolation=cv2.INTER_CUBIC)
    lo, hi = np.percentile(d, 0.5), np.percentile(d, 99.5)
    d = np.clip((d - lo) / (hi - lo), 0, 1)
    # edge-preserving smoothing removes 8-bit banding without blurring object edges
    d8 = cv2.bilateralFilter((d * 255).astype(np.float32), 9, 12, 9)
    out = os.path.join(out_dir, os.path.splitext(os.path.basename(f))[0] + ".png")
    Image.fromarray(np.clip(d8, 0, 255).astype(np.uint8)).save(out)
    print(out, img.size)
