"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ChartArtifact } from "@/types/artifact";

export function ChartArtifactView({ artifact }: { artifact: ChartArtifact }) {
  return (
    <div className="h-[360px] rounded-2xl border border-white/10 bg-black/20 p-4">
      <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
        {artifact.chartType === "bar" ? (
          <BarChart data={artifact.data}>
            <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
            <XAxis dataKey={artifact.xKey} stroke="#94a3b8" tickLine={false} />
            <YAxis stroke="#94a3b8" tickLine={false} />
            <Tooltip
              contentStyle={{
                background: "#080A12",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: "12px",
                color: "#e2e8f0",
              }}
            />
            <Bar dataKey={artifact.yKey} fill="#67e8f9" radius={[6, 6, 0, 0]} />
          </BarChart>
        ) : (
          <LineChart data={artifact.data}>
            <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
            <XAxis dataKey={artifact.xKey} stroke="#94a3b8" tickLine={false} />
            <YAxis stroke="#94a3b8" tickLine={false} />
            <Tooltip
              contentStyle={{
                background: "#080A12",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: "12px",
                color: "#e2e8f0",
              }}
            />
            <Line
              type="monotone"
              dataKey={artifact.yKey}
              stroke="#67e8f9"
              strokeWidth={2}
              dot={{ fill: "#67e8f9", r: 3 }}
            />
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
