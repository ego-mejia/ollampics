import { useEffect, useMemo, useState } from "react";
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
import { fetchLeaderboard, type LeaderboardEntry } from "../../../api";
import { Empty, Header, Sub, Title, Wrap } from "./style";

const COLORS = ["#3D49E4", "#5DBA32", "#F4C84A", "#8AA7E8", "#E5358F", "#F2A340", "#8C42D8"];

type Row = { model: string; successRate: number; tps: number };

export default function ModelsChart() {
  const { t } = useTranslation();
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLeaderboard()
      .then(setEntries)
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, []);

  const rows: Row[] = useMemo(() => {
    // Aggregate by model across all suites + runtimes.
    // success_rate: weighted by n_tasks. tps: averaged across runtime/suite variants.
    const byModel = new Map<
      string,
      { successWeighted: number; tasks: number; tpsSum: number; tpsN: number }
    >();
    for (const e of entries) {
      const prev = byModel.get(e.model) || { successWeighted: 0, tasks: 0, tpsSum: 0, tpsN: 0 };
      prev.successWeighted += e.success_rate * e.n_tasks;
      prev.tasks += e.n_tasks;
      if (e.avg_tps != null) {
        prev.tpsSum += e.avg_tps;
        prev.tpsN += 1;
      }
      byModel.set(e.model, prev);
    }
    return [...byModel.entries()]
      .map(([model, agg]) => ({
        model: shortenModel(model),
        successRate: agg.tasks > 0 ? (agg.successWeighted / agg.tasks) * 100 : 0,
        tps: agg.tpsN > 0 ? Number((agg.tpsSum / agg.tpsN).toFixed(1)) : 0,
      }))
      .sort((a, b) => b.successRate - a.successRate);
  }, [entries]);

  if (loading) return null;

  return (
    <Wrap>
      <Header>
        <Title>{t("dashboard.chartTitle")}</Title>
        <Sub>{t("dashboard.chartSub")}</Sub>
      </Header>
      {rows.length === 0 ? (
        <Empty>{t("dashboard.chartEmpty")}</Empty>
      ) : (
        <div style={{ width: "100%", height: 300 }}>
          <ResponsiveContainer>
            <ComposedChart data={rows} margin={{ top: 10, right: 20, left: 0, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border-soft))" />
              <XAxis
                dataKey="model"
                stroke="rgb(var(--fg-dim))"
                fontSize={11}
                angle={-15}
                textAnchor="end"
                interval={0}
                height={60}
              />
              <YAxis
                yAxisId="left"
                stroke="rgb(var(--fg-dim))"
                fontSize={11}
                domain={[0, 100]}
                unit="%"
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="rgb(var(--fg-dim))"
                fontSize={11}
              />
              <Tooltip
                contentStyle={{
                  background: "rgb(var(--card))",
                  border: "1px solid rgb(var(--border))",
                  fontSize: 12,
                }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar yAxisId="left" dataKey="successRate" name="success%" radius={[4, 4, 0, 0]}>
                {rows.map((_, i) => (
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
      )}
    </Wrap>
  );
}

function shortenModel(name: string): string {
  const last = name.split("/").pop() || name;
  return last.length > 28 ? last.slice(0, 26) + "…" : last;
}
