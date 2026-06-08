import { useTranslation } from "react-i18next";
import { Section, SectionTitle } from "../style";
import { Grid, MetricDesc, MetricName, Row } from "./style";

const KEYS = [
  "tps",
  "ttft",
  "tokensIn",
  "tokensOut",
  "vram",
  "watts",
  "successRate",
  "tries",
];

export default function MetricsSection() {
  const { t } = useTranslation();
  return (
    <Section>
      <SectionTitle>{t("home.metricsTitle")}</SectionTitle>
      <Grid>
        {KEYS.map((k) => (
          <Row key={k}>
            <MetricName>{t(`home.metrics.${k}.name`)}</MetricName>
            <MetricDesc>{t(`home.metrics.${k}.desc`)}</MetricDesc>
          </Row>
        ))}
      </Grid>
    </Section>
  );
}
