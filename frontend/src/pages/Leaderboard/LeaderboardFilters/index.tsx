import { useTranslation } from "react-i18next";
import type { SuiteMeta } from "../../../api";
import { Field, FieldLabel, FiltersRow, Select } from "./style";

export type Metric = "success_rate" | "avg_tps" | "avg_ttft_ms";

type Props = {
  suites: SuiteMeta[];
  suite: string;
  setSuite: (s: string) => void;
  metric: Metric;
  setMetric: (m: Metric) => void;
  modelFamilies: string[];
  modelFamily: string;
  setModelFamily: (s: string) => void;
  variants: string[];
  variant: string;
  setVariant: (s: string) => void;
};

export default function LeaderboardFilters({
  suites,
  suite,
  setSuite,
  metric,
  setMetric,
  modelFamilies,
  modelFamily,
  setModelFamily,
  variants,
  variant,
  setVariant,
}: Props) {
  const { t } = useTranslation();
  return (
    <FiltersRow>
      <Field>
        <FieldLabel>{t("leaderboard.suite")}</FieldLabel>
        <Select value={suite} onChange={(e) => setSuite(e.target.value)}>
          <option value="">{t("common.all")}</option>
          {suites.map((s) => (
            <option key={s.name} value={s.name}>{s.name}</option>
          ))}
        </Select>
      </Field>
      <Field>
        <FieldLabel>{t("leaderboard.model")}</FieldLabel>
        <Select value={modelFamily} onChange={(e) => setModelFamily(e.target.value)}>
          <option value="">{t("leaderboard.allModels")}</option>
          {modelFamilies.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </Select>
      </Field>
      <Field>
        <FieldLabel>{t("leaderboard.quantization")}</FieldLabel>
        <Select value={variant} onChange={(e) => setVariant(e.target.value)}>
          <option value="">{t("leaderboard.allQuants")}</option>
          {variants.map((v) => (
            <option key={v} value={v}>{v}</option>
          ))}
        </Select>
      </Field>
      <Field>
        <FieldLabel>{t("leaderboard.sortBy")}</FieldLabel>
        <Select value={metric} onChange={(e) => setMetric(e.target.value as Metric)}>
          <option value="success_rate">success_rate ↓</option>
          <option value="avg_tps">avg_tps ↓</option>
          <option value="avg_ttft_ms">avg_ttft_ms ↑</option>
        </Select>
      </Field>
    </FiltersRow>
  );
}
