#!/bin/zsh
# Builds everything that ships, from the current source, in one command:
#   cues → narration check → score + mix per language → captions/.srt → thumbnails → 1080p60 masters (and their
#   captioned cuts) rendered silent in chunks, joined without re-encoding, the mix muxed in → the zip.
#
# usage: tools/release.sh                      everything
#        LANGS=en tools/release.sh             only these languages (the others' files are left as they are)
#        REDO=2700-3449 tools/release.sh       re-render only the chunks touching these frames (needs the SAME timeline
#                                              as the last release; the other chunks are reused from .render-chunks/)
#        VOICE=<name> tools/release.sh         the version narrated by another voice (tools/voice_warp.py first)
#        CAPTIONS=0 tools/release.sh           no captioned cuts
#        ZIP_ONLY=1 tools/release.sh           only rebuild the zip from the files already in out/ (after a stopped
#                                              release or a hand fix); it says when each file was made, so you can
#                                              see a stale one. A release stopped half-way has already rewritten the
#                                              captions/.srt for the new timing: finish it (REDO=99998-99999 reuses
#                                              every finished chunk) rather than shipping a mix of old and new.
#
# Never edit this file while it runs (zsh reads scripts as it goes): copy it, run the copy. Don't edit src/ while it
# is bundling. One release per project at a time. Long: run it in the background with a log and check the log.
set -e
setopt null_glob
unset FORCE_COLOR   # node would colour the numbers it prints
cd "${0:A:h}/.."

NAME=${NAME:-$(node -p 'require("./package.json").name')}   # output names: out/<NAME>-<LANG>[-<Voice>][-captioned].mp4
[[ -n $ZIP_ONLY ]] || npm run -s cues
ALL=($(node -p 'require("./audio/cues.json").langs.join(" ")'))   # the film's languages (src/film/script.ts)
LANGS=(${=LANGS:-$ALL})
V=${VOICE:-}; sfx=${V:+-${(C)V}}
CHUNK=150

# the deliverable: every language's masters, captioned cuts and thumbnails, stored (no compression; video doesn't
# compress) at the zip's root; rebuilt after every release so it never holds a stale cut
package() {
  local files=() f
  for L in $ALL; do
    for f in out/$NAME-${(U)L}$sfx.mp4 out/$NAME-${(U)L}$sfx-captioned.mp4 out/$NAME-thumbnail-${(U)L}.png; do [[ -f $f ]] && files+=(${f:t}); done
  done
  (cd out && rm -f $NAME$sfx.zip && zip -0 -q $NAME$sfx.zip $files && unzip -tq $NAME$sfx.zip)
  for f in $files; do echo "  $(date -r out/$f '+%d %b %H:%M')  $f"; done
}
if [[ -n $ZIP_ONLY ]]; then package; exit 0; fi
AUDIO_IMG=${AUDIO_IMG:-film-audio}; ASR_IMG=${ASR_IMG:-film-asr}
for img in $AUDIO_IMG $ASR_IMG; do docker image inspect $img >/dev/null 2>&1 || { echo "missing Docker image $img: run tools/setup.sh"; exit 2; }; done

# every narration line must exist, and none may carry a TTS glitch (vo_clean.py)
clips=()
for L in $LANGS; do
  clips+=($(node -e 'const c=require("./audio/cues.json");for(const v of c.vo)console.log("audio/vo/'${V:+$V/}$L'/"+v.id+".wav")'))
done
missing=$(for c in $clips; do [[ -f $c ]] || echo $c; done)
[[ -z "$missing" ]] || { echo "missing narration:"; echo "$missing"; exit 1; }
docker run --rm -v "$PWD":/p -w /p $AUDIO_IMG python tools/check_vo.py $clips

# each language's score and mix follow its own timing
for L in $LANGS; do
  [[ -f audio/score.py ]] && docker run --rm -e VOICE=$V -v "$PWD":/p -w /p $AUDIO_IMG python audio/score.py $L
  docker run --rm -e VOICE=$V -v "$PWD":/p -w /p $AUDIO_IMG python audio/mix.py $L
done
# captions before bundling: the captioned cut draws src/film/captions.gen.json
mkdir -p out
docker run --rm -e VOICE=$V -v "$PWD":/p -w /p $ASR_IMG python tools/captions.py $LANGS

