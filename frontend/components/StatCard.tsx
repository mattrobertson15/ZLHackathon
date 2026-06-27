interface StatCardProps {
  label: string;
  value: number;
  color?: "green" | "red" | "yellow" | "gray";
}

export default function StatCard({
  label,
  value,
  color = "gray",
}: StatCardProps) {
  const colorClasses = {
    green: "text-green-600",
    red: "text-red-600",
    yellow: "text-yellow-600",
    gray: "text-gray-900",
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-sm font-medium text-gray-600">{label}</h3>
      <p className={`text-3xl font-bold ${colorClasses[color]} mt-2`}>
        {value}
      </p>
    </div>
  );
}
