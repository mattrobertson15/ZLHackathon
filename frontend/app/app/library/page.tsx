"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listUploads, resolveMediaUrl } from "@/lib/api";
import { Upload } from "@/lib/types";

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    processed: "bg-green-100 text-green-800",
    processing: "bg-yellow-100 text-yellow-800",
    uploaded: "bg-blue-100 text-blue-800",
    failed: "bg-red-100 text-red-800",
  };
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colors[status] ?? "bg-gray-100 text-gray-700"}`}>
      {status}
    </span>
  );
}

export default function LibraryPage() {
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listUploads()
      .then(setUploads)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load uploads"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] flex items-center justify-center">
        <div className="text-gray-600">Loading library...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 max-w-6xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Library</h1>
          <Link
            href="/app/upload"
            className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
          >
            Upload New
          </Link>
        </div>

        {uploads.length === 0 ? (
          <div className="text-center py-24 text-gray-500">
            <p className="text-lg mb-4">No uploads yet.</p>
            <Link href="/app/upload" className="text-blue-600 hover:underline">
              Upload your first image or video
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {uploads.map((upload) => (
              <Link
                key={upload.id}
                href={`/app/results/${upload.id}`}
                className="bg-white rounded-lg shadow hover:shadow-md transition-shadow overflow-hidden group"
              >
                <div className="aspect-video bg-gray-100 flex items-center justify-center overflow-hidden">
                  {upload.fileType === "image" ? (
                    <img
                      src={resolveMediaUrl(upload.fileUrl)}
                      alt={upload.fileName}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                    />
                  ) : (
                    <div className="flex flex-col items-center gap-2 text-gray-400">
                      <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                          d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
                      </svg>
                      <span className="text-xs">Video</span>
                    </div>
                  )}
                </div>
                <div className="p-4">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <p className="text-sm font-medium text-gray-900 truncate">{upload.fileName}</p>
                    <StatusBadge status={upload.status} />
                  </div>
                  {upload.locationLabel && (
                    <p className="text-xs text-gray-500 mb-1">{upload.locationLabel}</p>
                  )}
                  <p className="text-xs text-gray-400">
                    {new Date(upload.uploadedAt).toLocaleString()}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
