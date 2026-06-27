# RTSP Camera Emulator

Emulates a CCTV camera by looping a video file into an RTSP stream, so Safety
Sentinel can treat it like a real feed. See
[ARCHITECTURE.md](../ARCHITECTURE.md#camera--rtsp-ingestion-layer) and the demo
walkthrough in [DEMOSCRIPT.md](../DEMOSCRIPT.md).

## How it works

`ffmpeg -re -stream_loop -1 -i demo-worksite.mp4 -f rtsp rtsp://.../worksite-demo`
restreams a file in a realtime loop. **`ffmpeg` alone is not enough** — `-f rtsp`
*pushes* to an RTSP server that must already be listening. We run
[mediamtx](https://github.com/bluenviron/mediamtx) as that server. Both run as
containers in [`docker-compose.yml`](../docker-compose.yml).

## Multiple feeds

The stack emulates **three cameras at once**, one per seeded zone, so the demo
shows the same footage producing *different* events under each zone's PPE policy:

| Camera (seeded) | Zone | RTSP path | Clip |
|-----------------|------|-----------|------|
| cam-01 Floor Entry | general-floor (helmet) | `worksite-demo` | `demo-worksite.mp4` |
| cam-02 Dock North | loading-dock (vest, no_vest→high) | `loading-dock` | `loading-dock.mp4` |
| cam-03 Welding Bay | welding-station (helmet+vest) | `welding-bay` | `welding-bay.mp4` |

`make-sample-video.sh` builds all three clips, and `docker-compose.yml` runs one
`ffmpeg` service per feed. The three seeded cameras are pre-wired to these RTSP
URLs and (with `SEED_CAMERA_MONITORING=true`, set in compose) **start monitoring
automatically** — no manual registration needed.

To theme a feed with your own stills, drop images into the matching
`media/sources/<zone>/` folder (`floor-entry`, `loading-dock`, `welding-bay`) and
rebuild — see [media/sources/README.md](media/sources/README.md). Empty folders
fall back to the shared `uploads/` stills, so this is entirely optional.

## Quick start

```bash
# 1. Build the three demo clips from the bundled sample images (needs local ffmpeg).
#    Or drop your own clips in as emulator/media/{demo-worksite,loading-dock,welding-bay}.mp4.
./emulator/make-sample-video.sh

# 2. Bring up mediamtx + the three ffmpeg feeds + backend.
docker compose up --build

# 3. Open the frontend → Cameras. cam-01/02/03 are already monitoring; live
#    snapshots and events flow into Dashboard/Events/Alerts automatically.
#    (To drive a feed manually instead, register an RTSP URL from the table above:
#     rtsp://mediamtx:8554/<path> inside compose, rtsp://localhost:8554/<path> from host.)
```

## Verify the stream directly

```bash
ffprobe rtsp://localhost:8554/worksite-demo     # or open it in VLC
```

## Live phone camera (instead of a looped file)

The same relay works with a **live phone** as the publisher — walk past it without
a hard hat for a believable live demo. The phone *pushes* its stream to MediaMTX
(outbound, so it works through NAT/Wi-Fi) and the backend pulls it exactly like
this file emulator. The deployable relay app (config + Fly `fly.toml`) lives in
[`../relay/`](../relay/) — see [relay/README.md](../relay/README.md) for the phone
app (Larix Broadcaster), the publish URL, and the Test Stream check.

## Deploying

The always-on stack (backend + mediamtx + ffmpeg) must run on a persistent
container host — Fly.io, Render, Railway, or a VM — **not Vercel** (serverless
can't run the background monitor or hold an RTSP connection). Keep the Vercel
frontend and point its `NEXT_PUBLIC_API_URL` at the container host's public API
URL. Inside the host's private network the backend still reaches the feed at
`rtsp://mediamtx:8554/worksite-demo`, so the RTSP stream itself stays private. For
the hosted Fly setup (backend app + separate relay app) see
[relay/README.md](../relay/README.md).
