"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  listCameras,
  createCamera,
  startCamera,
  stopCamera,
  captureCamera,
  deleteCamera,
  cameraSnapshotUrl,
} from "@/lib/api";
import { Camera, CameraStatus } from "@/lib/types";

const STATUS_STYLES: Record<CameraStatus, string> = {
  live: "bg-green-100 text-green-800 border-green-200",
  offline: "bg-gray-100 text-gray-700 border-gray-200",
  error: "bg-red-100 text-red-800 border-red-200",
};

function StatusBadge({ status }: { status: CameraStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${STATUS_STYLES[status]}`}
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
  tick,
  onChanged,
}: {
  camera: Camera;
  tick: number;
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [snapshotFailed, setSnapshotFailed] = useState(false);

  const run = async (fn: () => Promise<unknown>) => {
    try {
      setBusy(true);
      await fn();
      onChanged();
    } catch {
      // surface errors via the refreshed camera status (lastError)
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  const hasSnapshot = camera.lastCaptureAt && !snapshotFailed;

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden flex flex-col">
      <div className="relative aspect-video bg-gray-900 flex items-center justify-center">
        {hasSnapshot ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={cameraSnapshotUrl(camera.id, tick)}
            alt={`${camera.label} snapshot`}
            className="h-full w-full object-cover"
            onError={() => setSnapshotFailed(true)}
          />
        ) : (
          <div className="text-gray-400 text-sm text-center px-4">
            {camera.status === "error"
              ? "No signal"
              : "Waiting for first capture…"}
          </div>
        )}
        <div className="absolute top-2 left-2">
          <StatusBadge status={camera.status} />
        </div>
        {camera.monitoring && (
          <div className="absolute top-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
            ● REC · every {camera.captureIntervalSeconds}s
          </div>
        )}
      </div>

      <div className="p-4 flex flex-col gap-3 flex-1">
        <div>
          <h3 className="font-semibold text-gray-900">{camera.label}</h3>
          <p className="text-xs text-gray-500">
            {camera.locationLabel || "No location"} ·{" "}
            <span className="font-mono break-all">{camera.rtspUrl}</span>
          </p>
        </div>

        <div className="text-sm text-gray-600 flex flex-wrap gap-x-4 gap-y-1">
          <span>
            Events:{" "}
            <span className="font-semibold text-gray-900">
              {camera.recentEventCount}
            </span>
          </span>
          <span>
            Last capture:{" "}
            {camera.lastCaptureAt
              ? new Date(camera.lastCaptureAt).toLocaleTimeString()
              : "—"}
          </span>
        </div>

        {camera.lastError && (
          <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded p-2 break-words">
            {camera.lastError}
          </p>
        )}

        <div className="mt-auto flex flex-wrap gap-2">
          {camera.monitoring ? (
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
          )}
          <button
            disabled={busy}
            onClick={() => run(() => captureCamera(camera.id))}
            className="px-3 py-1.5 text-sm font-semibold rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Capture now
          </button>
          <button
            disabled={busy}
            onClick={() => {
              if (confirm(`Remove camera "${camera.label}"?`)) {
                run(() => deleteCamera(camera.id));
              }
            }}
            className="px-3 py-1.5 text-sm font-semibold rounded-lg text-red-600 hover:bg-red-50 disabled:opacity-50 ml-auto"
          >
            Remove
          </button>
        </div>
        <Link
          href="/app/events"
          className="text-xs text-blue-600 hover:underline"
        >
          View events on the Events page →
        </Link>
      </div>
    </div>
  );
}

export default function CamerasPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  const [label, setLabel] = useState("");
  const [rtspUrl, setRtspUrl] = useState("rtsp://localhost:8554/worksite-demo");
  const [locationLabel, setLocationLabel] = useState("");
  const [interval, setIntervalSeconds] = useState(15);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    if (!label.trim() || !rtspUrl.trim()) {
      setError("Label and RTSP URL are required.");
      return;
    }
    try {
      setSubmitting(true);
      setError(null);
      await createCamera({
        label: label.trim(),
        rtspUrl: rtspUrl.trim(),
        locationLabel: locationLabel.trim() || undefined,
        captureIntervalSeconds: interval,
      });
      setLabel("");
      setLocationLabel("");
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
          automatically.
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
              Camera label
            </label>
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="e.g., Loading Dock Camera"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location label (optional)
            </label>
            <input
              type="text"
              value={locationLabel}
              onChange={(e) => setLocationLabel(e.target.value)}
              placeholder="e.g., Loading Dock"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              RTSP URL
            </label>
            <input
              type="text"
              value={rtspUrl}
              onChange={(e) => setRtspUrl(e.target.value)}
              placeholder="rtsp://host:8554/stream"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">
              For the demo emulator use{" "}
              <code className="font-mono">
                rtsp://localhost:8554/worksite-demo
              </code>{" "}
              (or <code className="font-mono">rtsp://mediamtx:8554/...</code>{" "}
              inside docker-compose).
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Capture interval (seconds)
            </label>
            <input
              type="number"
              min={5}
              value={interval}
              onChange={(e) => setIntervalSeconds(Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
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
