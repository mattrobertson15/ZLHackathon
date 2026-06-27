interface ViolationBreakdownItem {
  label: string;
  value: number;
}

interface ViolationBreakdownCardProps {
  title: string;
  items: ViolationBreakdownItem[];
}

export default function ViolationBreakdownCard({
  title,
  items,
}: ViolationBreakdownCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="space-y-3">
        {items.map((item, idx) => (
          <div key={idx} className="flex justify-between items-center">
            <span className="text-gray-600">{item.label}</span>
            <span className="font-semibold text-gray-900">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
