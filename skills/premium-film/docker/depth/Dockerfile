# film-depth: photographs rebuilt in depth for 3D camera moves. Depth Anything V2 (Large) for the depth map and
# LaMa (big-lama) to fill in what is behind the near layer (tools/depth/layers.py).
#   docker build -t film-depth <skill>/docker/depth      (downloads ~1.5 GB of models once)
#   docker run --rm -v "$PWD":/p -w /p film-depth python tools/depth/depth.py public/depth public/plates/city.jpg
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir "transformers==4.57.*" pillow opencv-python-headless numpy
RUN pip install --no-cache-dir "simple-lama-inpainting==0.1.2" --no-deps && pip install --no-cache-dir fire
ENV HF_HOME=/hf LAMA_MODEL=/models/big-lama.pt
RUN mkdir -p /models && python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt', '/models/big-lama.pt')"
RUN python -c "from transformers import AutoImageProcessor, AutoModelForDepthEstimation as M; n='depth-anything/Depth-Anything-V2-Large-hf'; AutoImageProcessor.from_pretrained(n); M.from_pretrained(n)"
WORKDIR /p
