# film-audio: score, sound design, mixing, narration clean-up and music analysis.
#   docker build -t film-audio <skill>/docker/audio
#   docker run --rm -v "$PWD":/p -w /p film-audio python audio/mix.py
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      libsndfile1 ffmpeg fluidsynth musescore-general-soundfont-lossless fluid-soundfont-gm \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "numpy==2.*" "scipy==1.*" "soundfile==0.12.*" "pedalboard==0.9.*" \
      "pyloudnorm==0.1.*" "mido==1.3.*" "librosa==0.11.*" "opencv-python-headless==4.*"
WORKDIR /p
