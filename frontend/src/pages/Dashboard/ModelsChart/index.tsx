import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchLeaderboard, type LeaderboardEntry } from "../../../api";
import { Empty, Header, Sub, Title, Wrap } from "./style";

const COLORS = ["#3D49E4", "#5DBA32", "#F4C84A", "#8AA7E8", "#E5358F", "#F2A340", "#8C42D8"];

type Row = { model: string; successRate: number; tps: number | null };

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
    // Aggregate by model across all suites + runtimes — average success_rate
    // weighted by n_tasks; best tps.
    const byModel = new Map<string, { successWeighted: number; tasks: number; tps: number }>();
    for (const e of entries) {
      const prev = byModel.get(e.model) || { successWeighted: 0, tasks: 0, tps: 0 };
      prev.successWeighted += e.success_rate * e.n_tasks;
      prev.tasks += e.n_tasks;
      prev.tps = Math.max(prev.tps, e.avg_tps || 0);
      byModel.set(e.model, prev);
    }
    return [...byModel.entries()]
      .map(([model, agg]) => ({
        model: shortenModel(model),
        successRate: agg.tasks > 0 ? (agg.successWeighted / agg.tasks) * 100 : 0,
        tps: agg.tps || null,
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
        <div style={{ width: "100%", height: 260 }}>
          <ResponsiveContainer>
            <BarChart data={rows} margin={{ top: 10, right: 20, left: 0, bottom: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border-soft))" />
              <XAxis
                dataKey="model"
                stroke="rgb(var(--fg-dim))"
                fontSize={11}
                angle={-15}
                textAnchor="end"
                interval={0}
                height={50}
              />
              <YAxis
                stroke="rgb(var(--fg-dim))"
                fontSize={11}
                domain={[0, 100]}
                unit="%"
              />
              <Tooltip
                contentStyle={{
                  background: "rgb(var(--card))",
                  border: "1px solid rgb(var(--border))",
                  fontSize: 12,
                }}
                formatter={(v) => `${Number(v).toFixed(1)}%`}
              />
              <Bar dataKey="successRate" radius={[4, 4, 0, 0]}>
                {rows.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </Wrap>
  );
}

function shortenModel(name: string): string {
  // Keep last segment after / and trim quant tag for readability
  const last = name.split("/").pop() || name;
  return last.length > 28 ? last.slice(0, 26) + "…" : last;
}
