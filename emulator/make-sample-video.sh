#!/usr/bin/env bash
#
# Build looping demo worksite videos from the sample JPGs in ../uploads so the
# RTSP emulator has footage to stream — no need to source real CCTV video.
#
# Produces one clip per emulated camera feed (see docker-compose.yml):
#   emulator/media/demo-worksite.mp4  -> rtsp://mediamtx:8554/worksite-demo  (cam-01, general floor)
#   emulator/media/loading-dock.mp4   -> rtsp://mediamtx:8554/loading-dock   (cam-02, loading dock)
#   emulator/media/welding-bay.mp4    -> rtsp://mediamtx:8554/welding-bay    (cam-03, welding station)
#
# The same sample stills appear on every feed; each zone's PPE policy turns the
# footage into different events (e.g. no_vest is high-severity in the dock yet
# ignored on the helmet-only floor).
#
# Requires a local ffmpeg. If you already have your own clips, just drop them in
# under emulator/media/ with the names above and skip this script.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
UPLOADS_DIR="$REPO_ROOT/uploads"
MEDIA_DIR="$SCRIPT_DIR/media"
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

# Encode an H.264 slideshow from an explicit, ordered list of images. The concat
# demuxer (rather than a glob) lets each clip use a different subset/order so the
# three feeds aren't byte-identical. Each image is normalized to 1280x720
# (letterboxed) so mixed-resolution stills encode cleanly into one stream.
build_clip() {
  local out="$1"; shift
  local list
  list="$(mktemp)"
  local img
  for img in "$@"; do
    printf "file '%s'\nduration %s\n" "$img" "$SECONDS_PER_IMAGE" >>"$list"
  done
  # concat demuxer drops the final image's duration; repeat it so it's shown.
  printf "file '%s'\n" "${@: -1}" >>"$list"

  echo "Building $(basename "$out") from $# image(s) at ${SECONDS_PER_IMAGE}s each..."
  ffmpeg -y -f concat -safe 0 -i "$list" \
    -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p" \
    -r 25 \
    -c:v libx264 -preset veryfast \
    "$out"
  rm -f "$list"
}

# Split the available stills across the two zone-specific feeds (round-robin so
# each gets a different mix). The floor feed shows the full set. Falls back to
# the full set if there are too few images to split.
dock_imgs=()
weld_imgs=()
idx=0
for img in "${images[@]}"; do
  if (( idx % 2 == 0 )); then
    dock_imgs+=("$img")
  else
    weld_imgs+=("$img")
  fi
  idx=$((idx + 1))
done
[ ${#dock_imgs[@]} -eq 0 ] && dock_imgs=("${images[@]}")
[ ${#weld_imgs[@]} -eq 0 ] && weld_imgs=("${images[@]}")

build_clip "$MEDIA_DIR/demo-worksite.mp4" "${images[@]}"
build_clip "$MEDIA_DIR/loading-dock.mp4" "${dock_imgs[@]}"
build_clip "$MEDIA_DIR/welding-bay.mp4" "${weld_imgs[@]}"

echo "Done. Clips written to $MEDIA_DIR:"
echo "  demo-worksite.mp4  loading-dock.mp4  welding-bay.mp4"
echo "Now run: docker compose up --build"
