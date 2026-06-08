import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { PromptFile } from "../../../../api";
import {
  Content,
  Hint,
  PromptHeader,
  PromptMeta,
  PromptName,
  PromptRow,
  ToggleBtn,
  Wrap,
} from "./style";

type Props = { prompts: PromptFile[] };

export default function PromptsViewer({ prompts }: Props) {
  const { t } = useTranslation();
  const [open, setOpen] = useState<Set<string>>(new Set());

  const toggle = (name: string) => {
    const next = new Set(open);
    next.has(name) ? next.delete(name) : next.add(name);
    setOpen(next);
  };

  return (
    <Wrap>
      <Hint>{t("tests.ragPromptsHint")}</Hint>
      {prompts.map((p) => {
        const isOpen = open.has(p.name);
        return (
          <PromptRow key={p.name}>
            <PromptHeader>
              <PromptName>{p.name}</PromptName>
              <PromptMeta>{(p.size_bytes / 1024).toFixed(1)} KB</PromptMeta>
            </PromptHeader>
            <ToggleBtn onClick={() => toggle(p.name)}>
              {isOpen ? t("tests.hide") : t("tests.viewPrompt")}
            </ToggleBtn>
            {isOpen && <Content>{p.content}</Content>}
          </PromptRow>
        );
      })}
    </Wrap>
  );
}
