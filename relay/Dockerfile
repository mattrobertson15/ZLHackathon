# MediaMTX relay for the Safety Sentinel phone-RTSP demo.
# Bakes our mediamtx.yml into the upstream image so Fly can run it with no mounts.
# Pin a specific release for reproducibility; bump as needed.
FROM bluenviron/mediamtx:1.11.3

COPY mediamtx.yml /mediamtx.yml
