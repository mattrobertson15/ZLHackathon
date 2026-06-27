"use client";

import { useState } from "react";
import Link from "next/link";
import { loadDemoScenario } from "@/lib/api";
import type { DemoScenarioResponse } from "@/lib/types";

const scenarioSteps = [
  "Load curated worksite uploads",
  "Review generated PPE detections",
  "Open structured safety events",
  "Show mock alerts and dashboard movement",
  "Generate a supervisor-ready summary",
];

const demoLinks = [
  { href: "/app/dashboard", label: "Dashboard", tone: "bg-blue-600 hover:bg-blue-700 text-white" },
  { href: "/app/events", label: "Events", tone: "bg-white hover:bg-gray-50 text-gray-900 border border-gray-300" },
  { href: "/app/alerts", label: "Alerts", tone: "bg-white hover:bg-gray-50 text-gray-900 border border-gray-300" },
  { href: "/app/summaries", label: "Summaries", tone: "bg-white hover:bg-gray-50 text-gray-900 border border-gray-300" },
];

export default function DemoPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DemoScenarioResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleLoadScenario() {
    try {
      setLoading(true);
      setError(null);
      const data = await loadDemoScenario();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load demo scenario");
    } finally {
      setLoading(false);
    }
  }

  const primaryUpload = result?.uploads[0];

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="max-w-6xl mx-auto px-8 py-4 flex justify-between items-center">
          <Link href="/app/dashboard" className="text-2xl font-bold text-gray-900">
            Safety Sentinel
          </Link>
          <div className="flex gap-4">
            <Link href="/app/dashboard" className="text-gray-600 hover:text-gray-900">
              Dashboard
            </Link>
            <Link href="/app/upload" className="text-gray-600 hover:text-gray-900">
              Upload
            </Link>
            <Link href="/app/events" className="text-gray-600 hover:text-gray-900">
              Events
            </Link>
            <Link href="/app/alerts" className="text-gray-600 hover:text-gray-900">
              Alerts
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto p-8">
        <div className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-700 mb-2">
            Guided scenario
          </p>
          <h1 className="text-3xl font-bold text-gray-900 mb-3">
            Warehouse Shift Demo
          </h1>
          <p className="text-gray-600 max-w-3xl">
            Load a repeatable PPE review scenario that populates the real upload,
            detection, event, alert, and analytics tables for a clean product walkthrough.
          </p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <section className="lg:col-span-2 bg-white rounded-lg shadow p-6">
            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-3">
                  Load Scenario Data
                </h2>
                <p className="text-gray-600 mb-5">
                  Seeds three processed uploads with realistic PPE detections,
                  six safety events, and four mock alerts. Re-running replaces
                  this demo scenario without clearing other app data.
                </p>
                <button
                  onClick={handleLoadScenario}
                  disabled={loading}
                  className="px-5 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? "Loading Demo..." : "Load Demo Scenario"}
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 min-w-56">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {result?.counts.uploads ?? 3}
                  </div>
                  <div className="text-sm text-gray-600">Uploads</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {result?.counts.events ?? 6}
                  </div>
                  <div className="text-sm text-gray-600">Events</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {result?.counts.alerts ?? 4}
                  </div>
                  <div className="text-sm text-gray-600">Alerts</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {result?.counts.detections ?? 9}
                  </div>
                  <div className="text-sm text-gray-600">Detections</div>
                </div>
              </div>
            </div>
          </section>

          <section className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Demo Run Order
            </h2>
            <ol className="space-y-3">
              {scenarioSteps.map((step, index) => (
                <li key={step} className="flex gap-3 text-sm text-gray-700">
                  <span className="h-6 w-6 shrink-0 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-semibold">
                    {index + 1}
                  </span>
                  <span className="pt-0.5">{step}</span>
                </li>
              ))}
            </ol>
          </section>
        </div>

        {result && (
          <section className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-5">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  Scenario Loaded
                </h2>
                <p className="text-gray-600">{result.message}</p>
              </div>
              <div className="flex flex-wrap gap-3">
                {primaryUpload && (
                  <Link
                    href={`/app/results/${primaryUpload.id}`}
                    className="px-4 py-2 bg-gray-900 text-white font-semibold rounded-lg hover:bg-gray-800 transition-colors"
                  >
                    Open Results
                  </Link>
                )}
                {demoLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`px-4 py-2 font-semibold rounded-lg transition-colors ${link.tone}`}
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {result.uploads.map((upload) => (
                <Link
                  key={upload.id}
                  href={`/app/results/${upload.id}`}
                  className="block border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="text-sm text-gray-600 mb-1">
                    {upload.locationLabel || "Worksite"}
                  </div>
                  <div className="font-semibold text-gray-900 mb-2">
                    {upload.fileName}
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(upload.uploadedAt).toLocaleString()}
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}

        <section className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">
            Scenario Coverage
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-700">
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="font-semibold text-gray-900 mb-1">Detection</div>
              <p>Person, helmet, vest, missing helmet, and missing vest observations.</p>
            </div>
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="font-semibold text-gray-900 mb-1">Workflow</div>
              <p>Open violations, reviewed coaching items, and manual review routing.</p>
            </div>
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="font-semibold text-gray-900 mb-1">Reporting</div>
              <p>Dashboard metrics, trends, mock alerts, and summary generation.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
