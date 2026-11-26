#!/usr/bin/env bash
# Renders software-design-report.md to software-design-report.pdf (A4) in Docker, so the PDF looks
# the same on every computer. Needs only Docker. Run it after a change of the report or of a
# diagram (render.sh makes the diagrams).
#   1. pandoc reads the report as GitHub Markdown and writes HTML with the style of report.css.
#   2. Chromium prints the HTML to PDF. The images are read from this folder.
set -euo pipefail
cd "$(dirname "$0")"
docker run --rm -v "$PWD:/design:ro" pandoc/core:3.14 \
  /design/software-design-report.md --from gfm --to html5 --standalone \
  --metadata pagetitle="OmniLog Software Design Report" --css file:///design/report.css \
  --variable header-includes='<base href="file:///design/">' \
  | docker run --rm -i -v "$PWD:/design" debian:trixie-slim bash -c '
      cat > /tmp/report.html
      apt-get update -qq >/dev/null
      apt-get install -y -qq --no-install-recommends chromium fonts-dejavu-core >/dev/null
      chromium --headless --no-sandbox --disable-gpu --no-pdf-header-footer --allow-file-access-from-files \
        --print-to-pdf=/design/software-design-report.pdf file:///tmp/report.html 2>/dev/null
    '
echo "Done: software-design-report.pdf"
