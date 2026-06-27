"use client";

import { SafetySummary } from "@/lib/types";

interface SummaryCardProps {
  summary: SafetySummary;
  onSelect: (summary: SafetySummary) => void;
}

export default function SummaryCard({ summary, onSelect }: SummaryCardProps) {
  return (
    <div
      onClick={() => onSelect(summary)}
      className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md transition-shadow border-l-4 border-blue-500"
    >
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-semibold text-gray-900">
            {summary.period.charAt(0).toUpperCase() + summary.period.slice(1)} Summary
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {new Date(summary.startDate).toLocaleDateString()} -{" "}
            {new Date(summary.endDate).toLocaleDateString()}
          </p>
        </div>
        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
          {new Date(summary.createdAt).toLocaleString()}
        </span>
      </div>
      <p className="text-sm text-gray-700 line-clamp-2">
        {summary.executiveSummary}
      </p>
    </div>
  );
}
