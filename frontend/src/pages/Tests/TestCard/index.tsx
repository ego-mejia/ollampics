import { useTranslation } from "react-i18next";
import type { SuiteCard } from "../../../api";
import {
  CardHeader,
  CardLink,
  CorpusBadge,
  Desc,
  IconBlock,
  OpenAction,
  TasksBadge,
  Title,
} from "./style";

type Props = { card: SuiteCard };

export default function TestCard({ card }: Props) {
  const { t } = useTranslation();
  // i18n takes precedence; fall back to backend-provided strings if missing.
  const label = t(`tests.suites.${card.name}.label`, card.label);
  const description = t(`tests.suites.${card.name}.description`, card.description);
  return (
    <CardLink to={`/tests/${card.name}`}>
      <CardHeader>
        <IconBlock>{card.icon}</IconBlock>
        <div>
          <TasksBadge>{t("tests.tasksCount", { count: card.n_tasks })}</TasksBadge>
          {card.has_corpus && <CorpusBadge>{t("tests.withCorpus")}</CorpusBadge>}
        </div>
      </CardHeader>
      <Title>{label}</Title>
      <Desc>{description}</Desc>
      <OpenAction>{t("tests.openSuite")} →</OpenAction>
    </CardLink>
  );
}
