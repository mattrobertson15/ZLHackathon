"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getAnalyticsOverview, getAnalyticsTrends } from "@/lib/api";
import { AnalyticsOverview, AnalyticsTrends } from "@/lib/types";

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
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-600">Compliance Rate</h3>
              <p className="text-3xl font-bold text-green-600 mt-2">
                {overview?.compliancePercentage || 0}%
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-600">Total Observations</h3>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {overview?.totalObservations || 0}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-600">Safety Violations</h3>
              <p className="text-3xl font-bold text-red-600 mt-2">
                {overview?.totalViolations || 0}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-600">Pending Reviews</h3>
              <p className="text-3xl font-bold text-yellow-600 mt-2">
                {overview?.openEvents || 0}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Violation Breakdown
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Missing Helmet</span>
                  <span className="font-semibold text-gray-900">
                    {overview?.violationBreakdown.no_helmet || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Missing Vest</span>
                  <span className="font-semibold text-gray-900">
                    {overview?.violationBreakdown.no_vest || 0}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Severity Breakdown
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">High</span>
                  <span className="font-semibold text-red-600">
                    {overview?.severityBreakdown.high || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Medium</span>
                  <span className="font-semibold text-yellow-600">
                    {overview?.severityBreakdown.medium || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Low</span>
                  <span className="font-semibold text-green-600">
                    {overview?.severityBreakdown.low || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {trends && trends.points.length > 0 && (
            <div className="mt-6 bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Compliance Trends (Daily)
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b">
                    <tr>
                      <th className="text-left py-2 px-4 font-semibold text-gray-600">
                        Date
                      </th>
                      <th className="text-right py-2 px-4 font-semibold text-gray-600">
                        Compliance %
                      </th>
                      <th className="text-right py-2 px-4 font-semibold text-gray-600">
                        Violations
                      </th>
                      <th className="text-right py-2 px-4 font-semibold text-gray-600">
                        No Helmet
                      </th>
                      <th className="text-right py-2 px-4 font-semibold text-gray-600">
                        No Vest
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {trends.points.map((point) => (
                      <tr key={point.date} className="border-b hover:bg-gray-50">
                        <td className="py-2 px-4 text-gray-900">{point.date}</td>
                        <td className="text-right py-2 px-4 text-gray-900">
                          {point.compliancePercentage}%
                        </td>
                        <td className="text-right py-2 px-4 text-gray-900">
                          {point.totalViolations}
                        </td>
                        <td className="text-right py-2 px-4 text-gray-900">
                          {point.noHelmet}
                        </td>
                        <td className="text-right py-2 px-4 text-gray-900">
                          {point.noVest}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
