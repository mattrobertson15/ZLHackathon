interface ComplianceScoreCardProps {
  percentage: number;
  label?: string;
}

export default function ComplianceScoreCard({
  percentage,
  label = "Compliance Rate",
}: ComplianceScoreCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-sm font-medium text-gray-600">{label}</h3>
      <p className="text-3xl font-bold text-green-600 mt-2">{percentage}%</p>
    </div>
  );
}
