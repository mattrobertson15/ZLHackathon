"use client";

import { AlertRecord } from "@/lib/types";

interface AlertCardProps {
  alert: AlertRecord;
  onSelect: (alert: AlertRecord) => void;
}

export default function AlertCard({ alert, onSelect }: AlertCardProps) {
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

  return (
    <div
      onClick={() => onSelect(alert)}
      className={`${getAlertTypeColor(
        alert.alertType
      )} rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow`}
    >
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h3 className="font-semibold mb-1">{alert.title}</h3>
          <p className="text-sm opacity-90">{alert.message}</p>
        </div>
        <div className="flex gap-2 ml-4">
          <span
            className={`inline-block px-2 py-1 text-xs font-medium rounded whitespace-nowrap ${getStatusColor(
              alert.status
            )}`}
          >
            {alert.status}
          </span>
        </div>
      </div>
      <div className="text-xs opacity-75 mt-2">
        {new Date(alert.createdAt).toLocaleString()}
      </div>
    </div>
  );
}
