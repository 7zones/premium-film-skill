#!/bin/zsh
# usage: tools/excerpt.sh <video> whole            → tmp/review/<name>-whole.mp4 (640 px, 24 fps, ≈5 MB for 3 min)
#        tools/excerpt.sh <video> <from-s> <to-s>  → tmp/review/<name>-<from>/ frames every 0.5 s named by film time
#                                                    (t012.5.jpg, 768 px) + audio.mp3
# Review media for tools/review.py. The small whole-film video is the cheapest full review; frames + mp3 work when a
# video upload is refused (OpenRouter needs ≥ $1 left on the key for video).
video=${1:A}; cd "${0:A:h}/.."; mkdir -p tmp/review; name=${video:t:r}
if [[ $2 == whole ]]; then
  ffmpeg -v error -y -i $video -vf "scale=640:-2,fps=24" -c:v libx264 -crf 32 -preset veryfast -c:a aac -b:a 96k -ac 1 tmp/review/$name-whole.mp4
  ls -la tmp/review/$name-whole.mp4; exit
fi
typeset -F 2 from=$2 to=$3 t   # fixed-point floats: an integer counter never advances by 0.5, and plain floats print as 7.0e+00
dir=tmp/review/$name-$2; mkdir -p $dir
for ((t = from; t < to; t += 0.5)); do
  ffmpeg -v error -y -ss $t -i $video -frames:v 1 -vf scale=768:-2 -q:v 3 $dir/t$(printf %05.1f $t).jpg
done
ffmpeg -v error -y -ss $from -t $(( to - from )) -i $video -vn -c:a libmp3lame -b:a 128k $dir/audio.mp3
ls $dir | head; echo "$(ls $dir | wc -l) files in $dir"