# Other renders on this machine may clear the shared temp folder, so the bundle, Remotion's frames and every
# intermediate file live in a private folder here.
work="$PWD/.render-tmp"
rm -rf $work; mkdir -p $work/tmp $work/public
trap 'rm -rf $work' EXIT
export TMPDIR="$work/tmp/"
free_mb() { df -m "$PWD" | tail -1 | awk '{print $4}'; }
# another project's render (ours, and the shell running this script, carry this folder's path); keep the string
# "remotion render" out of any monitoring command you run, or this check will wait on it
others_rendering() { pgrep -fl "remotion render" | grep -v -F -- "$PWD" | grep -q . }
wait_room() {  # $1 = MB needed; also lets another project's render finish first
  local waited=0
  while (( $(free_mb) < $1 )) || others_rendering; do
    sleep 30; (( waited += 30 ))
    (( waited >= 7200 )) && { echo "gave up waiting for disk space ($(free_mb) MB free)"; exit 3; }
  done
}
# The picture renders silent; the bundle leaves the mixes out (its public folder links to everything else).
for f in public/*; do [[ ${f:t} == audio ]] || ln -s $PWD/$f $work/public/; done
npx remotion bundle src/index.ts --public-dir $work/public --out-dir $work/bundle --log=error
if [[ -z $V ]]; then
  for L in $LANGS; do
    npx remotion still $work/bundle Thumb-$L out/$NAME-thumbnail-${(U)L}.png --log=error
  done
fi

# Unless the OS reports lots of free memory (macOS rarely does), Remotion keeps every frame of a render on disk until
# it encodes (tens of GB for a 3-minute film), so the film renders 150 frames at a time as full-quality JPEGs (no
# visible difference after encoding). Concurrency 1: several tabs share Chrome's GPU budget and some draw centred
# text a pixel apart, which flickers; per-chunk start-up dominates anyway.
keep="$PWD/.render-chunks"
redo_a=-1; redo_b=-1
[[ -n $REDO ]] && { redo_a=${REDO%-*}; redo_b=${REDO#*-}; }
render() {  # $1 = lang, $2 = captions (true|false), $3 = output file
  local L=$1 cap=$2 target=$3 comp=Film-$1
  local frames=$(node -e 'const c=require("./audio/cues.json"),v="'$V'";console.log(Math.round((v?c.voices[v]["'$L'"].duration:c.duration["'$L'"])*60))')
  local dir=$keep/$L-$cap$sfx
  [[ -z $REDO ]] && rm -rf $dir
  mkdir -p $dir
  rm -f $work/chunks.txt
  for ((a = 0; a < frames; a += CHUNK)); do
    b=$(( a + CHUNK - 1 < frames - 1 ? a + CHUNK - 1 : frames - 1 ))
    part=$dir/$(printf %05d $a).mp4
    if [[ -n $REDO && -s $part ]] && (( b < redo_a || a > redo_b )); then echo "file '$part'" >> $work/chunks.txt; continue; fi
    for try in 1 2 3 4 5; do  # a disk that fills for a moment only costs a retry
      wait_room 1200
      npx remotion render $work/bundle $comp $part --props="{\"lang\":\"$L\",\"withAudio\":false,\"captions\":$cap${V:+,\"voice\":\"$V\"}}" \
        --frames=$a-$b --concurrency=1 --muted --crf=16 --pixel-format=yuv420p --image-format=jpeg --jpeg-quality=100 --timeout=240000 --log=error && break
      [[ $try == 5 ]] && { echo "chunk $L $a-$b failed"; exit 1; }
      echo "chunk $L $a-$b failed (try $try), retrying"
    done
    rm -rf $work/tmp/*
    echo "file '$part'" >> $work/chunks.txt
    echo "$target: frames $a-$b of $frames"
  done
  wait_room 700
  local mix=public/audio/mix-$L${V:+-$V}.wav
  ffmpeg -v error -y -r 60 -f concat -safe 0 -i $work/chunks.txt -i $mix -map 0:v:0 -map 1:a:0 \
    -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart $target
  # AAC raises peaks by up to ~1 dB: measure the delivered file and trim the mix's gain until it is ≤ −1 dBTP
  local gain=0 tp
  for pass in 1 2 3; do
    tp=$(ffmpeg -nostats -i $target -map 0:a -af ebur128=peak=true -f null - 2>&1 | awk '/True peak/{f=1} f&&/Peak:/{print $2; exit}')
    (( tp <= -1.0 )) && break
    gain=$(printf %.2f $(( gain - tp - 1.15 )))
    echo "$target: true peak $tp dBTP after encoding; the mix goes in ${gain} dB lower"
    ffmpeg -v error -y -i $target -i $mix -map 0:v:0 -map 1:a:0 -c:v copy -af volume=${gain}dB -c:a aac -b:a 320k \
      -shortest -movflags +faststart $target.tmp.mp4 && mv $target.tmp.mp4 $target
  done
  local got=$(ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of default=nk=1:nw=1 $target)
  [[ $got == $frames ]] || { echo "$target has $got frames, expected $frames"; exit 1; }
  echo "$target done: $frames frames ($(free_mb) MB free)"
}
for L in $LANGS; do render $L false out/$NAME-${(U)L}$sfx.mp4; done
if [[ ${CAPTIONS:-1} == 1 ]]; then
  for L in $LANGS; do render $L true out/$NAME-${(U)L}$sfx-captioned.mp4; done
fi
for L in $LANGS; do cp out/srt/$L${V:+-$V}.srt out/$NAME-${(U)L}$sfx.srt; done
rm -rf $work/bundle
echo "package out/$NAME$sfx.zip:"
package
