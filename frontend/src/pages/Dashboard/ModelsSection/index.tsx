import { useTranslation } from "react-i18next";
import Card from "../../../components/Card";
import { SectionTitle } from "../../../components/PageHeader";
import {
  HeaderRow,
  TBody,
  TDEmpty,
  TDMono,
  TDMutedRight,
  TH,
  THRight,
  THead,
  Table,
} from "../../../components/Table";
import type { ModelInfo } from "../../../api";
import { EmptyCode, Section, SizeCell } from "./style";

type Props = { models: ModelInfo[]; loading: boolean };

export default function ModelsSection({ models, loading }: Props) {
  const { t } = useTranslation();

  return (
    <Section>
      <SectionTitle>
        {t("dashboard.modelsTitle")} ({models.length})
      </SectionTitle>
      <Card>
        <Table>
          <THead>
            <HeaderRow>
              <TH>{t("common.name")}</TH>
              <THRight>{t("common.size")}</THRight>
            </HeaderRow>
          </THead>
          <TBody>
            {loading ? (
              <tr>
                <TDEmpty colSpan={2}>{t("common.loading")}</TDEmpty>
              </tr>
            ) : models.length === 0 ? (
              <tr>
                <TDEmpty colSpan={2}>
                  {t("dashboard.modelsEmpty", { cmd: "" })}
                  <EmptyCode>ollama pull &lt;name&gt;</EmptyCode>
                </TDEmpty>
              </tr>
            ) : (
              models.map((m) => (
                <tr key={m.name} className="border-t border-border-soft">
                  <TDMono>{m.name}</TDMono>
                  <TDMutedRight>
                    <SizeCell>
                      {(m.size_bytes / (1024 * 1024 * 1024)).toFixed(1)} GB
                    </SizeCell>
                  </TDMutedRight>
                </tr>
              ))
            )}
          </TBody>
        </Table>
      </Card>
    </Section>
  );
}
