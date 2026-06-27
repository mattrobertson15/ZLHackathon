"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getCamera, cameraSnapshotUrl } from "@/lib/api";
import { CameraDetail, SafetyEvent } from "@/lib/types";
import StatCard from "@/components/StatCard";
import EventTable from "@/components/EventTable";

function complianceFromEvents(events: SafetyEvent[]): number {
  if (events.length === 0) return 100;
  const violations = events.filter((e) => e.eventType === "ppe_violation").length;
  return Math.round(((events.length - violations) / events.length) * 100);
}

const VIOLATION_LABELS: Record<string, string> = {
  no_helmet: "No Hard Hat",
  no_vest: "No Safety Vest",
};

// A violation counts as "live" if it's still open and was seen very recently.
const LIVE_VIOLATION_WINDOW_MS = 60_000;

function liveViolation(
  events: SafetyEvent[],
  nowMs: number
): SafetyEvent | null {
  const latest = events[0]; // events arrive newest-first from the API
  if (
    latest &&
    latest.eventType === "ppe_violation" &&
    latest.status === "open" &&
    nowMs - new Date(latest.createdAt).getTime() <= LIVE_VIOLATION_WINDOW_MS
  ) {
    return latest;
  }
  return null;
}

// Poll cadence for the near-live preview + events on the detail page.
const POLL_INTERVAL_MS = 2000;

