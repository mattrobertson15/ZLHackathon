"use client";

import { useEffect, useState } from "react";
import { generateSummary, listSummaries } from "@/lib/api";
import { SafetySummary } from "@/lib/types";
import { buildSummaryReport, downloadMarkdownReport } from "@/lib/report";
import SummaryCard from "@/components/SummaryCard";

type PeriodType = "daily" | "weekly" | "monthly";

export default function SummariesPage() {
  const [summaries, setSummaries] = useState<SafetySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSummary, setSelectedSummary] = useState<SafetySummary | null>(null);

  const [period, setPeriod] = useState<PeriodType>("weekly");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const fetchSummaries = async () => {
    try {
      setLoading(true);
      const data = await listSummaries({ limit: 50 });
      setSummaries(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load summaries");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummaries();
  }, []);

  const setQuickDate = (days: number, periodType: PeriodType) => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);

    setPeriod(periodType);
    setStartDate(start.toISOString().split("T")[0]);
    setEndDate(end.toISOString().split("T")[0]);
  };

  const handleGenerate = async () => {
    if (!startDate || !endDate) {
      setError("Please select both start and end dates");
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      const newSummary = await generateSummary(period, startDate, endDate);
      setSummaries((prev) => [newSummary, ...prev]);
      setSelectedSummary(newSummary);
      setStartDate("");
      setEndDate("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate summary");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadSummary = (summary: SafetySummary) => {
    const report = buildSummaryReport(summary);
    downloadMarkdownReport(report.markdown, report.fileName);
  };

  return (
    <>
      <div className="max-w-7xl mx-auto p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Safety Summaries</h1>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6 sticky top-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Generate Summary</h2>

              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Period
                  </label>
                  <select
                    value={period}
                    onChange={(e) => setPeriod(e.target.value as PeriodType)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                </div>
              </div>

              <div className="space-y-2 mb-6 border-t pt-4">
                <p className="text-xs font-semibold text-gray-600 uppercase">Quick Select</p>
                <button
                  onClick={() => setQuickDate(7, "weekly")}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 rounded transition-colors"
                >
                  This Week (7 days)
                </button>
                <button
                  onClick={() => setQuickDate(30, "monthly")}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 rounded transition-colors"
                >
                  This Month (30 days)
                </button>
                <button
                  onClick={() => setQuickDate(1, "daily")}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 rounded transition-colors"
                >
                  Today
                </button>
              </div>

              <button
                onClick={handleGenerate}
                disabled={generating || !startDate || !endDate}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {generating ? "Generating..." : "Generate Summary"}
              </button>
            </div>
          </div>

          <div className="lg:col-span-2">
            {loading ? (
              <div className="bg-white rounded-lg shadow p-8 text-center text-gray-600">
                Loading summaries...
              </div>
            ) : summaries.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-8 text-center text-gray-600">
                No summaries yet. Generate your first summary to get started!
              </div>
            ) : (
              <div className="space-y-4">
                {summaries.map((summary) => (
                  <SummaryCard
                    key={summary.id}
                    summary={summary}
                    onSelect={setSelectedSummary}
                    onDownload={handleDownloadSummary}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {selectedSummary && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-gray-50 border-b px-6 py-4 flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">
                {selectedSummary.period.charAt(0).toUpperCase() + selectedSummary.period.slice(1)}{" "}
                Summary
              </h2>
              <button
                onClick={() => setSelectedSummary(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
              >
                ×
              </button>
            </div>

            <div className="p-6 space-y-6">
              <div className="border-b pb-4">
                <p className="text-sm text-gray-600">
                  {new Date(selectedSummary.startDate).toLocaleDateString()} -{" "}
                  {new Date(selectedSummary.endDate).toLocaleDateString()}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-2 uppercase tracking-wide">
                  Executive Summary
                </h3>
                <p className="text-gray-700 whitespace-pre-wrap">
                  {selectedSummary.executiveSummary}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-2 uppercase tracking-wide">
                  Top Violations
                </h3>
                <p className="text-gray-700 whitespace-pre-wrap">
                  {selectedSummary.topViolations}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-2 uppercase tracking-wide">
                  Trend Analysis
                </h3>
                <p className="text-gray-700 whitespace-pre-wrap">
                  {selectedSummary.trendAnalysis}
                </p>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-2 uppercase tracking-wide">
                  Recommended Actions
                </h3>
                <p className="text-gray-700 whitespace-pre-wrap">
                  {selectedSummary.recommendedActions}
                </p>
              </div>

              <div className="border-t pt-4">
                <p className="text-xs text-gray-500">
                  Generated on {new Date(selectedSummary.createdAt).toLocaleString()}
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  onClick={() => handleDownloadSummary(selectedSummary)}
                  className="w-full px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors font-medium"
                >
                  Download Report
                </button>
                <button
                  onClick={() => setSelectedSummary(null)}
                  className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
