import { useTranslation } from "react-i18next";
import { Stat } from "../../../components/Card";
import { CardsGrid } from "./style";

type Props = { attempts: number; successes: number };

export default function SummaryCards({ attempts, successes }: Props) {
  const { t } = useTranslation();
  const rate = attempts > 0 ? `${((successes / attempts) * 100).toFixed(0)}%` : "—";
  return (
    <CardsGrid>
      <Stat title={t("run.attempts")} value={`${attempts}`} />
      <Stat title={t("run.successes")} value={`${successes}`} variant="success" />
      <Stat title={t("run.successRate")} value={rate} />
    </CardsGrid>
  );
}
