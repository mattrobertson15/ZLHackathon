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

## Quick start

```bash
# 1. Build demo footage from the bundled sample images (needs local ffmpeg).
#    Or drop your own clip in as emulator/media/demo-worksite.mp4 and skip this.
./emulator/make-sample-video.sh

# 2. Bring up mediamtx + ffmpeg + backend.
docker compose up --build

# 3. Open the frontend, go to Cameras, register:
#      RTSP URL: rtsp://mediamtx:8554/worksite-demo   (inside compose)
#                rtsp://localhost:8554/worksite-demo   (testing from host)
#    Click "Start monitoring" — events appear on Dashboard/Events automatically.
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
