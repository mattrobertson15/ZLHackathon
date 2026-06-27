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

# Echo the images in a per-zone source folder (emulator/media/sources/<zone>/),
# if any. Drop zone-specific stills there to theme a feed — e.g. dock workers
# missing hi-vis vests under sources/loading-dock/. Empty folder -> no output.
zone_images() {
  local dir="$SOURCES_DIR/$1"
  shopt -s nullglob
  local found=("$dir"/*.jpg "$dir"/*.jpeg "$dir"/*.png)
  printf '%s\n' "${found[@]}"
}

SOURCES_DIR="$MEDIA_DIR/sources"

# Fallback split of the shared uploads/ stills across the two zone feeds
# (round-robin so each gets a different mix), used when a zone folder is empty.
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

# Each feed: prefer its zone source folder; fall back to the shared stills.
# (output clip, zone source folder, fallback image list)
mapfile -t floor_zone < <(zone_images floor-entry)
mapfile -t dock_zone  < <(zone_images loading-dock)
mapfile -t weld_zone  < <(zone_images welding-bay)

floor_src=("${images[@]}");    [ ${#floor_zone[@]} -gt 0 ] && floor_src=("${floor_zone[@]}")
dock_src=("${dock_imgs[@]}");  [ ${#dock_zone[@]}  -gt 0 ] && dock_src=("${dock_zone[@]}")
weld_src=("${weld_imgs[@]}");  [ ${#weld_zone[@]}  -gt 0 ] && weld_src=("${weld_zone[@]}")

build_clip "$MEDIA_DIR/demo-worksite.mp4" "${floor_src[@]}"
build_clip "$MEDIA_DIR/loading-dock.mp4" "${dock_src[@]}"
build_clip "$MEDIA_DIR/welding-bay.mp4" "${weld_src[@]}"

echo "Done. Clips written to $MEDIA_DIR:"
echo "  demo-worksite.mp4  loading-dock.mp4  welding-bay.mp4"
echo "Tip: drop zone-specific stills in emulator/media/sources/<zone>/ to theme a feed."
echo "Now run: docker compose up --build"
