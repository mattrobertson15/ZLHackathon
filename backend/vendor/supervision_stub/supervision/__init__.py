"""Stub for the real `supervision` package.

inference-sdk's loaders.py does `import supervision as sv` at module load
time, but only calls `sv.get_video_frames_generator` / `sv.list_files_with_extensions`
for video/directory inputs. This project only calls `client.infer(image_path, ...)`
with a single image file path, which never reaches those functions.

The real `supervision` package pulls in matplotlib + scipy (~125MB installed)
purely for that unused code path. This stub satisfies the import without the
weight; see ARCHITECTURE.md#vision-inference-layer for context.
"""


def get_video_frames_generator(*args, **kwargs):
    raise NotImplementedError(
        "supervision stub: video frame streaming is not used by Safety Sentinel's Roboflow integration"
    )


def list_files_with_extensions(*args, **kwargs):
    raise NotImplementedError(
        "supervision stub: directory loading is not used by Safety Sentinel's Roboflow integration"
    )
