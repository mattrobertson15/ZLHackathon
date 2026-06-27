"use client";

import { SafetyEvent, Severity, EventStatus } from "@/lib/types";

interface EventTableProps {
  events: SafetyEvent[];
  onEventSelect: (event: SafetyEvent) => void;
}

export default function EventTable({ events, onEventSelect }: EventTableProps) {
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

  if (events.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center text-gray-600">
        No events found
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {events.map((event) => (
        <div
          key={event.id}
          className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => onEventSelect(event)}
        >
          <div className="flex justify-between items-start mb-2">
            <div className="flex-1">
              <p className="font-semibold text-gray-900 capitalize">
                {event.eventType.replace(/_/g, " ")}
              </p>
              {event.violationType && (
                <p className="text-sm text-gray-600 capitalize">
                  {event.violationType.replace(/_/g, " ")}
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <span
                className={`inline-block px-3 py-1 text-sm font-medium rounded-full ${getSeverityColor(
                  event.severity
                )}`}
              >
                {event.severity}
              </span>
              <span
                className={`inline-block px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(
                  event.status
                )}`}
              >
                {event.status}
              </span>
            </div>
          </div>
          <p className="text-sm text-gray-600">{event.suggestedAction}</p>
          <p className="text-xs text-gray-500 mt-2">
            Confidence: {(event.confidence * 100).toFixed(1)}% • ID: {event.id}
          </p>
        </div>
      ))}
    </div>
  );
}
