interface SeverityItem {
  label: string;
  value: number;
  color: "red" | "yellow" | "green";
}

interface SeverityBreakdownCardProps {
  items: SeverityItem[];
}

export default function SeverityBreakdownCard({
  items,
}: SeverityBreakdownCardProps) {
  const colorClasses = {
    red: "text-red-600",
    yellow: "text-yellow-600",
    green: "text-green-600",
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Severity Breakdown
      </h3>
      <div className="space-y-3">
        {items.map((item, idx) => (
          <div key={idx} className="flex justify-between items-center">
            <span className="text-gray-600">{item.label}</span>
            <span className={`font-semibold ${colorClasses[item.color]}`}>
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
