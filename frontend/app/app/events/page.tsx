"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listEvents, updateEvent } from "@/lib/api";
import { SafetyEvent, EventStatus, Severity } from "@/lib/types";
import EventTable from "@/components/EventTable";

export default function EventsPage() {
  const [events, setEvents] = useState<SafetyEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [eventTypeFilter, setEventTypeFilter] = useState<string>("");
  const [selectedEvent, setSelectedEvent] = useState<SafetyEvent | null>(null);
  const [updatingEventId, setUpdatingEventId] = useState<string | null>(null);

  const fetchEvents = async (
    status?: string,
    severity?: string,
    eventType?: string
  ) => {
    try {
      setLoading(true);
      const data = await listEvents({
        status: status || undefined,
        severity: severity || undefined,
        eventType: eventType || undefined,
        limit: 100,
      });
      setEvents(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load events");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents(statusFilter, severityFilter, eventTypeFilter);
  }, [statusFilter, severityFilter, eventTypeFilter]);

  const handleStatusUpdate = async (eventId: string, newStatus: EventStatus) => {
    try {
      setUpdatingEventId(eventId);
      await updateEvent(eventId, newStatus);
      setEvents((prev) =>
        prev.map((e) => (e.id === eventId ? { ...e, status: newStatus } : e))
      );
      if (selectedEvent?.id === eventId) {
        setSelectedEvent({ ...selectedEvent, status: newStatus });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update event");
    } finally {
      setUpdatingEventId(null);
    }
  };

  const getSeverityColor = (severity: Severity) => {
    switch (severity) {
      case "high":
        return "bg-red-100 text-red-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "low":
        return "bg-green-100 text-green-800";
    }
  };

  const getStatusColor = (status: EventStatus) => {
    switch (status) {
      case "open":
        return "bg-blue-100 text-blue-800";
      case "reviewed":
        return "bg-purple-100 text-purple-800";
      case "dismissed":
        return "bg-gray-100 text-gray-800";
      case "resolved":
        return "bg-green-100 text-green-800";
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
            <Link href="/app/alerts" className="text-gray-600 hover:text-gray-900">
              Alerts
            </Link>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Safety Events</h1>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="reviewed">Reviewed</option>
              <option value="dismissed">Dismissed</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Severity
            </label>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Severities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Event Type
            </label>
            <select
              value={eventTypeFilter}
              onChange={(e) => setEventTypeFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              <option value="ppe_violation">PPE Violation</option>
              <option value="positive_observation">Positive Observation</option>
              <option value="uncertain_review">Uncertain Review</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            {loading ? (
              <div className="bg-white rounded-lg shadow p-8 text-center text-gray-600">
                Loading events...
              </div>
            ) : (
              <EventTable events={events} onEventSelect={setSelectedEvent} />
            )}
          </div>

          <div>
            {selectedEvent ? (
              <div className="bg-white rounded-lg shadow p-6 sticky top-8">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Event Details
                </h2>

                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-600">Event Type</p>
                    <p className="font-medium text-gray-900 capitalize">
                      {selectedEvent.eventType.replace(/_/g, " ")}
                    </p>
                  </div>

                  {selectedEvent.violationType && (
                    <div>
                      <p className="text-sm text-gray-600">Violation Type</p>
                      <p className="font-medium text-gray-900 capitalize">
                        {selectedEvent.violationType.replace(/_/g, " ")}
                      </p>
                    </div>
                  )}

                  <div>
                    <p className="text-sm text-gray-600">Severity</p>
                    <p
                      className={`inline-block px-3 py-1 text-sm font-medium rounded-full mt-1 ${getSeverityColor(
                        selectedEvent.severity
                      )}`}
                    >
                      {selectedEvent.severity}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm text-gray-600">Status</p>
                    <p
                      className={`inline-block px-3 py-1 text-sm font-medium rounded-full mt-1 ${getStatusColor(
                        selectedEvent.status
                      )}`}
                    >
                      {selectedEvent.status}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm text-gray-600">Confidence</p>
                    <p className="font-medium text-gray-900">
                      {(selectedEvent.confidence * 100).toFixed(1)}%
                    </p>
                  </div>

                  <div>
                    <p className="text-sm text-gray-600">Suggested Action</p>
                    <p className="font-medium text-gray-900">
                      {selectedEvent.suggestedAction}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm text-gray-600">Created</p>
                    <p className="font-medium text-gray-900">
                      {new Date(selectedEvent.createdAt).toLocaleString()}
                    </p>
                  </div>

                  {selectedEvent.status !== "resolved" && (
                    <div className="pt-4 border-t border-gray-200">
                      <p className="text-sm font-medium text-gray-700 mb-2">
                        Update Status
                      </p>
                      <div className="space-y-2">
                        {(
                          [
                            "reviewed",
                            "dismissed",
                            "resolved",
                          ] as EventStatus[]
                        )
                          .filter((s) => s !== selectedEvent.status)
                          .map((status) => (
                            <button
                              key={status}
                              onClick={() =>
                                handleStatusUpdate(selectedEvent.id, status)
                              }
                              disabled={updatingEventId === selectedEvent.id}
                              className="w-full px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 capitalize transition-colors"
                            >
                              Mark as {status}
                            </button>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-6 text-center text-gray-600">
                Select an event to view details
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
