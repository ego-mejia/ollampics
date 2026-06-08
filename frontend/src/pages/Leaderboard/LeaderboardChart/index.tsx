import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { LeaderboardEntry } from "../../../api";
import { Empty, Title, Wrap } from "./style";

const COLORS = ["#3D49E4", "#5DBA32", "#F4C84A", "#8AA7E8", "#E5358F", "#F2A340", "#8C42D8", "#E5402F"];

type Props = {
  entries: LeaderboardEntry[];
  suite: string;
};

export default function LeaderboardChart({ entries, suite }: Props) {
  const { t } = useTranslation();

  const data = useMemo(
    () =>
      entries.map((e) => ({
        model: shorten(e.model),
        successRate: Math.round(e.success_rate * 100),
        tps: e.avg_tps ? Number(e.avg_tps.toFixed(1)) : 0,
        ttft: e.avg_ttft_ms ? Math.round(e.avg_ttft_ms) : 0,
        suite: e.suite,
      })),
    [entries]
  );

  if (data.length === 0) {
    return (
      <Wrap>
        <Title>{t("leaderboard.chartTitle")}</Title>
        <Empty>{t("leaderboard.empty")}</Empty>
      </Wrap>
    );
  }

  // For specific suite: bar chart of success_rate per model.
  // For all suites: composed chart of success_rate (bars) + tps (line) per model.
  const isAll = !suite;

  return (
    <Wrap>
      <Title>{t("leaderboard.chartTitle")}</Title>
      <div style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer>
          {isAll ? (
            <ComposedChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 50 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border-soft))" />
              <XAxis
                dataKey="model"
                stroke="rgb(var(--fg-dim))"
                fontSize={11}
                angle={-20}
                textAnchor="end"
                interval={0}
                height={70}
              />
              <YAxis yAxisId="left" stroke="rgb(var(--fg-dim))" fontSize={11} unit="%" />
              <YAxis yAxisId="right" orientation="right" stroke="rgb(var(--fg-dim))" fontSize={11} />
              <Tooltip
                contentStyle={{
                  background: "rgb(var(--card))",
                  border: "1px solid rgb(var(--border))",
                  fontSize: 12,
                }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar yAxisId="left" dataKey="successRate" name="success%" radius={[4, 4, 0, 0]}>
                {data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="tps"
                stroke="#E5358F"
                strokeWidth={2}
                dot={{ r: 3 }}
                name="tps"
              />
            </ComposedChart>
          ) : (
            <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 50 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border-soft))" />
              <XAxis
                dataKey="model"
                stroke="rgb(var(--fg-dim))"
                fontSize={11}
                angle={-20}
                textAnchor="end"
                interval={0}
                height={70}
              />
              <YAxis stroke="rgb(var(--fg-dim))" fontSize={11} unit="%" domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  background: "rgb(var(--card))",
                  border: "1px solid rgb(var(--border))",
                  fontSize: 12,
                }}
                formatter={(v) => `${v}%`}
              />
              <Bar dataKey="successRate" radius={[4, 4, 0, 0]}>
                {data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </Wrap>
  );
}

function shorten(name: string): string {
  const last = name.split("/").pop() || name;
  return last.length > 24 ? last.slice(0, 22) + "…" : last;
}
