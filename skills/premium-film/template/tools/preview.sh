#!/bin/zsh
# usage: tools/preview.sh <name> <from-s> <to-s> [lang=master] [scale=0.5] [sheet-every-n-frames=6]
# Renders a stretch of the film at 30 fps (FilmDraft), half size, WITH its soundtrack when public/audio/mix-<lang>.wav
# exists, to tmp/prev/<name>.mp4, plus a contact sheet tmp/prev/<name>.jpg. PROPS adds props, e.g. PROPS='"captions":true'.
# The fastest honest look at a change: check the sheet, then the clip, before any full render.
setopt null_glob; unset FORCE_COLOR
zmodload zsh/mathfunc
cd "${0:A:h}/.."
name=$1; from=$2; to=$3; lang=${4:-$(sed -n 's/.*LANGS = \["\([a-z-]*\)".*/\1/p' src/film/script.ts)}; scale=${5:-0.5}; step=${6:-6}
a=$(( int(rint(from * 30)) )); b=$(( int(rint(to * 30)) - 1 ))
mkdir -p tmp/prev
export TMPDIR="$PWD/tmp/.render-tmp/"; mkdir -p $TMPDIR
npx remotion render src/index.ts FilmDraft tmp/prev/$name.silent.mp4 --props="{\"lang\":\"$lang\",\"withAudio\":false${PROPS:+,$PROPS}}" \
  --frames=$a-$b --scale=$scale --concurrency=${CONC:-2} --muted --crf=18 --log=error || { rm -rf $TMPDIR; exit 1; }
mix=public/audio/mix-$lang${VOICE:+-$VOICE}.wav
if [[ -f $mix ]]; then
  ffmpeg -v error -y -i tmp/prev/$name.silent.mp4 -ss $from -t $(( to - from )) -i $mix -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest tmp/prev/$name.mp4 && rm tmp/prev/$name.silent.mp4
else
  mv tmp/prev/$name.silent.mp4 tmp/prev/$name.mp4
fi
n=$(( (b - a + 1) / step )); cols=6; rows=$(( (n + cols - 1) / cols ))
ffmpeg -v error -y -i tmp/prev/$name.mp4 -vf "select='not(mod(n\,$step))',scale=320:180,tile=${cols}x${rows}" -frames:v 1 -fps_mode passthrough tmp/prev/$name.jpg
rm -rf $TMPDIR
echo "tmp/prev/$name.mp4 ($from–$to s, $lang) and its contact sheet tmp/prev/$name.jpg"
