import { useTranslation } from "react-i18next";
import SuiteIcon from "../../../components/SuiteIcon";
import { Body, Desc, IconSlot, Title, Wrap } from "./style";

type Props = { suite: string };

const TITLE_KEY = (suite: string) =>
  suite === "" ? "leaderboard.allSuitesTitle" : `tests.suites.${suite}.label`;

const DESC_KEY = (suite: string) =>
  suite === "" ? "leaderboard.allSuitesDesc" : `tests.suites.${suite}.description`;

export default function SuiteHeader({ suite }: Props) {
  const { t } = useTranslation();
  const iconName = suite || "all";
  const titleFallback = suite || t("common.all");
  return (
    <Wrap>
      <IconSlot>
        <SuiteIcon name={iconName} size={120} ariaLabel={iconName} />
      </IconSlot>
      <Body>
        <Title>{t(TITLE_KEY(suite), titleFallback)}</Title>
        <Desc>{t(DESC_KEY(suite), "")}</Desc>
      </Body>
    </Wrap>
  );
}
