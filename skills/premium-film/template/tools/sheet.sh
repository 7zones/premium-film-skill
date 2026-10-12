#!/bin/zsh
# usage: tools/sheet.sh <video> [every-seconds=2] [cols=6] [rows=5]
# Contact sheets of a whole video (one frame every N seconds, 6×5 per sheet) in tmp/sheets/. Look at every sheet of
# both languages before calling a cut done: it is how a missing beat, a dark stretch or a repeated layout shows up.
setopt null_glob
video=${1:A}; every=${2:-2}; cols=${3:-6}; rows=${4:-5}
cd "${0:A:h}/.."; mkdir -p tmp/sheets
base=${video:t:r}
ffmpeg -v error -y -i $video -vf "fps=1/$every,scale=384:216,tile=${cols}x${rows}" -fps_mode passthrough tmp/sheets/$base-%02d.jpg
ls tmp/sheets/$base-*.jpg
