# Phone Live Stream Setup

Goal: use a phone as a live CCTV camera for the Safety Sentinel demo while the
backend runs on Fly.

## Architecture

```
Phone ──push RTMP (outbound, port 1935)──► MediaMTX relay (Fly, public)
                                                  │
                              rtsp://safety-sentinel-relay.internal:8554/phone-demo
                                                  │
                                                  ▼
                                    safety-sentinel-api (pulls frames)
```

The phone **pushes** outbound to the relay — it never needs to be reachable from
the internet. The backend **pulls** RTSP over Fly's private `.internal` network.

## What's Deployed

| Resource | Value |
|---|---|
| Relay app | `safety-sentinel-relay` on Fly (region: sjc) |
| Public IP | `213.188.215.51` (dedicated, $2/mo) |
| RTMP ingest (public) | `rtmp://safety-sentinel-relay.fly.dev:1935/phone-demo` |
| RTSP pull (private) | `rtsp://safety-sentinel-relay.internal:8554/phone-demo` |
| Auth | Disabled (open publish for demo simplicity) |

## What to Enter in the Safety Sentinel Camera UI

RTSP URL field: `rtsp://safety-sentinel-relay.internal:8554/phone-demo`

Hit **Test Stream** only after the phone is actively broadcasting — the backend
needs a live stream to grab a frame from.

## Larix Broadcaster — What Was Tried (iOS/Android)

Larix Broadcaster is a free push-RTMP app. Connection kept failing:

- **"Phone could not connect to server"** — turned out port 1935 had no public IP
  assigned (Fly doesn't auto-assign one for raw TCP). Fixed by allocating a
  dedicated IPv4.
- **"Can't find the app and stream"** — RTMP auth rejection. Fixed by removing
  the publish password from `mediamtx.yml` (open publish).
- Still failing after both fixes — root cause unclear; possibly Larix URL
  parsing, cellular carrier blocking port 1935, or RTMP handshake quirk.

Larix connection string format it expects: `rtmp://server/application/streamkey`

## Alternative Push Options to Try

### 1. ffmpeg on a laptop (easiest to debug)
```bash
ffmpeg -re -i YOUR_VIDEO.mp4 \
  -c:v libx264 -preset veryfast -b:v 2000k \
  -c:a aac -b:a 128k \
  -f flv rtmp://safety-sentinel-relay.fly.dev:1935/phone-demo
```
Confirms the relay works end-to-end before blaming the phone.

### 2. OBS Studio (desktop)
Settings → Stream → Custom, then:
- Server: `rtmp://safety-sentinel-relay.fly.dev:1935`
- Stream Key: `phone-demo`

### 3. Streamlabs Mobile (iOS/Android)
Alternative to Larix. Custom RTMP:
- URL: `rtmp://safety-sentinel-relay.fly.dev:1935/phone-demo`

### 4. Use port 80 instead of 1935
Some cellular carriers block port 1935. MediaMTX can listen on port 80 for RTMP
instead. Would require updating `mediamtx.yml` + `fly.toml` and redeploying.

### 5. WebRTC ingest (no relay needed)
MediaMTX supports WebRTC push. A browser tab on the phone could push video
directly. Requires enabling `webrtc: yes` in `mediamtx.yml` and exposing port
8889. The phone camera stream would come from a simple HTML page using
`getUserMedia`.

## Files

| File | Purpose |
|---|---|
| `relay/mediamtx.yml` | MediaMTX config (protocols, auth, paths) |
| `relay/Dockerfile` | Bakes config into `bluenviron/mediamtx:1.11.3` |
| `relay/fly.toml` | Fly app config, exposes RTMP port 1935 |
| `backend/app/utils/rtsp_capture.py` | Backend RTSP frame capture |
| `frontend/app/app/cameras/page.tsx` | Camera registration + Test Stream UI |
