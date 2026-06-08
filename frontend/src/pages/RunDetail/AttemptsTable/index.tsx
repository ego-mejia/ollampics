import { useTranslation } from "react-i18next";
import Card from "../../../components/Card";
import {
  HeaderRow,
  TBody,
  TDEmpty,
  TDMono,
  TDMutedRight,
  TDRight,
  TH,
  THRight,
  THead,
  Table,
} from "../../../components/Table";
import type { AttemptSummary } from "../../../api";
import { StatusError, StatusFail, StatusSuccess } from "./style";

type Props = { attempts: AttemptSummary[]; live: boolean };

export default function AttemptsTable({ attempts, live }: Props) {
  const { t } = useTranslation();

  return (
    <Card>
      <Table>
        <THead>
          <HeaderRow>
            <TH>{t("run.cols.model")}</TH>
            <TH>{t("run.cols.task")}</TH>
            <THRight>{t("run.cols.try")}</THRight>
            <TH>{t("run.cols.status")}</TH>
            <THRight>{t("run.cols.tps")}</THRight>
            <THRight>{t("run.cols.ttft")}</THRight>
            <THRight>{t("run.cols.tokIn")}</THRight>
            <THRight>{t("run.cols.tokOut")}</THRight>
            <THRight>{t("run.cols.vram")}</THRight>
            <THRight>{t("run.cols.watts")}</THRight>
            <THRight>{t("run.cols.wallS")}</THRight>
          </HeaderRow>
        </THead>
        <TBody>
          {attempts.length === 0 ? (
            <tr>
              <TDEmpty colSpan={11}>
                {live ? t("run.waitingFirst") : t("run.noAttempts")}
              </TDEmpty>
            </tr>
          ) : (
            attempts.map((a) => {
              const StatusCell =
                a.status === "success"
                  ? StatusSuccess
                  : a.status === "fail"
                    ? StatusFail
                    : StatusError;
              return (
                <tr key={a.id} className="border-t border-border-soft">
                  <TDMono>{a.model}</TDMono>
                  <TDMono>{a.task_id}</TDMono>
                  <TDMutedRight>{a.try_n}</TDMutedRight>
                  <StatusCell>{a.status}</StatusCell>
                  <TDRight>{a.tps_decode?.toFixed(1) ?? "—"}</TDRight>
                  <TDRight>{a.ttft_ms ?? "—"}</TDRight>
                  <TDMutedRight>{a.tokens_in ?? "—"}</TDMutedRight>
                  <TDMutedRight>{a.tokens_out ?? "—"}</TDMutedRight>
                  <TDMutedRight>
                    {a.peak_vram_mb ? `${a.peak_vram_mb}M` : "—"}
                  </TDMutedRight>
                  <TDMutedRight>{a.avg_watts?.toFixed(1) ?? "—"}</TDMutedRight>
                  <TDMutedRight>
                    {a.wall_time_s?.toFixed(2) ?? "—"}
                  </TDMutedRight>
                </tr>
              );
            })
          )}
        </TBody>
      </Table>
    </Card>
  );
}
