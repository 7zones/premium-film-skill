#!/bin/zsh
zmodload zsh/mathfunc   # int() and other math functions
# usage: tools/strip.sh <video> <time-s> [span-s=1.0] [every-n-frames=1]
# Every frame (or every n-th) across a transition, tiled 10 across, to tmp/strips/. Transitions are judged frame by
# frame: a "hard cut" a reviewer reports may be a smooth move it sampled at 1 fps, and a real pop is only visible here.
video=${1:A}; t=$2; span=${3:-1.0}; every=${4:-1}
cd "${0:A:h}/.."; mkdir -p tmp/strips
start=$(( t - span / 2.0 )); (( start < 0 )) && start=0
fps=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 $video | awk -F/ '{print $1/$2}')
n=$(( int(span * fps / every) )); rows=$(( (n + 9) / 10 ))
out=tmp/strips/${video:t:r}-$t.jpg
ffmpeg -v error -y -ss $start -i $video -vf "trim=end_frame=$(( n * every )),select='not(mod(n\,$every))',scale=320:-1,tile=10x$rows" -frames:v 1 $out
echo $out
