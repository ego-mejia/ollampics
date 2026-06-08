import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  fetchLeaderboard,
  fetchSuites,
  type LeaderboardEntry,
  type SuiteMeta,
} from "../../api";
import Alert from "../../components/Alert";
import PageHeader from "../../components/PageHeader";
import LeaderboardChart from "./LeaderboardChart";
import LeaderboardFilters, { type Metric } from "./LeaderboardFilters";
import LeaderboardTable from "./LeaderboardTable";
import SuiteHeader from "./SuiteHeader";
import { PageWrap } from "./style";

/** Split an Ollama model name into (family, variant). For instance:
 *    qwen3.6:27b-mlx        → family="qwen3.6",  variant="27b-mlx"
 *    liquidai/lfm2.5:q8_0   → family="liquidai/lfm2.5", variant="q8_0"
 *    plain                  → family="plain",  variant=""
 */
function splitModel(name: string): { family: string; variant: string } {
  const idx = name.indexOf(":");
  if (idx < 0) return { family: name, variant: "" };
  return { family: name.slice(0, idx), variant: name.slice(idx + 1) };
}

export default function Leaderboard() {
  const { t } = useTranslation();
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [suites, setSuites] = useState<SuiteMeta[]>([]);
  const [suite, setSuite] = useState<string>("");
  const [metric, setMetric] = useState<Metric>("success_rate");
  const [modelFamily, setModelFamily] = useState<string>("");
  const [variant, setVariant] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetchSuites().then(setSuites).catch((e) => setErr(String(e)));
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchLeaderboard(suite || undefined, metric)
      .then(setEntries)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, [suite, metric]);

  // Available options for the family / variant filters — computed from current
  // results so we never show a dropdown value that wouldn't filter to anything.
  const { modelFamilies, variants } = useMemo(() => {
    const fams = new Set<string>();
    const vars_ = new Set<string>();
    for (const e of entries) {
      const { family, variant: v } = splitModel(e.model);
      fams.add(family);
      if (v) vars_.add(v);
    }
    return {
      modelFamilies: [...fams].sort(),
      variants: [...vars_].sort(),
    };
  }, [entries]);

  // Apply family/variant filters client-side
  const filtered = useMemo(() => {
    return entries.filter((e) => {
      const { family, variant: v } = splitModel(e.model);
      if (modelFamily && family !== modelFamily) return false;
      if (variant && v !== variant) return false;
      return true;
    });
  }, [entries, modelFamily, variant]);

  return (
    <PageWrap>
      <PageHeader title={t("leaderboard.title")} subtitle={t("leaderboard.subtitle")} />

      <SuiteHeader suite={suite} />

      <LeaderboardFilters
        suites={suites}
        suite={suite}
        setSuite={setSuite}
        metric={metric}
        setMetric={setMetric}
        modelFamilies={modelFamilies}
        modelFamily={modelFamily}
        setModelFamily={setModelFamily}
        variants={variants}
        variant={variant}
        setVariant={setVariant}
      />

      <LeaderboardChart entries={filtered} suite={suite} />

      {err && <Alert>{err}</Alert>}
      <LeaderboardTable entries={filtered} loading={loading} />
    </PageWrap>
  );
}
