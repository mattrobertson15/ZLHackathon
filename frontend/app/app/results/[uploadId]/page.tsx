"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getUploadResults, resolveMediaUrl } from "@/lib/api";
import { Upload, Detection, SafetyEvent, AlertRecord } from "@/lib/types";
import BoundingBoxOverlay from "@/components/BoundingBoxOverlay";
import StatCard from "@/components/StatCard";
import EventTable from "@/components/EventTable";
import AlertCard from "@/components/AlertCard";

function groupByFrame(detections: Detection[]): Array<{
  frameTimestamp: number | null;
  frameUrl: string | null;
  detections: Detection[];
}> {
  const groups = new Map<number | null, { frameUrl: string | null; detections: Detection[] }>();
  for (const detection of detections) {
    const key = detection.frameTimestamp;
    if (!groups.has(key)) {
      groups.set(key, { frameUrl: detection.frameUrl, detections: [] });
    }
    groups.get(key)!.detections.push(detection);
  }
  return Array.from(groups.entries())
    .sort((a, b) => (a[0] ?? 0) - (b[0] ?? 0))
    .map(([frameTimestamp, value]) => ({ frameTimestamp, ...value }));
}

export default function ResultsPage({ params }: { params: Promise<{ uploadId: string }> }) {
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [upload, setUpload] = useState<Upload | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [events, setEvents] = useState<SafetyEvent[]>([]);
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadParams() {
      const resolvedParams = await params;
      setUploadId(resolvedParams.uploadId);
    }
    loadParams();
  }, [params]);

  useEffect(() => {
    if (!uploadId) return;

    async function fetchData() {
      try {
        const results = await getUploadResults(uploadId!);
        setUpload(results.upload);
        setDetections(results.detections);
        setEvents(results.events);
        setAlerts(results.alerts);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load results");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [uploadId]);

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] flex items-center justify-center">
        <div className="text-gray-600">Loading results...</div>
      </div>
    );
  }

  if (error || !upload) {
    return (
      <div className="max-w-6xl mx-auto p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error || "Upload not found"}
        </div>
      </div>
    );
  }

  const frameGroups = upload.fileType === "video" ? groupByFrame(detections) : [];
  const violationEvents = events.filter((event) => event.eventType === "ppe_violation");

  return (
    <div className="max-w-6xl mx-auto p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Analysis Results</h1>
      <p className="text-gray-600 mb-6">
        From raw upload to operational intelligence: {upload.fileName}
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Detections" value={detections.length} />
        <StatCard label="Safety Events" value={events.length} />
        <StatCard
          label="Violations"
          value={violationEvents.length}
          color={violationEvents.length > 0 ? "red" : "green"}
        />
        <StatCard label="Alerts Created" value={alerts.length} color={alerts.length > 0 ? "yellow" : "gray"} />
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Info</h2>
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <p className="text-sm text-gray-600">File Name</p>
            <p className="font-medium text-gray-900">{upload.fileName}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Type</p>
            <p className="font-medium text-gray-900 capitalize">{upload.fileType}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Zone</p>
            <p className="font-medium text-gray-900">
              {upload.zoneDisplayName || upload.locationLabel || "No specific zone"}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Status</p>
            <p className="font-medium text-gray-900 capitalize">{upload.status}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Uploaded</p>
            <p className="font-medium text-gray-900">
              {new Date(upload.uploadedAt).toLocaleString()}
            </p>
          </div>
        </div>

        {upload.fileType === "image" && (
          <BoundingBoxOverlay
            src={resolveMediaUrl(upload.fileUrl)}
            alt={upload.fileName}
            detections={detections}
          />
        )}

        {upload.fileType === "video" && (
          <div>
            <video
              controls
              src={resolveMediaUrl(upload.fileUrl)}
              className="max-w-full h-auto rounded-lg border border-gray-200 mb-4"
            />
            {frameGroups.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Sampled Frames ({frameGroups.length})
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {frameGroups.map((group) => (
                    <div key={group.frameTimestamp ?? "unknown"}>
                      {group.frameUrl ? (
                        <BoundingBoxOverlay
                          src={resolveMediaUrl(group.frameUrl)}
                          alt={`Frame at ${group.frameTimestamp?.toFixed(2)}s`}
                          detections={group.detections}
                        />
                      ) : null}
                      <p className="text-sm text-gray-600 mt-1">
                        Frame: {group.frameTimestamp?.toFixed(2)}s
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Safety Events ({events.length})
        </h2>
        {events.length === 0 ? (
          <p className="text-gray-600">No safety events were generated from this upload.</p>
        ) : (
          <EventTable events={events} onEventSelect={() => {}} />
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Alerts Created ({alerts.length})
        </h2>
        {alerts.length === 0 ? (
          <p className="text-gray-600">
            No alerts were triggered — nothing required follow-up.
          </p>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <AlertCard key={alert.id} alert={alert} onSelect={() => {}} />
            ))}
          </div>
        )}
      </div>

      <div className="mt-6 flex gap-4">
        <Link
          href="/app/dashboard"
          className="flex-1 bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-blue-700 text-center transition-colors"
        >
          Back to Dashboard
        </Link>
        <Link
          href="/app/events"
          className="flex-1 bg-gray-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-gray-700 text-center transition-colors"
        >
          View Events
        </Link>
        <Link
          href="/app/alerts"
          className="flex-1 bg-gray-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-gray-700 text-center transition-colors"
        >
          View Alerts
        </Link>
      </div>
    </div>
  );
}
