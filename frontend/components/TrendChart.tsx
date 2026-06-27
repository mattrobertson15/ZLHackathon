"use client";

import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface TrendPoint {
  date: string;
  compliancePercentage: number;
  totalViolations: number;
  noHelmet: number;
  noVest: number;
}

interface TrendChartProps {
  points: TrendPoint[];
  title?: string;
}

export default function TrendChart({
  points,
  title = "Compliance Trends",
}: TrendChartProps) {
  if (points.length === 0) {
    return null;
  }

  const formatted = points.map((p) => ({
    ...p,
    date: p.date.length > 10 ? p.date.slice(0, 10) : p.date,
  }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">{title}</h3>

      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={formatted} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12, fill: "#6b7280" }}
            tickLine={false}
          />
          <YAxis
            yAxisId="pct"
            orientation="left"
            domain={[0, 100]}
            tickFormatter={(v) => `${v}%`}
            tick={{ fontSize: 12, fill: "#6b7280" }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            yAxisId="count"
            orientation="right"
            allowDecimals={false}
            tick={{ fontSize: 12, fill: "#6b7280" }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{ borderRadius: 8, border: "1px solid #e5e7eb", fontSize: 13 }}
            formatter={(value, name) => {
              if (name === "Compliance %") return [`${value}%`, name];
              return [value as number, name as string];
            }}
          />
          <Legend wrapperStyle={{ fontSize: 13, paddingTop: 12 }} />
          <Bar yAxisId="count" dataKey="noHelmet" name="No Helmet" fill="#fca5a5" radius={[3, 3, 0, 0]} />
          <Bar yAxisId="count" dataKey="noVest" name="No Vest" fill="#fcd34d" radius={[3, 3, 0, 0]} />
          <Line
            yAxisId="pct"
            type="monotone"
            dataKey="compliancePercentage"
            name="Compliance %"
            stroke="#22c55e"
            strokeWidth={2.5}
            dot={{ r: 4, fill: "#22c55e" }}
            activeDot={{ r: 6 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
