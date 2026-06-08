import { useTranslation } from "react-i18next";
import { SectionTitle } from "../../../components/PageHeader";
import type { SuiteMeta } from "../../../api";
import {
  Checkbox,
  CountAccent,
  RowLabel,
  SelectorBox,
  SuiteName,
  TasksText,
} from "./style";

type Props = {
  suites: SuiteMeta[];
  selected: Set<string>;
  onToggle: (name: string) => void;
};

export default function SuitesSelector({ suites, selected, onToggle }: Props) {
  const { t } = useTranslation();
  return (
    <section>
      <SectionTitle>
        {t("launcher.suitesLabel")} ·{" "}
        <CountAccent>
          {t("launcher.suitesSelected", { count: selected.size })}
        </CountAccent>
      </SectionTitle>
      <SelectorBox>
        {suites.map((s) => (
          <RowLabel key={s.name}>
            <Checkbox
              type="checkbox"
              checked={selected.has(s.name)}
              onChange={() => onToggle(s.name)}
            />
            <SuiteName>{s.name}</SuiteName>
            <TasksText>{t("launcher.tasks", { count: s.tasks.length })}</TasksText>
          </RowLabel>
        ))}
      </SelectorBox>
    </section>
  );
}
