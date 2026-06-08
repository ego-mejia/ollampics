import { useTranslation } from "react-i18next";
import SuiteIcon from "../../../components/SuiteIcon";
import { Body, Desc, IconSlot, Title, Wrap } from "./style";

export default function CompareHero() {
  const { t } = useTranslation();
  return (
    <Wrap>
      <IconSlot>
        <SuiteIcon name="compare" size={120} ariaLabel="compare" />
      </IconSlot>
      <Body>
        <Title>{t("compare.title")}</Title>
        <Desc>{t("compare.subtitle")}</Desc>
      </Body>
    </Wrap>
  );
}
