"use client";

import { ModelComparison } from "@/lib/types";

const LABEL_DISPLAY: Record<string, string> = {
  person: "Person",
  helmet: "Helmet",
  no_helmet: "No Helmet",
  vest: "Vest",
  no_vest: "No Vest",
};

function labelBadge(label: string, variant: "green" | "red" | "blue" | "gray") {
  const classes: Record<string, string> = {
    green: "bg-green-100 text-green-800",
    red: "bg-red-100 text-red-800",
    blue: "bg-blue-100 text-blue-800",
    gray: "bg-gray-100 text-gray-700",
  };
  return (
    <span
      key={label}
      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${classes[variant]}`}
    >
      {LABEL_DISPLAY[label] ?? label}
    </span>
  );
}

function DetectionList({
  title,
  detections,
  available,
  error,
  accentColor,
}: {
  title: string;
  detections: ModelComparison["roboflow"]["detections"];
  available: boolean;
  error: string | null;
  accentColor: string;
}) {
  const labelCounts = detections.reduce<Record<string, number>>((acc, d) => {
    acc[d.label] = (acc[d.label] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className={`flex-1 rounded-lg border-2 ${accentColor} p-4`}>
      <h4 className="font-semibold text-gray-900 mb-3">{title}</h4>
      {!available ? (
        <p className="text-sm text-gray-500 italic">{error ?? "Not available"}</p>
      ) : detections.length === 0 ? (
        <p className="text-sm text-gray-500 italic">No detections</p>
      ) : (
        <div className="space-y-2">
          <p className="text-sm text-gray-600">{detections.length} detection{detections.length !== 1 ? "s" : ""}</p>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(labelCounts).map(([label, count]) => (
              <span
                key={label}
                className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-800 rounded-md text-xs font-medium"
              >
                {LABEL_DISPLAY[label] ?? label}
                {count > 1 && <span className="text-gray-500">×{count}</span>}
              </span>
            ))}
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Avg confidence:{" "}
            {(
              detections.reduce((sum, d) => sum + d.confidence, 0) / detections.length
            ).toFixed(2)}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ModelComparisonPanel({ comparison }: { comparison: ModelComparison }) {
  const { roboflow, qwen, agreement } = comparison;
  const total = agreement.matchingLabels.length + agreement.roboflowOnly.length + agreement.qwenOnly.length;
  const agreePct = total > 0 ? Math.round((agreement.matchingLabels.length / total) * 100) : 100;

  return (
    <div className="space-y-4">
      {/* Agreement summary bar */}
      <div className="flex items-center gap-3">
        <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden flex">
          <div
            className="h-full bg-green-500 transition-all"
            style={{ width: `${agreePct}%` }}
            title={`Both agreed: ${agreement.matchingLabels.length}`}
          />
          <div
            className="h-full bg-blue-400"
            style={{
              width: total > 0 ? `${Math.round((agreement.roboflowOnly.length / total) * 100)}%` : "0%",
            }}
            title={`Roboflow only: ${agreement.roboflowOnly.length}`}
          />
          <div
            className="h-full bg-orange-400"
            style={{
              width: total > 0 ? `${Math.round((agreement.qwenOnly.length / total) * 100)}%` : "0%",
            }}
            title={`Qwen only: ${agreement.qwenOnly.length}`}
          />
        </div>
        <span className="text-sm font-semibold text-gray-700">{agreePct}% agreement</span>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-xs text-gray-600">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          Both agree ({agreement.matchingLabels.length})
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-blue-400" />
          Roboflow only ({agreement.roboflowOnly.length})
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-orange-400" />
          Qwen only ({agreement.qwenOnly.length})
        </div>
      </div>

      {/* Side-by-side model results */}
      <div className="flex gap-4">
        <DetectionList
          title="Roboflow"
          detections={roboflow.detections}
          available={roboflow.available}
          error={roboflow.error}
          accentColor="border-blue-300"
        />
        <DetectionList
          title="Qwen Vision"
          detections={qwen.detections}
          available={qwen.available}
          error={qwen.error}
          accentColor="border-orange-300"
        />
      </div>

      {/* Label-level breakdown */}
      {agreement.matchingLabels.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Agreed</p>
          <div className="flex flex-wrap gap-1.5">
            {agreement.matchingLabels.map((l) => labelBadge(l, "green"))}
          </div>
        </div>
      )}
      {agreement.roboflowOnly.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Roboflow Only</p>
          <div className="flex flex-wrap gap-1.5">
            {agreement.roboflowOnly.map((l) => labelBadge(l, "blue"))}
          </div>
        </div>
      )}
      {agreement.qwenOnly.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Qwen Only</p>
          <div className="flex flex-wrap gap-1.5">
            {agreement.qwenOnly.map((l) => labelBadge(l, "red"))}
          </div>
        </div>
      )}
    </div>
  );
}
