import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  fetchCorpusDocs,
  fetchCorpusPrompts,
  type CorpusDoc,
  type PromptFile,
} from "../../../api";
import Card from "../../../components/Card";
import { SectionTitle } from "../../../components/PageHeader";
import DocsList from "./DocsList";
import GenerateButton from "./GenerateButton";
import PromptsViewer from "./PromptsViewer";
import { Section } from "./style";

export default function RagPanel() {
  const { t } = useTranslation();
  const [docs, setDocs] = useState<CorpusDoc[]>([]);
  const [prompts, setPrompts] = useState<PromptFile[]>([]);

  const reload = useCallback(async () => {
    const [d, p] = await Promise.all([fetchCorpusDocs(), fetchCorpusPrompts()]);
    setDocs(d);
    setPrompts(p);
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  // Poll while generation is running (after pressing Generate).
  const onTriggered = useCallback(() => {
    let count = 0;
    const tick = async () => {
      count += 1;
      await reload();
      if (count < 10) setTimeout(tick, 4000);
    };
    setTimeout(tick, 4000);
  }, [reload]);

  return (
    <>
      <Section>
        <SectionTitle>{t("tests.ragCorpusTitle")}</SectionTitle>
        <GenerateButton onTriggered={onTriggered} hasCorpus={docs.length > 0} />
        <Card>
          <DocsList docs={docs} />
        </Card>
      </Section>

      <Section>
        <SectionTitle>{t("tests.ragPromptsTitle")}</SectionTitle>
        <Card>
          <PromptsViewer prompts={prompts} />
        </Card>
      </Section>
    </>
  );
}
