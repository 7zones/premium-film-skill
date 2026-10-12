#!/bin/zsh
# Reads a web page the way a person sees it: rendered in a real (headless) browser, so pages that only appear after
# their JavaScript runs still give their text, plus a tall screenshot to see the brand's real colours, type, logo and
# product UI. Saves tmp/research/<name>.txt and tmp/research/<name>.png.
#
#   tools/webpage.sh <url> <name>
#   tools/webpage.sh archive:<domain-or-url> <name>     the newest Internet Archive copy (for a site that is down:
#                                                        an HTTP 5xx/522, a timeout, or a page that is gone)
#
# Uses Remotion's own headless browser (installed with the project; fetched once by `npx remotion browser ensure`).
# Public pages only: never log in, submit forms or read walled sites. Record every page you rely on in the fact
# sheet with its URL and date.
set -e
cd "${0:A:h}/.."
url=$1; name=${2:?usage: webpage.sh <url | archive:domain> <name>}
mkdir -p tmp/research
if [[ $url == archive:* ]]; then
  target=${url#archive:}
  # the copy closest to today (the archive redirects to it)
  read snap code <<< "$(curl -s -o /dev/null -L -m 40 -w '%{url_effective} %{http_code}' "https://web.archive.org/web/$(date +%Y%m%d)/$target")"
  [[ $snap == *web.archive.org/web/[0-9]* ]] || { echo "no Internet Archive copy of $target (or the archive is busy: try later); use other sources and ask the owner"; exit 1; }
  year=${${snap#*web.archive.org/web/}[1,4]}
  (( year < $(date +%Y) - 1 )) && echo "warning: the newest archive copy is from $year — probably not the current product"
  [[ $code == 200 ]] || echo "warning: that archive copy is an error page (HTTP $code)"
  echo "archive copy: $snap"
  url=$snap
fi
bin=$(ls node_modules/.remotion/chrome-headless-shell/*/*/chrome-headless-shell 2>/dev/null | head -1)
[[ -n $bin ]] || { npx remotion browser ensure >/dev/null 2>&1; bin=$(ls node_modules/.remotion/chrome-headless-shell/*/*/chrome-headless-shell 2>/dev/null | head -1); }
[[ -n $bin ]] || { echo "no headless browser: run npx remotion browser ensure"; exit 1; }
# a real browser's identity and 12 s of virtual time let client-side pages finish rendering
flags=(--headless --disable-gpu --hide-scrollbars --virtual-time-budget=12000
  --user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36")
$bin $flags --dump-dom "$url" 2>/dev/null > tmp/research/$name.html || true
$bin $flags --window-size=1440,4200 --screenshot="$PWD/tmp/research/$name.png" "$url" >/dev/null 2>&1 || true
node -e '
const fs = require("fs");
const h = fs.readFileSync(process.argv[1], "utf8")
  .replace(/<(script|style|noscript|svg)[^>]*>[\s\S]*?<\/\1>/gi, " ")
  .replace(/<(br|\/p|\/div|\/li|\/h[1-6]|\/section|\/tr)[^>]*>/gi, "\n")
  .replace(/<[^>]+>/g, " ")
  .replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&#39;|&apos;/g, "\x27").replace(/&quot;/g, "\"");
const lines = h.split("\n").map((l) => l.replace(/\s+/g, " ").trim()).filter(Boolean);
fs.writeFileSync(process.argv[2], lines.join("\n") + "\n");
console.log(`${lines.length} lines of text`);
' tmp/research/$name.html tmp/research/$name.txt
rm -f tmp/research/$name.html
[[ -s tmp/research/$name.png ]] && echo "tmp/research/$name.txt  tmp/research/$name.png  ($url)" || echo "tmp/research/$name.txt (no screenshot)  ($url)"
grep -qi "blocked because our system has flagged" tmp/research/$name.txt && echo "the Internet Archive is refusing automated visits from this machine for now (too many requests): try again later, use other sources, and ask the owner"
[[ $(wc -l < tmp/research/$name.txt) -gt 3 ]] || echo "almost no text: the site may be down (try archive:<domain>) or block automated visits — use other sources and ask the owner"
