"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { uploadFile, analyzeUpload, listZones } from "@/lib/api";
import type { Zone } from "@/lib/types";
import UploadDropzone from "@/components/UploadDropzone";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [zones, setZones] = useState<Zone[]>([]);
  const [zoneId, setZoneId] = useState("");
  const [notes, setNotes] = useState("");
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadId, setUploadId] = useState<string | null>(null);

  useEffect(() => {
    listZones()
      .then(setZones)
      .catch(() => setZones([]));
  }, []);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file");
      return;
    }

    try {
      setUploading(true);
      setError(null);
      const upload = await uploadFile(file, undefined, notes, zoneId || undefined);
      setUploadId(upload.id);
      setFile(null);
      setZoneId("");
      setNotes("");

      setAnalyzing(true);
      await analyzeUpload(upload.id, true, true);

      router.push(`/app/results/${upload.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setAnalyzing(false);
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <div className="max-w-2xl mx-auto p-8">
        <div className="bg-white rounded-lg shadow p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Media</h1>
          <p className="text-gray-600 mb-6">
            Upload an image or video for safety analysis
          </p>

          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleUpload} className="space-y-6">
            <UploadDropzone onFileSelect={handleFileSelect} selectedFile={file} />

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Zone (optional)
                </label>
                <select
                  value={zoneId}
                  onChange={(e) => setZoneId(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">No specific zone</option>
                  {zones.map((zone) => (
                    <option key={zone.id} value={zone.id}>
                      {zone.displayName}
                      {zone.requiredPpe.length > 0
                        ? ` — requires ${zone.requiredPpe.join(", ")}`
                        : " — no PPE required"}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  The zone determines which PPE rules apply to this upload.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes (optional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Any additional context about this upload..."
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex gap-4">
              <button
                type="submit"
                disabled={!file || uploading || analyzing}
                className="flex-1 bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {analyzing
                  ? "Analyzing..."
                  : uploading
                  ? "Uploading..."
                  : "Upload & Analyze"}
              </button>
              <Link
                href="/app/dashboard"
                className="px-4 py-2 border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </Link>
            </div>
          </form>

          <div className="mt-8 pt-6 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              Supported Formats
            </h3>
            <ul className="text-sm text-gray-600 space-y-2">
              <li>• Images: JPG, PNG, WebP</li>
              <li>• Videos: MP4, MOV (up to 30 seconds recommended)</li>
              <li>
                • File size: Up to 100MB
              </li>
            </ul>
          </div>

          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-blue-900">
                Need a reliable walkthrough?
              </h3>
              <p className="text-sm text-blue-800 mt-1">
                Load the warehouse shift scenario and review the same workflow with seeded data.
              </p>
            </div>
            <Link
              href="/app/demo"
              className="shrink-0 px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 text-center transition-colors"
            >
              Open Demo
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}
