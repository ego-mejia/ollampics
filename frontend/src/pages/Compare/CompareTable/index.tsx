import { useTranslation } from "react-i18next";
import Card from "../../../components/Card";
import {
  HeaderRow,
  TBody,
  TDEmpty,
  TDMono,
  TDMuted,
  TDRight,
  TH,
  THRight,
  THead,
  Table,
} from "../../../components/Table";
import type { CompareResponse } from "../../../api";
import {
  DiffMinus,
  DiffPlus,
  Section,
  StatBox,
  StatLabel,
  StatusError,
  StatusFail,
  StatusMissing,
  StatusSuccess,
  StatValue,
  StatValueAccent,
  StatValueWarn,
  Summary,
} from "./style";

type Props = { data: CompareResponse };

function statusCell(s: string | null) {
  if (s === "success") return <StatusSuccess>✓</StatusSuccess>;
  if (s === "fail") return <StatusFail>✗</StatusFail>;
  if (s === "error" || s === "timeout") return <StatusError>!</StatusError>;
  return <StatusMissing>—</StatusMissing>;
}

function diffPct(a: number | null, b: number | null) {
  if (a == null || b == null || a === 0) return null;
  const pct = ((b - a) / a) * 100;
  if (Math.abs(pct) < 2) return null;
  return pct;
}

export default function CompareTable({ data }: Props) {
  const { t } = useTranslation();
  const { run_a, run_b, entries, summary } = data;
  const labelA = `#${run_a.id}`;
  const labelB = `#${run_b.id}`;

  return (
    <>
      <Section>
        <Summary>
          <StatBox>
            <StatLabel>{t("compare.bothPass")}</StatLabel>
            <StatValueAccent>{summary.both_success}</StatValueAccent>
          </StatBox>
          <StatBox>
            <StatLabel>{t("compare.aOnly", { id: labelA })}</StatLabel>
            <StatValueWarn>{summary.a_only_success}</StatValueWarn>
          </StatBox>
          <StatBox>
            <StatLabel>{t("compare.bOnly", { id: labelB })}</StatLabel>
            <StatValueWarn>{summary.b_only_success}</StatValueWarn>
          </StatBox>
          <StatBox>
            <StatLabel>{t("compare.totalTasks")}</StatLabel>
            <StatValue>{summary.n_shared_tasks}</StatValue>
          </StatBox>
        </Summary>
      </Section>

      <Card>
        <Table>
          <THead>
            <HeaderRow>
              <TH>{t("compare.cols.task")}</TH>
              <TH>{t("compare.cols.suite")}</TH>
              <THRight>{labelA}</THRight>
              <THRight>{labelB}</THRight>
              <THRight>tps {labelA}</THRight>
              <THRight>tps {labelB}</THRight>
              <THRight>ttft {labelA}</THRight>
              <THRight>ttft {labelB}</THRight>
            </HeaderRow>
          </THead>
          <TBody>
            {entries.length === 0 ? (
              <tr>
                <TDEmpty colSpan={8}>{t("compare.noShared")}</TDEmpty>
              </tr>
            ) : (
              entries.map((e) => {
                const tpsDelta = diffPct(e.a_tps, e.b_tps);
                const ttftDelta = diffPct(e.a_ttft_ms, e.b_ttft_ms);
                return (
                  <tr
                    key={`${e.suite}:${e.task_id}`}
                    className="border-t border-border-soft"
                  >
                    <TDMono>{e.task_id}</TDMono>
                    <TDMuted>{e.suite}</TDMuted>
                    {statusCell(e.a_status)}
                    {statusCell(e.b_status)}
                    <TDRight>{e.a_tps?.toFixed(1) ?? "—"}</TDRight>
                    <TDRight>
                      {e.b_tps?.toFixed(1) ?? "—"}
                      {tpsDelta != null &&
                        (tpsDelta > 0 ? (
                          <DiffPlus>+{tpsDelta.toFixed(0)}%</DiffPlus>
                        ) : (
                          <DiffMinus>{tpsDelta.toFixed(0)}%</DiffMinus>
                        ))}
                    </TDRight>
                    <TDRight>{e.a_ttft_ms ?? "—"}</TDRight>
                    <TDRight>
                      {e.b_ttft_ms ?? "—"}
                      {ttftDelta != null &&
                        (ttftDelta < 0 ? (
                          <DiffPlus>{ttftDelta.toFixed(0)}%</DiffPlus>
                        ) : (
                          <DiffMinus>+{ttftDelta.toFixed(0)}%</DiffMinus>
                        ))}
                    </TDRight>
                  </tr>
                );
              })
            )}
          </TBody>
        </Table>
      </Card>
    </>
  );
}
