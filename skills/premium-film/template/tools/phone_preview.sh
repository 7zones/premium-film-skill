#!/bin/zsh
zmodload zsh/mathfunc   # int() and other math functions
# usage: tools/phone_preview.sh <video> [max-MB=25]
# A 30 fps copy small enough to send through chat apps and phone viewers (many cap uploads at ~30 MB), sized by a
# two-pass encode to fit. Only when someone needs to watch on a phone; it is not a deliverable unless asked for.
video=${1:A}; max=${2:-25}
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $video)
kbps=$(( int((max * 8192.0 * 0.93 / dur) - 160) ))   # 7% headroom for the container and the audio
out=${video:r}-preview.mp4
cd "${TMPDIR:-/tmp}"
ffmpeg -v error -y -i $video -c:v libx264 -preset slow -b:v ${kbps}k -r 30 -pass 1 -an -f mp4 /dev/null && \
ffmpeg -v error -y -i $video -c:v libx264 -preset slow -b:v ${kbps}k -maxrate $(( kbps * 3 / 2 ))k -bufsize $(( kbps * 3 ))k -r 30 -pass 2 -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart $out
rm -f ffmpeg2pass-0.log ffmpeg2pass-0.log.mbtree
ls -la $out
