#!/usr/bin/env bash
#
# Build a looping demo worksite video from the sample JPGs in ../uploads so the
# RTSP emulator has footage to stream — no need to source real CCTV video.
#
# Output: emulator/media/demo-worksite.mp4 (consumed by docker-compose's ffmpeg
# service and streamed to rtsp://mediamtx:8554/worksite-demo).
#
# Requires a local ffmpeg. If you already have your own clip, just drop it in
# as emulator/media/demo-worksite.mp4 and skip this script.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
UPLOADS_DIR="$REPO_ROOT/uploads"
MEDIA_DIR="$SCRIPT_DIR/media"
OUT="$MEDIA_DIR/demo-worksite.mp4"
SECONDS_PER_IMAGE="${SECONDS_PER_IMAGE:-2}"

mkdir -p "$MEDIA_DIR"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg not found. Install it (e.g. 'apt-get install ffmpeg' or 'brew install ffmpeg')." >&2
  exit 1
fi

shopt -s nullglob
images=("$UPLOADS_DIR"/*.jpg "$UPLOADS_DIR"/*.jpeg "$UPLOADS_DIR"/*.png)
if [ ${#images[@]} -eq 0 ]; then
  echo "No sample images found in $UPLOADS_DIR" >&2
  exit 1
fi

echo "Building $OUT from ${#images[@]} sample image(s) at ${SECONDS_PER_IMAGE}s each..."

# Each image is normalized to 1280x720 (letterboxed) so a slideshow of
# mixed-resolution stills encodes cleanly into a single H.264 stream.
ffmpeg -y \
  -framerate "1/${SECONDS_PER_IMAGE}" \
  -pattern_type glob -i "$UPLOADS_DIR/*.jpg" \
  -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p" \
  -r 25 \
  -c:v libx264 -preset veryfast \
  "$OUT"

echo "Done: $OUT"
echo "Now run: docker compose up --build"
