"use client";

import { Detection } from "@/lib/types";

interface DetectionViewerProps {
  detections: Detection[];
  uploadId: string;
}

export default function DetectionViewer({
  detections,
  uploadId,
}: DetectionViewerProps) {
  if (detections.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Detections (0)
        </h2>
        <p className="text-gray-600">No detections found in this upload.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Detections ({detections.length})
      </h2>
      <div className="space-y-3">
        {detections.map((detection) => (
          <div
            key={detection.id}
            className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex justify-between items-start mb-2">
              <div>
                <p className="font-semibold text-gray-900 capitalize">
                  {detection.label.replace(/_/g, " ")}
                </p>
                <p className="text-sm text-gray-600">
                  Confidence: {(detection.confidence * 100).toFixed(1)}%
                </p>
              </div>
              <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                {detection.source}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-600">Bounding Box:</span>
                <p className="text-gray-900">
                  X: {detection.boundingBox.x.toFixed(1)}, Y:{" "}
                  {detection.boundingBox.y.toFixed(1)}
                </p>
              </div>
              <div>
                <span className="text-gray-600">Dimensions:</span>
                <p className="text-gray-900">
                  {detection.boundingBox.width.toFixed(1)} ×{" "}
                  {detection.boundingBox.height.toFixed(1)}
                </p>
              </div>
            </div>
            {detection.frameTimestamp && (
              <p className="text-sm text-gray-600 mt-2">
                Frame: {detection.frameTimestamp.toFixed(2)}s
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
