"use client";

import { useEffect, useState } from "react";
import { getAnalyticsOverview, getAnalyticsTrends, resetIncidents } from "@/lib/api";
import { AnalyticsOverview, AnalyticsTrends } from "@/lib/types";
import { buildDashboardReport, downloadMarkdownReport } from "@/lib/report";
import ComplianceScoreCard from "@/components/ComplianceScoreCard";
import StatCard from "@/components/StatCard";
import ViolationBreakdownCard from "@/components/ViolationBreakdownCard";
import SeverityBreakdownCard from "@/components/SeverityBreakdownCard";
import TrendTable from "@/components/TrendTable";

export default function Dashboard() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [trends, setTrends] = useState<AnalyticsTrends | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        const [overviewData, trendsData] = await Promise.all([
          getAnalyticsOverview("weekly"),
          getAnalyticsTrends("daily"),
        ]);
        setOverview(overviewData);
        setTrends(trendsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  async function handleReset() {
    if (!confirm("Are you sure you want to reset all incidents? This cannot be undone.")) {
      return;
    }

    setResetting(true);
    try {
      await resetIncidents();
      const [overviewData, trendsData] = await Promise.all([
        getAnalyticsOverview("weekly"),
        getAnalyticsTrends("daily"),
      ]);
      setOverview(overviewData);
      setTrends(trendsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reset incidents");
    } finally {
      setResetting(false);
    }
  }

  function handleDownloadReport() {
    if (!overview) {
      return;
    }

    const report = buildDashboardReport(overview, trends);
    downloadMarkdownReport(report.markdown, report.fileName);
  }

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] p-8 flex items-center justify-center">
        <div className="text-gray-600">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
            <div className="flex flex-col gap-2 sm:flex-row">
              <button
                onClick={handleDownloadReport}
                disabled={!overview}
                className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                Download Report
              </button>
              <button
                onClick={handleReset}
                disabled={resetting}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {resetting ? "Resetting..." : "Reset Incidents"}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <ComplianceScoreCard percentage={overview?.compliancePercentage || 0} />
            <StatCard label="Total Observations" value={overview?.totalObservations || 0} />
            <StatCard label="Safety Violations" value={overview?.totalViolations || 0} color="red" />
            <StatCard label="Pending Reviews" value={overview?.openEvents || 0} color="yellow" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ViolationBreakdownCard
              title="Violation Breakdown"
              items={[
                { label: "Missing Helmet", value: overview?.violationBreakdown.no_helmet || 0 },
                { label: "Missing Vest", value: overview?.violationBreakdown.no_vest || 0 },
              ]}
            />
            <SeverityBreakdownCard
              items={[
                { label: "High", value: overview?.severityBreakdown.high || 0, color: "red" },
                { label: "Medium", value: overview?.severityBreakdown.medium || 0, color: "yellow" },
                { label: "Low", value: overview?.severityBreakdown.low || 0, color: "green" },
              ]}
            />
          </div>

          {trends && trends.points.length > 0 && (
            <div className="mt-6">
              <TrendTable points={trends.points} title="Compliance Trends (Daily)" />
            </div>
          )}
        </div>
      </div>
    </>
  );
}
