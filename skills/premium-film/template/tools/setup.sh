#!/bin/zsh
# usage: tools/setup.sh [all]
# Gets a machine ready to build this film: checks the basics, installs the npm packages, creates .env from the
# example, builds the Docker images the tools run in (film-audio + film-asr; "all" adds film-voice + film-depth),
# then checks which services the keys in .env reach and picks the best current model per job (tools/providers.py).
# Images are shared by every film on the machine: build once.
set -e
cd "${0:A:h}/.."
for b in node npx ffmpeg ffprobe docker; do command -v $b >/dev/null || { echo "missing: $b (install it first: Node 22+, ffmpeg, Docker Desktop or Colima)"; exit 1; }; done
docker info >/dev/null 2>&1 || { echo "Docker is installed but not running: start Docker Desktop (or 'colima start')"; exit 1; }
[[ -f .env ]] || { cp .env.example .env; chmod 600 .env; echo "created .env: add the keys you have (all optional; see the comments in it)"; }
[[ -d node_modules ]] || npm install --no-audit --no-fund
imgs=(audio asr); [[ $1 == all ]] && imgs+=(voice depth)
for i in $imgs; do
  if docker image inspect film-$i >/dev/null 2>&1; then echo "film-$i: ready"; else echo "building film-$i (first time only)…"; docker build -q -t film-$i docker/$i; fi
done
df -h . | tail -1 | awk '{print "free disk: " $4 " (a release needs a few GB; renders wait when it runs low)"}'
codex=$(command -v codex || { [[ -x /Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex ]] && echo /Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex; } || true)
echo; docker run --rm -e CODEX=$codex -v "$PWD":/p -w /p film-audio python tools/providers.py
echo; echo "ready: npx remotion studio  (preview)   ·   tools/release.sh  (build everything that ships)"