export default function CameraDetailPage({
  params,
}: {
  params: Promise<{ cameraId: string }>;
}) {
  const [cameraId, setCameraId] = useState<string | null>(null);
  const [detail, setDetail] = useState<CameraDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Bumped each poll to cache-bust the snapshot <img> for a near-live preview.
  const [tick, setTick] = useState(0);

  useEffect(() => {
    params.then((p) => setCameraId(p.cameraId));
  }, [params]);

  useEffect(() => {
    if (!cameraId) return;
    let active = true;
    const load = () =>
      getCamera(cameraId)
        .then((d) => {
          if (!active) return;
          setDetail(d);
          setError(null);
        })
        .catch((err) => {
          if (active)
            setError(err instanceof Error ? err.message : "Failed to load camera");
        })
        .finally(() => {
          if (active) setLoading(false);
        });

    load();
    // Poll so new captures, violations, and the snapshot appear "live".
    const id = setInterval(() => {
      setTick((t) => t + 1);
      load();
    }, POLL_INTERVAL_MS);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [cameraId]);

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] flex items-center justify-center">
        <div className="text-gray-600">Loading camera...</div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="max-w-5xl mx-auto p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error || "Camera not found"}
        </div>
      </div>
    );
  }

  const { camera, captures, events } = detail;
  const violations = events.filter((e) => e.eventType === "ppe_violation").length;
  const compliance = complianceFromEvents(events);
  const snapshotUrl = cameraSnapshotUrl(camera.id, tick);
  const live = liveViolation(events, Date.now());

  const streamStatusColors: Record<string, string> = {
    live: "bg-green-500",
    offline: "bg-gray-400",
    error: "bg-red-500",
  };

  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="flex items-center gap-3 mb-1">
        <Link
          href="/app/cameras"
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          ← Cameras
        </Link>
      </div>
      <h1 className="text-3xl font-bold text-gray-900 mb-1">{camera.displayName}</h1>
      <div className="flex items-center gap-3 mb-6 text-sm text-gray-500">
        <span className="flex items-center gap-1.5">
          <span
            className={`w-2.5 h-2.5 rounded-full ${streamStatusColors[camera.streamStatus]}`}
          />
          {camera.streamStatus.charAt(0).toUpperCase() + camera.streamStatus.slice(1)}
        </span>
        {camera.zoneId && <span>Zone: {camera.zoneId}</span>}
        {camera.rtspUrl && (
          <span className="font-mono text-xs truncate max-w-xs">{camera.rtspUrl}</span>
        )}
      </div>

      {/* Live violation banner — the demo money shot */}
      {live && (
        <div className="bg-red-600 text-white rounded-lg shadow-lg p-5 mb-6 flex items-center gap-4 animate-pulse">
          <span className="text-3xl" aria-hidden>
            ⚠️
          </span>
          <div className="flex-1">
            <div className="text-xs font-semibold uppercase tracking-wide opacity-90">
              Live Violation Detected
            </div>
            <div className="text-xl font-bold">
              {live.violationType
                ? VIOLATION_LABELS[live.violationType] ?? live.violationType
                : "PPE Violation"}
            </div>
            <div className="text-sm opacity-90">
              {camera.displayName} · {Math.round(live.confidence * 100)}% confidence ·{" "}
              {new Date(live.createdAt).toLocaleTimeString()}
            </div>
          </div>
          <div className="hidden sm:block text-right text-xs opacity-90">
            <div>Mock Slack alert sent</div>
            <div>Mock SMS alert sent</div>
            <div>Safety manager notified</div>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Compliance %" value={compliance} color={compliance >= 80 ? "green" : "red"} />
        <StatCard label="Total Captures" value={captures.length} />
        <StatCard label="Safety Events" value={events.length} />
        <StatCard label="Violations" value={violations} color={violations > 0 ? "red" : "green"} />
      </div>

      {/* Latest snapshot */}
      {camera.rtspUrl && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Latest Snapshot</h2>
          {camera.lastCaptureAt ? (
            <div>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={snapshotUrl}
                alt="Latest camera snapshot"
                className="rounded-lg border border-gray-200 max-h-80 object-contain"
                onError={(e) => {
                  (e.currentTarget as HTMLImageElement).style.display = "none";
                }}
              />
              <p className="text-xs text-gray-500 mt-2">
                Last captured: {new Date(camera.lastCaptureAt).toLocaleString()}
              </p>
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No snapshot yet — start monitoring to capture frames.</p>
          )}
        </div>
      )}

      {/* Capture history */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Capture History ({captures.length})
        </h2>
        {captures.length === 0 ? (
          <p className="text-gray-500 text-sm">No captures yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b">
                <tr>
                  <th className="text-left py-2 px-3 font-semibold text-gray-600">Captured</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-600">File</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-600">Status</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-600"></th>
                </tr>
              </thead>
              <tbody>
                {captures.slice(0, 20).map((capture) => (
                  <tr key={capture.id} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-3 text-gray-700">
                      {new Date(capture.uploadedAt).toLocaleString()}
                    </td>
                    <td className="py-2 px-3 text-gray-700 font-mono text-xs">
                      {capture.fileName}
                    </td>
                    <td className="py-2 px-3">
                      <span className={`capitalize text-xs font-medium px-2 py-0.5 rounded-full ${
                        capture.status === "processed"
                          ? "bg-green-100 text-green-800"
                          : capture.status === "failed"
                          ? "bg-red-100 text-red-800"
                          : "bg-gray-100 text-gray-700"
                      }`}>
                        {capture.status}
                      </span>
                    </td>
                    <td className="py-2 px-3">
                      <Link
                        href={`/app/results/${capture.id}`}
                        className="text-xs text-blue-600 hover:underline"
                      >
                        View →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {captures.length > 20 && (
              <p className="text-xs text-gray-500 mt-2 px-3">
                Showing 20 of {captures.length} captures.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Events */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Safety Events ({events.length})
        </h2>
        {events.length === 0 ? (
          <p className="text-gray-500 text-sm">No events from this camera yet.</p>
        ) : (
          <EventTable events={events} onEventSelect={() => {}} />
        )}
      </div>

      <div className="flex gap-4">
        <Link
          href="/app/cameras"
          className="flex-1 bg-gray-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-gray-700 text-center transition-colors"
        >
          Back to Cameras
        </Link>
        <Link
          href="/app/dashboard"
          className="flex-1 bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-blue-700 text-center transition-colors"
        >
          Dashboard
        </Link>
      </div>
    </div>
  );
}
