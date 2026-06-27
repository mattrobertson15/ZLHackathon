"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listAlerts, updateAlert } from "@/lib/api";
import { AlertRecord, AlertStatus } from "@/lib/types";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [alertTypeFilter, setAlertTypeFilter] = useState<string>("");

  const fetchAlerts = async (status?: string, alertType?: string) => {
    try {
      setLoading(true);
      const data = await listAlerts({
        status: status || undefined,
        alertType: alertType || undefined,
        limit: 100,
      });
      setAlerts(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load alerts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts(statusFilter, alertTypeFilter);
  }, [statusFilter, alertTypeFilter]);

  const handleStatusUpdate = async (alertId: string, newStatus: AlertStatus) => {
    try {
      await updateAlert(alertId, newStatus);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: newStatus } : a))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update alert");
    }
  };

  const getAlertTypeColor = (alertType: string) => {
    switch (alertType) {
      case "supervisor_review":
        return "bg-red-100 text-red-800";
      case "coaching_reminder":
        return "bg-yellow-100 text-yellow-800";
      case "manual_review":
        return "bg-purple-100 text-purple-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "draft":
        return "bg-gray-100 text-gray-800";
      case "queued":
        return "bg-blue-100 text-blue-800";
      case "sent_mock":
        return "bg-green-100 text-green-800";
      case "dismissed":
        return "bg-gray-200 text-gray-700";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-8 py-4 flex justify-between items-center">
          <Link href="/app/dashboard" className="text-2xl font-bold text-gray-900">
            Safety Sentinel
          </Link>
          <div className="flex gap-4">
            <Link href="/app/dashboard" className="text-gray-600 hover:text-gray-900">
              Dashboard
            </Link>
            <Link href="/app/events" className="text-gray-600 hover:text-gray-900">
              Events
            </Link>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Safety Alerts</h1>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="queued">Queued</option>
              <option value="sent_mock">Sent (Mock)</option>
              <option value="dismissed">Dismissed</option>
            </select>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Alert Type
            </label>
            <select
              value={alertTypeFilter}
              onChange={(e) => setAlertTypeFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              <option value="supervisor_review">Supervisor Review</option>
              <option value="coaching_reminder">Coaching Reminder</option>
              <option value="manual_review">Manual Review</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="bg-white rounded-lg shadow p-8 text-center text-gray-600">
            Loading alerts...
          </div>
        ) : alerts.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center text-gray-600">
            No alerts found
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div key={alert.id} className="bg-white rounded-lg shadow p-4">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{alert.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                  </div>
                  <div className="flex gap-2">
                    <span
                      className={`inline-block px-3 py-1 text-sm font-medium rounded-full whitespace-nowrap ${getAlertTypeColor(
                        alert.alertType
                      )}`}
                    >
                      {alert.alertType.replace(/_/g, " ")}
                    </span>
                    <span
                      className={`inline-block px-3 py-1 text-sm font-medium rounded-full whitespace-nowrap ${getStatusColor(
                        alert.status
                      )}`}
                    >
                      {alert.status}
                    </span>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <p className="text-xs text-gray-500">
                    {new Date(alert.createdAt).toLocaleString()} • ID: {alert.id}
                  </p>

                  {alert.status === "draft" && (
                    <button
                      onClick={() => handleStatusUpdate(alert.id, "sent_mock")}
                      className="px-3 py-1 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Mark as Sent
                    </button>
                  )}

                  {alert.status !== "dismissed" && alert.status !== "sent_mock" && (
                    <button
                      onClick={() => handleStatusUpdate(alert.id, "dismissed")}
                      className="px-3 py-1 text-sm font-medium border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Dismiss
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
