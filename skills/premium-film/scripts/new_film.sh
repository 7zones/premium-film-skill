#!/bin/zsh
# usage: <skill>/scripts/new_film.sh <new-project-dir> [package-name]
# Starts a new film from the skill's template: a working Remotion project (timeline, scene clock, captions, 3D kit,
# example scenes), the audio engine, the tools and the Docker recipes, with a local git repo so every delivered
# version can be committed (a deleted concept the client later wanted back was only recoverable from logs).
set -e
skill=${0:A:h:h}
dest=${1:?usage: new_film.sh <dir> [name]}
name=${2:-${dest:t:l}}
[[ -e $dest ]] && { echo "$dest already exists"; exit 1; }
mkdir -p $dest
rsync -a --exclude node_modules --exclude out --exclude .render-tmp --exclude .render-chunks "$skill/template/" "$dest/"
rsync -a "$skill/docker/" "$dest/docker/"
cd $dest
node -e 'const f="package.json",p=require("./"+f);p.name=process.argv[1];require("fs").writeFileSync(f,JSON.stringify(p,null,2)+"\n")' "$name"
chmod +x tools/*.sh tools/*.py 2>/dev/null || true
git init -q && git add -A && git commit -qm "Start the film from the premium-film template" && echo "git: initial commit"
echo "created $dest ($name). Next: cd \"$dest\" && tools/setup.sh"
