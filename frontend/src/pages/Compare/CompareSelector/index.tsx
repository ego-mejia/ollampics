import { useTranslation } from "react-i18next";
import type { RunBrief } from "../../../api";
import { Field, Hint, Label, Row, Select } from "./style";

type Props = {
  options: RunBrief[];
  valueA: number | null;
  valueB: number | null;
  onChange: (a: number | null, b: number | null) => void;
};

function optionLabel(r: RunBrief): string {
  const parts: string[] = [`#${r.id}`];
  if (r.model) parts.push(r.model);
  if (r.num_ctx) parts.push(`ctx=${r.num_ctx}`);
  if (r.kv_cache_type) parts.push(`kv=${r.kv_cache_type}`);
  parts.push(`(${r.n_successes}/${r.n_tasks})`);
  return parts.join(" · ");
}

export default function CompareSelector({ options, valueA, valueB, onChange }: Props) {
  const { t } = useTranslation();
  return (
    <Row>
      <Field>
        <Label>{t("compare.runA")}</Label>
        <Select
          value={valueA ?? ""}
          onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null, valueB)}
        >
          <option value="">—</option>
          {options.map((r) => (
            <option key={r.id} value={r.id}>
              {optionLabel(r)}
            </option>
          ))}
        </Select>
        <Hint>{t("compare.pickHint")}</Hint>
      </Field>
      <Field>
        <Label>{t("compare.runB")}</Label>
        <Select
          value={valueB ?? ""}
          onChange={(e) => onChange(valueA, e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">—</option>
          {options.map((r) => (
            <option key={r.id} value={r.id}>
              {optionLabel(r)}
            </option>
          ))}
        </Select>
        <Hint>{t("compare.pickHint")}</Hint>
      </Field>
    </Row>
  );
}
