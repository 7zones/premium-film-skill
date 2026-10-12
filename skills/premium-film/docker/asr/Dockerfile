# film-asr: Whisper large-v3 (faster-whisper, CPU int8) for word times: cutting takes into lines, checking what the
# narrator actually said, timing captions and re-timing a film to a new voice.
#   docker build -t film-asr <skill>/docker/asr          (downloads ~3 GB of model once)
#   docker run --rm -v "$PWD":/p -w /p film-asr python tools/cut_lines.py ...
# Two Whisper containers at once can run out of memory: run them one after another.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "faster-whisper==1.1.1" requests soundfile numpy
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3', device='cpu', compute_type='int8', download_root='/models')"
WORKDIR /p
