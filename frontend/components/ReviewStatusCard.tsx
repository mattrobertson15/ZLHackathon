import Link from "next/link";

interface ReviewStatusCardProps {
  statusBreakdown: {
    open: number;
    reviewed: number;
    dismissed: number;
    resolved: number;
  };
}

const STATUS_META: { key: keyof ReviewStatusCardProps["statusBreakdown"]; label: string; color: string }[] = [
  { key: "open", label: "Open", color: "text-blue-600" },
  { key: "reviewed", label: "Reviewed", color: "text-purple-600" },
  { key: "dismissed", label: "Dismissed", color: "text-gray-600" },
  { key: "resolved", label: "Resolved", color: "text-green-600" },
];

export default function ReviewStatusCard({ statusBreakdown }: ReviewStatusCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Review Status</h3>
      <div className="space-y-3">
        {STATUS_META.map(({ key, label, color }) => (
          <Link
            key={key}
            href={`/app/events?status=${key}`}
            className="flex justify-between items-center hover:bg-gray-50 rounded px-1 -mx-1 py-0.5 transition-colors"
          >
            <span className="text-gray-600">{label}</span>
            <span className={`font-semibold ${color}`}>{statusBreakdown[key]}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
