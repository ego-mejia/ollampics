import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  Bar,
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

type ChartDatum = {
  model: string;
  successRate: number;
  tps: number;
  ttft: number;
};

export default function LeaderboardChart({ entries, suite }: Props) {
  const { t } = useTranslation();

  const data = useMemo<ChartDatum[]>(() => {
    // When NO suite is selected, aggregate by model name (no duplicates on X).
    // Average success_rate and tps across all (runtime, suite) combos of that model.
    // When a specific suite IS selected, show one bar per (model, runtime) variant.
    if (!suite) {
      const byModel = new Map<
        string,
        { srSum: number; srN: number; tpsSum: number; tpsN: number; ttftSum: number; ttftN: number }
      >();
      for (const e of entries) {
        const acc = byModel.get(e.model) ?? {
          srSum: 0,
          srN: 0,
          tpsSum: 0,
          tpsN: 0,
          ttftSum: 0,
          ttftN: 0,
        };
        acc.srSum += e.success_rate;
        acc.srN += 1;
        if (e.avg_tps != null) {
          acc.tpsSum += e.avg_tps;
          acc.tpsN += 1;
        }
        if (e.avg_ttft_ms != null) {
          acc.ttftSum += e.avg_ttft_ms;
          acc.ttftN += 1;
        }
        byModel.set(e.model, acc);
      }
      const rows: ChartDatum[] = [];
      for (const [name, a] of byModel) {
        rows.push({
          model: shorten(name),
          successRate: a.srN ? Math.round((a.srSum / a.srN) * 100) : 0,
          tps: a.tpsN ? Number((a.tpsSum / a.tpsN).toFixed(1)) : 0,
          ttft: a.ttftN ? Math.round(a.ttftSum / a.ttftN) : 0,
        });
      }
      rows.sort((x, y) => y.successRate - x.successRate || y.tps - x.tps);
      return rows;
    }
    return entries.map((e) => ({
      model: shorten(e.model),
      successRate: Math.round(e.success_rate * 100),
      tps: e.avg_tps ? Number(e.avg_tps.toFixed(1)) : 0,
      ttft: e.avg_ttft_ms ? Math.round(e.avg_ttft_ms) : 0,
    }));
  }, [entries, suite]);

  if (data.length === 0) {
    return (
      <Wrap>
        <Title>{t("leaderboard.chartTitle")}</Title>
        <Empty>{t("leaderboard.empty")}</Empty>
      </Wrap>
    );
  }

  return (
    <Wrap>
      <Title>{t("leaderboard.chartTitle")}</Title>
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <ComposedChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border-soft))" />
            <XAxis
              dataKey="model"
              stroke="rgb(var(--fg-dim))"
              fontSize={11}
              angle={-25}
              textAnchor="end"
              interval={0}
              height={80}
            />
            <YAxis
              yAxisId="left"
              stroke="rgb(var(--fg-dim))"
              fontSize={11}
              unit="%"
              domain={[0, 100]}
            />
            <YAxis yAxisId="right" orientation="right" stroke="rgb(var(--fg-dim))" fontSize={11} />
            <Tooltip
              contentStyle={{
                background: "rgb(var(--card))",
                border: "1px solid rgb(var(--border))",
                fontSize: 12,
              }}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar
              yAxisId="left"
              dataKey="successRate"
              name="success%"
              radius={[4, 4, 0, 0]}
            >
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
        </ResponsiveContainer>
      </div>
    </Wrap>
  );
}

function shorten(name: string): string {
  const last = name.split("/").pop() || name;
  return last.length > 24 ? last.slice(0, 22) + "…" : last;
}
