# film-voice: speaker similarity (ECAPA), pitch and brightness, to tell whether a new take still sounds like the
# film's narrator.
#   docker build -t film-voice <skill>/docker/voice
#   docker run --rm -v "$PWD":/p -w /p film-voice python tools/voice_score.py --ref audio/vo/en/*.wav -- take.wav
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir "speechbrain==1.*" soundfile numpy librosa huggingface_hub
RUN python -c "from speechbrain.inference.speaker import EncoderClassifier; EncoderClassifier.from_hparams(source='speechbrain/spkrec-ecapa-voxceleb', savedir='/models/ecapa')"
WORKDIR /p
