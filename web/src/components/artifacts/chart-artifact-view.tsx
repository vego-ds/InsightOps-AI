"use client";

import * as React from "react";
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

const CHART_MARGIN = { top: 16, right: 20, bottom: 8, left: 4 };
const TOOLTIP_STYLE = {
  background: "#080A12",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: "12px",
  color: "#e2e8f0",
};
const AXIS_TICK = { fill: "#94a3b8", fontSize: 11 };

export function ChartArtifactView({ artifact }: { artifact: ChartArtifact }) {
  const chartData = React.useMemo(() => artifact.data, [artifact.data]);

  if (chartData.length === 0) {
    return (
      <div className="flex min-h-[280px] items-center justify-center rounded-2xl border border-white/10 bg-black/20 p-6 text-sm text-slate-400">
        This chart artifact does not contain renderable data.
      </div>
    );
  }

  return (
    <div className="h-[min(420px,55dvh)] min-h-[320px] min-w-0 overflow-hidden rounded-2xl border border-white/10 bg-black/20 p-3 sm:p-4">
      <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
        {artifact.chartType === "bar" ? (
          <BarChart data={chartData} margin={CHART_MARGIN}>
            <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
            <XAxis
              dataKey={artifact.xKey}
              stroke="#94a3b8"
              tick={AXIS_TICK}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis stroke="#94a3b8" tick={AXIS_TICK} tickLine={false} width={56} />
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              cursor={{ fill: "rgba(103,232,249,0.08)" }}
            />
            <Bar
              dataKey={artifact.yKey}
              fill="#67e8f9"
              isAnimationActive={false}
              radius={[6, 6, 0, 0]}
            />
          </BarChart>
        ) : (
          <LineChart data={chartData} margin={CHART_MARGIN}>
            <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
            <XAxis
              dataKey={artifact.xKey}
              stroke="#94a3b8"
              tick={AXIS_TICK}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis stroke="#94a3b8" tick={AXIS_TICK} tickLine={false} width={56} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Line
              type="monotone"
              dataKey={artifact.yKey}
              stroke="#67e8f9"
              strokeWidth={2}
              dot={chartData.length <= 24 ? { fill: "#67e8f9", r: 3 } : false}
              isAnimationActive={false}
            />
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
