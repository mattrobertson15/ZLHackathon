interface TrendPoint {
  date: string;
  compliancePercentage: number;
  totalViolations: number;
  noHelmet: number;
  noVest: number;
}

interface TrendTableProps {
  points: TrendPoint[];
  title?: string;
}

export default function TrendTable({
  points,
  title = "Compliance Trends",
}: TrendTableProps) {
  if (points.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
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
            {points.map((point) => (
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
  );
}
