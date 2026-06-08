import { useTranslation } from "react-i18next";
import { SectionTitle } from "../../../components/PageHeader";
import type { ModelInfo } from "../../../api";
import {
  Checkbox,
  CountAccent,
  ModelName,
  RowLabel,
  SelectorBox,
  SizeText,
} from "./style";

type Props = {
  models: ModelInfo[];
  selected: Set<string>;
  onToggle: (name: string) => void;
};

export default function ModelsSelector({ models, selected, onToggle }: Props) {
  const { t } = useTranslation();
  return (
    <section>
      <SectionTitle>
        {t("launcher.modelsLabel")} ·{" "}
        <CountAccent>
          {t("launcher.modelsSelected", { count: selected.size })}
        </CountAccent>
      </SectionTitle>
      <SelectorBox>
        {models.map((m) => (
          <RowLabel key={m.name}>
            <Checkbox
              type="checkbox"
              checked={selected.has(m.name)}
              onChange={() => onToggle(m.name)}
            />
            <ModelName>{m.name}</ModelName>
            <SizeText>
              {(m.size_bytes / (1024 * 1024 * 1024)).toFixed(1)} GB
            </SizeText>
          </RowLabel>
        ))}
      </SelectorBox>
    </section>
  );
}
