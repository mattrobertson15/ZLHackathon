"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getUpload, getDetections } from "@/lib/api";
import { Upload, Detection } from "@/lib/types";

export default function ResultsPage({ params }: { params: Promise<{ uploadId: string }> }) {
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [upload, setUpload] = useState<Upload | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
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
        const [uploadData, detectionsData] = await Promise.all([
          getUpload(uploadId),
          getDetections(uploadId),
        ]);
        setUpload(uploadData);
        setDetections(detectionsData);
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
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-gray-600">Loading results...</div>
      </div>
    );
  }

  if (error || !upload) {
    return (
      <div className="min-h-screen bg-gray-100">
        <nav className="bg-white shadow">
          <div className="max-w-6xl mx-auto px-8 py-4">
            <Link href="/app/dashboard" className="text-2xl font-bold text-gray-900">
              Safety Sentinel
            </Link>
          </div>
        </nav>
        <div className="max-w-6xl mx-auto p-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error || "Upload not found"}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="max-w-6xl mx-auto px-8 py-4 flex justify-between items-center">
          <Link href="/app/dashboard" className="text-2xl font-bold text-gray-900">
            Safety Sentinel
          </Link>
          <Link href="/app/dashboard" className="text-gray-600 hover:text-gray-900">
            Back to Dashboard
          </Link>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Analysis Results</h1>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Info</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">File Name</p>
              <p className="font-medium text-gray-900">{upload.fileName}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Type</p>
              <p className="font-medium text-gray-900 capitalize">{upload.fileType}</p>
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
            <div className="mt-6">
              <img
                src={`http://localhost:8000${upload.fileUrl}`}
                alt={upload.fileName}
                className="max-w-full h-auto rounded-lg border border-gray-200"
              />
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Detections ({detections.length})
          </h2>

          {detections.length === 0 ? (
            <p className="text-gray-600">No detections found in this upload.</p>
          ) : (
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
                        X: {detection.boundingBox.x}, Y: {detection.boundingBox.y}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-600">Dimensions:</span>
                      <p className="text-gray-900">
                        {detection.boundingBox.width} × {detection.boundingBox.height}
                      </p>
                    </div>
                  </div>

                  {detection.frameTimestamp && (
                    <p className="text-sm text-gray-600 mt-2">
                      Frame: {detection.frameTimestamp}s
                    </p>
                  )}
                </div>
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
        </div>
      </div>
    </div>
  );
}
