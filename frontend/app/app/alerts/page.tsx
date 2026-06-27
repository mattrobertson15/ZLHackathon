"use client";

import { useEffect, useState } from "react";
import { listAlerts, updateAlert } from "@/lib/api";
import { AlertRecord, AlertStatus } from "@/lib/types";
import AlertCard from "@/components/AlertCard";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [alertTypeFilter, setAlertTypeFilter] = useState<string>("");
  const [selectedAlert, setSelectedAlert] = useState<AlertRecord | null>(null);

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
      if (selectedAlert?.id === alertId) {
        setSelectedAlert({ ...selectedAlert, status: newStatus });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update alert");
    }
  };

  const getAlertTypeColor = (alertType: string) => {
    switch (alertType) {
      case "supervisor_review":
        return "bg-red-100 text-red-800 border-l-4 border-red-500";
      case "coaching_reminder":
        return "bg-yellow-100 text-yellow-800 border-l-4 border-yellow-500";
      case "manual_review":
        return "bg-purple-100 text-purple-800 border-l-4 border-purple-500";
      case "repeated_violation":
        return "bg-orange-100 text-orange-900 border-l-4 border-orange-500";
      default:
        return "bg-gray-100 text-gray-800 border-l-4 border-gray-500";
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

  const getAlertTypeLabel = (alertType: string) => {
    switch (alertType) {
      case "supervisor_review":
        return "Supervisor Review";
      case "coaching_reminder":
        return "Coaching Reminder";
      case "manual_review":
        return "Manual Review";
      case "repeated_violation":
        return "Repeated Violation";
      default:
        return alertType;
    }
  };

  const stats = {
    draft: alerts.filter((a) => a.status === "draft").length,
    queued: alerts.filter((a) => a.status === "queued").length,
    sent_mock: alerts.filter((a) => a.status === "sent_mock").length,
    total: alerts.length,
  };

  return (
    <>
      <div className="max-w-7xl mx-auto p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Safety Alerts</h1>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-gray-900">{stats.draft}</div>
            <div className="text-sm text-gray-600 mt-1">Draft Alerts</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-blue-600">{stats.queued}</div>
            <div className="text-sm text-gray-600 mt-1">Queued</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-green-600">{stats.sent_mock}</div>
            <div className="text-sm text-gray-600 mt-1">Sent (Mock)</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-sm text-gray-600 mt-1">Total Alerts</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
          <div className="lg:col-span-1 bg-white rounded-lg shadow p-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm text-gray-900 focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="draft">Draft</option>
                <option value="queued">Queued</option>
                <option value="sent_mock">Sent (Mock)</option>
                <option value="dismissed">Dismissed</option>
              </select>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Alert Type
              </label>
              <select
                value={alertTypeFilter}
                onChange={(e) => setAlertTypeFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm text-gray-900 focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Types</option>
                <option value="supervisor_review">Supervisor Review</option>
                <option value="coaching_reminder">Coaching Reminder</option>
                <option value="manual_review">Manual Review</option>
                <option value="repeated_violation">Repeated Violation</option>
              </select>
            </div>
          </div>

          <div className="lg:col-span-3">
            {loading ? (
              <div className="bg-white rounded-lg shadow p-8 text-center text-gray-600">
                Loading alerts...
              </div>
            ) : alerts.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-8 text-center text-gray-600">
                No alerts found. Check back soon!
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <AlertCard key={alert.id} alert={alert} onSelect={setSelectedAlert} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {selectedAlert && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-96 overflow-y-auto">
            <div className="sticky top-0 bg-gray-50 border-b px-6 py-4 flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">Alert Details</h2>
              <button
                onClick={() => setSelectedAlert(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
              >
                ×
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Title</label>
                <p className="text-gray-900 font-semibold mt-1">{selectedAlert.title}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700">Message</label>
                <p className="text-gray-700 mt-1">{selectedAlert.message}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">Alert Type</label>
                  <p className="text-gray-900 mt-1 text-sm">
                    {getAlertTypeLabel(selectedAlert.alertType)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Status</label>
                  <p className="text-gray-900 mt-1 text-sm capitalize">{selectedAlert.status}</p>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700">Event ID</label>
                <p className="text-gray-600 text-xs font-mono mt-1">{selectedAlert.safetyEventId}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700">Created</label>
                <p className="text-gray-600 text-sm mt-1">
                  {new Date(selectedAlert.createdAt).toLocaleString()}
                </p>
              </div>

              <div className="border-t pt-4 space-y-2">
                {selectedAlert.status === "draft" && (
                  <button
                    onClick={() => {
                      handleStatusUpdate(selectedAlert.id, "sent_mock");
                      setSelectedAlert(null);
                    }}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                  >
                    Mark as Sent
                  </button>
                )}

                {selectedAlert.status !== "dismissed" && selectedAlert.status !== "sent_mock" && (
                  <button
                    onClick={() => {
                      handleStatusUpdate(selectedAlert.id, "dismissed");
                      setSelectedAlert(null);
                    }}
                    className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                  >
                    Dismiss
                  </button>
                )}

                <button
                  onClick={() => setSelectedAlert(null)}
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
