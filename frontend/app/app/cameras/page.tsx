"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  listCameras,
  listZones,
  createCamera,
  startCamera,
  stopCamera,
  captureCamera,
  deleteCamera,
  cameraSnapshotUrl,
  testStream,
  type TestStreamResult,
} from "@/lib/api";
import { Camera, CameraStreamStatus, Zone } from "@/lib/types";

const STREAM_STYLES: Record<CameraStreamStatus, string> = {
  live: "bg-green-100 text-green-800 border-green-200",
  offline: "bg-gray-100 text-gray-700 border-gray-200",
  error: "bg-red-100 text-red-800 border-red-200",
};

function StreamBadge({ status }: { status: CameraStreamStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${STREAM_STYLES[status]}`}
    >
      <span
        className={`h-2 w-2 rounded-full ${
          status === "live"
            ? "bg-green-500 animate-pulse"
            : status === "error"
            ? "bg-red-500"
            : "bg-gray-400"
        }`}
      />
      {status === "live" ? "Live" : status === "error" ? "Error" : "Offline"}
    </span>
  );
}

function CameraCard({
  camera,
  zoneName,
  tick,
  onChanged,
}: {
  camera: Camera;
  zoneName?: string;
  tick: number;
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [snapshotFailed, setSnapshotFailed] = useState(false);

  // Reset the error flag whenever a new capture lands so the img retries.
  const prevCaptureAt = useRef(camera.lastCaptureAt);
  useEffect(() => {
    if (camera.lastCaptureAt !== prevCaptureAt.current) {
      prevCaptureAt.current = camera.lastCaptureAt;
      setSnapshotFailed(false);
    }
  }, [camera.lastCaptureAt]);

  const run = async (fn: () => Promise<unknown>) => {
    try {
      setBusy(true);
      await fn();
    } finally {
      setBusy(false);
      onChanged();
    }
  };

  const isFeed = Boolean(camera.rtspUrl);
  const hasSnapshot = camera.lastCaptureAt && !snapshotFailed;

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden flex flex-col">
      <div className="relative aspect-video bg-gray-900 flex items-center justify-center">
        {hasSnapshot ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={cameraSnapshotUrl(camera.id, tick)}
            alt={`${camera.displayName} snapshot`}
            className="h-full w-full object-cover"
            onError={() => setSnapshotFailed(true)}
          />
        ) : (
          <div className="text-gray-400 text-sm text-center px-4">
            {!isFeed
              ? "Location-only camera (no RTSP feed)"
              : camera.streamStatus === "error"
              ? "No signal"
              : "Waiting for first capture…"}
          </div>
        )}
        {isFeed && (
          <div className="absolute top-2 left-2">
            <StreamBadge status={camera.streamStatus} />
          </div>
        )}
        {camera.monitoring && (
          <div className="absolute top-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
            ● REC · every {camera.captureIntervalSeconds}s
          </div>
        )}
      </div>

      <div className="p-4 flex flex-col gap-3 flex-1">
        <div>
          <h3 className="font-semibold text-gray-900">{camera.displayName}</h3>
          <p className="text-xs text-gray-500">
            Zone: {zoneName || camera.zoneId || "unassigned"}
            {isFeed && (
              <>
                {" · "}
                <span className="font-mono break-all">{camera.rtspUrl}</span>
              </>
            )}
          </p>
        </div>

        <div className="text-sm text-gray-600 flex flex-wrap gap-x-4 gap-y-1">
          <span>
            Events:{" "}
            <span className="font-semibold text-gray-900">
              {camera.recentEventCount}
            </span>
          </span>
          {isFeed && (
            <span>
              Last capture:{" "}
              {camera.lastCaptureAt
                ? new Date(camera.lastCaptureAt).toLocaleTimeString()
                : "—"}
            </span>
          )}
        </div>

        {camera.lastError && (
          <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded p-2 break-words">
            {camera.lastError}
          </p>
        )}

        <div className="mt-auto flex flex-wrap gap-2">
          {isFeed ? (
            camera.monitoring ? (
              <button
                disabled={busy}
                onClick={() => run(() => stopCamera(camera.id))}
                className="px-3 py-1.5 text-sm font-semibold rounded-lg bg-gray-200 text-gray-800 hover:bg-gray-300 disabled:opacity-50"
              >
                Stop
              </button>
            ) : (
              <button
                disabled={busy}
                onClick={() => run(() => startCamera(camera.id))}
                className="px-3 py-1.5 text-sm font-semibold rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
              >
                {busy ? "Starting…" : "Start monitoring"}
              </button>
            )
          ) : (
            <span className="text-xs text-gray-400 self-center">
              Seeded location camera — no live feed
            </span>
          )}
          {isFeed && (
            <button
              disabled={busy}
              onClick={() => run(() => captureCamera(camera.id))}
              className="px-3 py-1.5 text-sm font-semibold rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Capture now
            </button>
          )}
          <button
            disabled={busy}
            onClick={() => {
              if (confirm(`Remove camera "${camera.displayName}"?`)) {
                run(() => deleteCamera(camera.id));
              }
            }}
            className="px-3 py-1.5 text-sm font-semibold rounded-lg text-red-600 hover:bg-red-50 disabled:opacity-50 ml-auto"
          >
            Remove
          </button>
        </div>
        <div className="flex gap-3">
          <Link href={`/app/cameras/${camera.id}`} className="text-xs text-indigo-600 hover:underline font-medium">
            View camera analytics →
          </Link>
          <Link href="/app/events" className="text-xs text-blue-600 hover:underline">
            All events →
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function CamerasPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  const [displayName, setDisplayName] = useState("");
  const [rtspUrl, setRtspUrl] = useState("rtsp://safety-sentinel-relay.internal:8554/phone-demo");
  const [zoneId, setZoneId] = useState("");
  const [interval, setIntervalSeconds] = useState(15);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // "Test Stream" probe state: Idle | Connecting | Connected | Failed.
  const [testState, setTestState] = useState<
    "idle" | "connecting" | "connected" | "failed"
  >("idle");
  const [testResult, setTestResult] = useState<TestStreamResult | null>(null);

  const handleTestStream = async () => {
    if (!rtspUrl.trim()) {
      setTestState("failed");
      setTestResult({ status: "failed", message: "Enter an RTSP URL first." });
      return;
    }
    setTestState("connecting");
    setTestResult(null);
    try {
      const result = await testStream(rtspUrl.trim());
      setTestResult(result);
      setTestState(result.status === "connected" ? "connected" : "failed");
    } catch (err) {
      setTestState("failed");
      setTestResult({
        status: "failed",
        message: err instanceof Error ? err.message : "Test request failed.",
      });
    }
  };

  const zoneName = useCallback(
    (id?: string | null) => zones.find((z) => z.id === id)?.displayName,
    [zones]
  );

  const refresh = useCallback(async () => {
    try {
      setCameras(await listCameras());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load cameras");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    listZones()
      .then(setZones)
      .catch(() => setZones([]));
    refresh();
    // Poll camera state + bump the snapshot cache-buster every 3s for a live feel.
    const id = setInterval(() => {
      setTick((t) => t + 1);
      refresh();
    }, 3000);
    return () => clearInterval(id);
  }, [refresh]);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!displayName.trim()) {
      setError("A display name is required.");
      return;
    }
    try {
      setSubmitting(true);
      setError(null);
      await createCamera({
        displayName: displayName.trim(),
        rtspUrl: rtspUrl.trim() || undefined,
        zoneId: zoneId || undefined,
        captureIntervalSeconds: interval,
      });
      setDisplayName("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to register camera");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-1">Cameras</h1>
        <p className="text-gray-600">
          Register an RTSP camera feed and Safety Sentinel will watch it
          continuously, capturing frames on an interval and raising PPE events
          automatically. Captures inherit the camera&apos;s zone, so live events
          get the same zone-aware rules as uploads.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Register a camera
        </h2>
        <form
          onSubmit={handleRegister}
          className="grid grid-cols-1 md:grid-cols-2 gap-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Display name
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="e.g., Loading Dock Camera"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Zone (optional)
            </label>
            <select
              value={zoneId}
              onChange={(e) => setZoneId(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">No zone</option>
              {zones.map((z) => (
                <option key={z.id} value={z.id}>
                  {z.displayName}
                </option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              RTSP URL (optional — leave blank for a location-only camera)
            </label>
            <input
              type="text"
              value={rtspUrl}
              onChange={(e) => setRtspUrl(e.target.value)}
              placeholder="rtsp://host:8554/stream"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg font-mono text-sm text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">
              For the phone relay use{" "}
              <code className="font-mono">
                rtsp://safety-sentinel-relay.internal:8554/phone-demo
              </code>{" "}
              (Streamlabs mobile: push to{" "}
              <code className="font-mono">rtmp://safety-sentinel-relay.fly.dev:1935/phone-demo</code>
              {" — "}Streamlabs OBS desktop: server{" "}
              <code className="font-mono">rtmp://safety-sentinel-relay.fly.dev:1935/live</code>
              {" "}+ stream key <code className="font-mono">phone-demo</code>, then use{" "}
              <code className="font-mono">…/live/phone-demo</code> as the RTSP URL).
            </p>
            <div className="mt-3 flex items-center gap-3">
              <button
                type="button"
                onClick={handleTestStream}
                disabled={testState === "connecting"}
                className="bg-gray-100 text-gray-800 text-sm font-semibold py-2 px-4 rounded-lg border border-gray-300 hover:bg-gray-200 disabled:opacity-60 transition-colors"
              >
                {testState === "connecting" ? "Connecting…" : "Test Stream"}
              </button>
              {testState !== "idle" && (
                <span
                  className={`inline-flex items-center gap-1.5 text-sm font-medium ${
                    testState === "connected"
                      ? "text-green-700"
                      : testState === "failed"
                        ? "text-red-700"
                        : "text-gray-600"
                  }`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${
                      testState === "connected"
                        ? "bg-green-500"
                        : testState === "failed"
                          ? "bg-red-500"
                          : "bg-gray-400 animate-pulse"
                    }`}
                  />
                  {testState === "connecting"
                    ? "Connecting"
                    : testResult?.status === "connected"
                      ? `Connected${
                          testResult.width && testResult.height
                            ? ` · ${testResult.width}×${testResult.height}`
                            : ""
                        }`
                      : "Failed"}
                </span>
              )}
            </div>
            {testResult && testState === "failed" && (
              <p className="text-xs text-red-600 mt-2">{testResult.message}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Capture interval (seconds)
            </label>
            <input
              type="number"
              min={1}
              value={interval}
              onChange={(e) => setIntervalSeconds(Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">
              Use 1–2s for a snappy live demo (e.g. a walk-by); larger values
              reduce inference load for always-on monitoring.
            </p>
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={submitting}
              className="w-full md:w-auto bg-blue-600 text-white font-semibold py-2 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
            >
              {submitting ? "Registering…" : "Register camera"}
            </button>
          </div>
        </form>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Registered cameras
        </h2>
        {loading ? (
          <p className="text-gray-500">Loading cameras…</p>
        ) : cameras.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
            No cameras registered yet. Add one above to start live monitoring.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {cameras.map((camera) => (
              <CameraCard
                key={camera.id}
                camera={camera}
                zoneName={zoneName(camera.zoneId)}
                tick={tick}
                onChanged={refresh}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
