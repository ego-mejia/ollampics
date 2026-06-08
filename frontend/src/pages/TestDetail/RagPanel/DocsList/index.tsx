import { useState } from "react";
import { useTranslation } from "react-i18next";
import { fetchCorpusDoc, type CorpusDoc } from "../../../../api";
import {
  DocHeader,
  DocMeta,
  DocName,
  DocRow,
  Empty,
  FullContent,
  Preview,
  ToggleBtn,
  Wrap,
} from "./style";

type Props = { docs: CorpusDoc[] };

export default function DocsList({ docs }: Props) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState<Record<string, string>>({});

  if (docs.length === 0) {
    return <Empty>{t("tests.ragCorpusEmpty")}</Empty>;
  }

  const toggle = async (name: string) => {
    if (expanded[name]) {
      setExpanded((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
      return;
    }
    const full = await fetchCorpusDoc(name);
    setExpanded((prev) => ({ ...prev, [name]: full.content || "" }));
  };

  return (
    <Wrap>
      {docs.map((d) => {
        const isOpen = Boolean(expanded[d.name]);
        return (
          <DocRow key={d.name}>
            <DocHeader>
              <DocName>{d.name}</DocName>
              <DocMeta>
                {(d.size_bytes / 1024).toFixed(1)} KB ·{" "}
                {t("tests.linesCount", { count: d.n_lines })}
              </DocMeta>
            </DocHeader>
            <Preview>{d.preview}</Preview>
            <ToggleBtn onClick={() => toggle(d.name)}>
              {isOpen ? t("tests.hide") : t("tests.viewDocument")}
            </ToggleBtn>
            {isOpen && <FullContent>{expanded[d.name]}</FullContent>}
          </DocRow>
        );
      })}
    </Wrap>
  );
}
