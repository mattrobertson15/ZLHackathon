# Per-zone source images (optional)

Drop zone-specific stills here to theme each emulated camera feed. The generator
(`../../make-sample-video.sh`) builds each clip from its matching folder below;
if a folder is **empty**, it falls back to a split of the shared `uploads/` stills,
so the demo works whether or not you add anything here.

| Folder | Feed clip | Camera / zone | What to put here |
|--------|-----------|---------------|------------------|
| `floor-entry/` | `demo-worksite.mp4` | cam-01 / general-floor (helmet) | workers with/without **hard hats** |
| `loading-dock/` | `loading-dock.mp4` | cam-02 / loading-dock (vest) | workers with/without **hi-vis vests** |
| `welding-bay/` | `welding-bay.mp4` | cam-03 / welding-station (helmet+vest) | workers with/without **helmet + vest** |

Accepted: `.jpg`, `.jpeg`, `.png`. Then rebuild: `./emulator/make-sample-video.sh`.

> Note: with the **mock** detector (no `ROBOFLOW_API_KEY`/Qwen), image *content*
> doesn't affect events — mock detections are seeded off the frame path, so these
> images only change the live snapshot preview. Themed images matter when a real
> vision model is driving detections. See ARCHITECTURE.md#vision-inference-layer.
