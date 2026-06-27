"use client";

import { useState } from "react";
import { SafetyEvent, Severity, EventStatus } from "@/lib/types";

interface EventTableProps {
  events: SafetyEvent[];
  onEventSelect: (event: SafetyEvent) => void;
  onStatusUpdate: (eventId: string, status: EventStatus, note?: string) => void;
  updatingEventId?: string | null;
}

const QUICK_ACTIONS: { status: EventStatus; label: string; needsNote: boolean }[] = [
  { status: "reviewed", label: "Mark Reviewed", needsNote: false },
  { status: "dismissed", label: "Dismiss", needsNote: true },
  { status: "resolved", label: "Resolve", needsNote: true },
];

export default function EventTable({
  events,
  onEventSelect,
  onStatusUpdate,
  updatingEventId,
}: EventTableProps) {
  const [notePromptFor, setNotePromptFor] = useState<{
    eventId: string;
    status: EventStatus;
  } | null>(null);
  const [noteDraft, setNoteDraft] = useState("");

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

  const handleQuickAction = (
    e: React.MouseEvent,
    eventId: string,
    status: EventStatus,
    needsNote: boolean
  ) => {
    e.stopPropagation();
    if (needsNote) {
      setNotePromptFor({ eventId, status });
      setNoteDraft("");
      return;
    }
    onStatusUpdate(eventId, status);
  };

  const confirmNotePrompt = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!notePromptFor) return;
    onStatusUpdate(notePromptFor.eventId, notePromptFor.status, noteDraft.trim() || undefined);
    setNotePromptFor(null);
    setNoteDraft("");
  };

  const cancelNotePrompt = (e: React.MouseEvent) => {
    e.stopPropagation();
    setNotePromptFor(null);
    setNoteDraft("");
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

          {event.status !== "resolved" && (
            <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100">
              {QUICK_ACTIONS.filter((a) => a.status !== event.status).map((action) => (
                <button
                  key={action.status}
                  onClick={(e) =>
                    handleQuickAction(e, event.id, action.status, action.needsNote)
                  }
                  disabled={updatingEventId === event.id}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}

          {notePromptFor?.eventId === event.id && (
            <div
              className="mt-3 pt-3 border-t border-gray-100"
              onClick={(e) => e.stopPropagation()}
            >
              <p className="text-xs font-medium text-gray-700 mb-1">
                Note for {notePromptFor.status} (optional)
              </p>
              <textarea
                value={noteDraft}
                onChange={(e) => setNoteDraft(e.target.value)}
                placeholder={
                  notePromptFor.status === "dismissed"
                    ? "e.g. false positive — shadow on hard hat"
                    : "e.g. spoke with worker, vest now worn"
                }
                className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                rows={2}
              />
              <div className="flex gap-2 mt-2">
                <button
                  onClick={confirmNotePrompt}
                  disabled={updatingEventId === event.id}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  Confirm {notePromptFor.status}
                </button>
                <button
                  onClick={cancelNotePrompt}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
