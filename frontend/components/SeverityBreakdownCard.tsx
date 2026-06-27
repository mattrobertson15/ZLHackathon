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

  const barClasses = {
    red: "bg-red-500",
    yellow: "bg-yellow-400",
    green: "bg-green-500",
  };

  const total = items.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Severity Breakdown
      </h3>
      <div className="space-y-4">
        {items.map((item, idx) => {
          const pct = total > 0 ? Math.round((item.value / total) * 100) : 0;
          return (
            <div key={idx}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-gray-600">{item.label}</span>
                <span className={`text-sm font-semibold ${colorClasses[item.color]}`}>
                  {item.value}
                </span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${barClasses[item.color]}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
