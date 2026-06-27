"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getAnalyticsOverview, getAnalyticsTrends } from "@/lib/api";
import { AnalyticsOverview, AnalyticsTrends } from "@/lib/types";
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 p-8 flex items-center justify-center">
        <div className="text-gray-600">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="max-w-6xl mx-auto px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Safety Sentinel</h1>
          <div className="flex gap-4">
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

      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h2>

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
    </div>
  );
}
