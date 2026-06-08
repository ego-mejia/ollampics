import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Primary } from "../../../../components/Button";
import { triggerCorpusGenerate } from "../../../../api";
import { ButtonsRow, Idle, Status } from "./style";

type Props = {
  onTriggered: () => void;
  hasCorpus: boolean;
};

export default function GenerateButton({ onTriggered, hasCorpus }: Props) {
  const { t } = useTranslation();
  const [working, setWorking] = useState(false);
  const [lastStartedAt, setLastStartedAt] = useState<string | null>(null);

  const fire = async (overwrite: boolean) => {
    setWorking(true);
    try {
      const resp = await triggerCorpusGenerate(overwrite);
      setLastStartedAt(resp.started_at);
      onTriggered();
    } finally {
      setTimeout(() => setWorking(false), 1500);
    }
  };

  return (
    <ButtonsRow>
      <Primary onClick={() => fire(false)} disabled={working}>
        {hasCorpus ? t("tests.regenerateBtn") : t("tests.generateBtn")}
      </Primary>
      {working && <Status>{t("tests.generating")}</Status>}
      {!working && lastStartedAt && (
        <Idle>
          {t("tests.generatedAt", {
            when: lastStartedAt.replace("T", " ").slice(0, 19),
          })}
        </Idle>
      )}
    </ButtonsRow>
  );
}
