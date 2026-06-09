import { useTranslation } from "react-i18next";
import type { ModelBrief } from "../../../api";
import { Field, Hint, Label, Row, Select } from "./style";

type Props = {
  options: ModelBrief[];
  valueA: string | null;
  valueB: string | null;
  onChange: (a: string | null, b: string | null) => void;
};

function optionLabel(m: ModelBrief): string {
  const parts: string[] = [m.name];
  if (m.n_runs) parts.push(`${m.n_runs} run${m.n_runs === 1 ? "" : "s"}`);
  parts.push(`${m.n_successes}/${m.n_tasks}`);
  return parts.join(" · ");
}

export default function CompareSelector({ options, valueA, valueB, onChange }: Props) {
  const { t } = useTranslation();
  return (
    <Row>
      <Field>
        <Label>{t("compare.modelA")}</Label>
        <Select
          value={valueA ?? ""}
          onChange={(e) => onChange(e.target.value || null, valueB)}
        >
          <option value="">—</option>
          {options.map((m) => (
            <option key={m.name} value={m.name}>
              {optionLabel(m)}
            </option>
          ))}
        </Select>
        <Hint>{t("compare.pickHint")}</Hint>
      </Field>
      <Field>
        <Label>{t("compare.modelB")}</Label>
        <Select
          value={valueB ?? ""}
          onChange={(e) => onChange(valueA, e.target.value || null)}
        >
          <option value="">—</option>
          {options.map((m) => (
            <option key={m.name} value={m.name}>
              {optionLabel(m)}
            </option>
          ))}
        </Select>
        <Hint>{t("compare.pickHint")}</Hint>
      </Field>
    </Row>
  );
}
