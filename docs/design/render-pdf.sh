#!/usr/bin/env bash
# Renders software-design-report.md to software-design-report.pdf (A4) with Chromium in Docker,
# so the PDF looks the same on every computer. Needs only Docker. Run it after a change of the
# report or of a diagram (render.sh makes the diagrams).
set -euo pipefail
cd "$(dirname "$0")"
docker run --rm -v "$PWD:/design" python:3.15-slim bash -c '
  apt-get update -qq >/dev/null
  apt-get install -y -qq --no-install-recommends chromium fonts-dejavu-core >/dev/null
  pip install -q --root-user-action=ignore markdown
  python /design/report_to_html.py /design/software-design-report.md /tmp/report.html
  chromium --headless --no-sandbox --disable-gpu --no-pdf-header-footer --allow-file-access-from-files \
    --print-to-pdf=/design/software-design-report.pdf file:///tmp/report.html
'
echo "Done: software-design-report.pdf"
