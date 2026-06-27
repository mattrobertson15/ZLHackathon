import type { RepeatedViolation } from "@/lib/types";

interface RepeatedViolationsCardProps {
  items: RepeatedViolation[];
}

const violationLabels: Record<string, string> = {
  no_helmet: "Missing Helmet",
  no_vest: "Missing Vest",
};

function severityClasses(severity: string): string {
  switch (severity) {
    case "high":
      return "bg-red-100 text-red-800";
    case "medium":
      return "bg-yellow-100 text-yellow-800";
    default:
      return "bg-green-100 text-green-800";
  }
}

export default function RepeatedViolationsCard({
  items,
}: RepeatedViolationsCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-lg font-semibold text-gray-900">Repeated Zone Issues</h3>
        <span className="text-xs text-gray-500">Past 7 days · 3+ repeats</span>
      </div>
      <p className="text-sm text-gray-500 mb-4">
        Zones with the same violation recurring this week (no employee identity).
      </p>

      {items.length === 0 ? (
        <div className="text-sm text-gray-500 py-6 text-center">
          No repeated zone issues this week.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-200">
                <th className="py-2 pr-4 font-medium">Zone</th>
                <th className="py-2 pr-4 font-medium">Violation</th>
                <th className="py-2 pr-4 font-medium text-right">Count</th>
                <th className="py-2 pr-4 font-medium">Severity</th>
                <th className="py-2 font-medium">Last seen</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={`${item.zoneLabel}-${item.violationType}`}
                  className="border-b border-gray-100 last:border-0"
                >
                  <td className="py-2 pr-4 font-medium text-gray-900">
                    {item.zoneLabel}
                  </td>
                  <td className="py-2 pr-4 text-gray-700">
                    {violationLabels[item.violationType] || item.violationType}
                  </td>
                  <td className="py-2 pr-4 text-right text-gray-900">
                    {item.count}
                    <span className="text-gray-400">
                      {" "}
                      ({item.distinctUploadCount} uploads)
                    </span>
                  </td>
                  <td className="py-2 pr-4">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${severityClasses(
                        item.severity
                      )}`}
                    >
                      {item.severity}
                    </span>
                  </td>
                  <td className="py-2 text-gray-600">
                    {new Date(item.lastSeenAt).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
