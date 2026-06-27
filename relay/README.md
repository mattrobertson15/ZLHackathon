# MediaMTX Relay — Phone RTSP Live Demo

Lets a phone act as a live CCTV camera for Safety Sentinel **while the backend is
hosted on Fly**. The phone can't be dialed into from the cloud (it's behind NAT
on Wi-Fi/cellular), so we flip the direction: the phone **pushes** its stream to
this relay, and the backend **pulls** from the relay over Fly's private network.

```
Phone (Larix Broadcaster) ──push RTMP (outbound)──► MediaMTX relay on Fly (public :1935)
                                                          │ rtsp://safety-sentinel-relay.internal:8554/phone-demo
                                                          ▼
                                                  safety-sentinel-api (existing camera monitor)
```

This reuses the same `rtsp://…/phone-demo` pull the backend already does for the
bundled `ffmpeg` file emulator (see [`../docker-compose.yml`](../docker-compose.yml));
only the publisher changes (a live phone instead of a looped file).

## Files

- `mediamtx.yml` — relay config. RTMP ingest + RTSP read; publish requires a
  password, read is open but only reachable on the private network.
- `Dockerfile` — bakes `mediamtx.yml` into a pinned `bluenviron/mediamtx` image.
- `fly.toml` — Fly app `safety-sentinel-relay`, exposes only RTMP `1935`.

## Deploy to Fly

```bash
cd relay
# Set a real publish password (don't ship the placeholder):
#   edit mediamtx.yml -> authInternalUsers[user: phone].pass
fly launch --no-deploy --copy-config --name safety-sentinel-relay
fly deploy
```

The backend (`safety-sentinel-api`) reaches the feed at
`rtsp://safety-sentinel-relay.internal:8554/phone-demo` with no extra config —
Fly's 6PN private network exposes every app over `.internal` automatically.

## Phone setup

Use a **broadcaster/push** app, not an RTSP *server* app.

**Streamlabs mobile (iOS/Android):** Settings → Go Live → Custom RTMP

```
RTMP URL:  rtmp://safety-sentinel-relay.fly.dev:1935/phone-demo
```

**Larix Broadcaster (iOS/Android):** Connections → add connection

```
URL:  rtmp://safety-sentinel-relay.fly.dev:1935/phone-demo
```

**Streamlabs OBS (desktop):** Settings → Stream → Custom

```
Server:     rtmp://safety-sentinel-relay.fly.dev:1935/live
Stream Key: phone-demo
```

Then in Safety Sentinel, use the RTSP URL that matches:

| Client              | RTSP URL for camera field |
|---------------------|---------------------------|
| Streamlabs mobile / Larix | `rtsp://safety-sentinel-relay.internal:8554/phone-demo` |
| Streamlabs OBS desktop    | `rtsp://safety-sentinel-relay.internal:8554/live/phone-demo` |

Start broadcasting, then in Safety Sentinel:

1. Cameras page → paste the matching RTSP URL → **Test Stream** (should report Connected).
2. Register the camera (zone `general-floor`, interval `1–2s`) → **Start monitoring**.
3. Walk into frame without a hard hat → a violation event + the red
   "Live Violation Detected" banner appear on the camera detail page.

## Local test (no Fly)

The repo's [`../docker-compose.yml`](../docker-compose.yml) already runs mediamtx +
the file emulator. To test the phone push locally, point Larix at
`rtmp://<your-laptop-ip>:1935/phone-demo` and confirm with
`ffprobe rtsp://localhost:8554/phone-demo`.

## Notes

- Bump the pinned `bluenviron/mediamtx` tag in the `Dockerfile` as needed; if you
  upgrade across a major version, re-check the `authInternalUsers` schema against
  the [MediaMTX docs](https://github.com/bluenviron/mediamtx#authentication).
- RTSP `8554` is deliberately private. Validate reachability with the backend's
  `POST /cameras/test-stream` (runs inside Fly), not from your laptop.
