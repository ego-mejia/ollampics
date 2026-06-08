import { useState } from "react";
import { useTranslation } from "react-i18next";
import { deleteRun, type RunSummary } from "../../../api";
import { StatusBadge } from "../../../components/Badge";
import Card from "../../../components/Card";
import { SectionTitle } from "../../../components/PageHeader";
import {
  HeaderRow,
  TBody,
  TD,
  TDEmpty,
  TDMono,
  TDMuted,
  TH,
  THCompact,
  THRight,
  THead,
  Table,
} from "../../../components/Table";
import { DeleteBtn, EmptyCode, IdLink, Section, SuccessCount, TotalCount } from "./style";

type Props = { runs: RunSummary[]; loading: boolean; onDeleted?: (id: number) => void };

export default function RunsSection({ runs, loading, onDeleted }: Props) {
  const { t } = useTranslation();
  const [busy, setBusy] = useState<number | null>(null);

  const onDelete = async (id: number) => {
    if (!window.confirm(t("dashboard.confirmDelete", { id }))) return;
    setBusy(id);
    try {
      await deleteRun(id);
      onDeleted?.(id);
    } catch (e) {
      window.alert(String(e));
    } finally {
      setBusy(null);
    }
  };

  return (
    <Section>
      <SectionTitle>
        {t("dashboard.runsTitle")} ({runs.length})
      </SectionTitle>
      <Card>
        <Table>
          <THead>
            <HeaderRow>
              <THCompact>{t("dashboard.cols.id")}</THCompact>
              <TH>{t("dashboard.cols.created")}</TH>
              <TH>{t("dashboard.cols.models")}</TH>
              <TH>{t("dashboard.cols.suites")}</TH>
              <THRight>{t("dashboard.cols.success")}</THRight>
              <TH>{t("dashboard.cols.status")}</TH>
              <TH className="w-10"></TH>
            </HeaderRow>
          </THead>
          <TBody>
            {loading ? (
              <tr>
                <TDEmpty colSpan={7}>{t("common.loading")}</TDEmpty>
              </tr>
            ) : runs.length === 0 ? (
              <tr>
                <TDEmpty colSpan={7}>
                  {t("dashboard.runsEmpty", { cmd: "" })}
                  <EmptyCode>oly run …</EmptyCode>
                </TDEmpty>
              </tr>
            ) : (
              runs.map((r) => (
                <tr
                  key={r.id}
                  className="group border-t border-border-soft hover:bg-elev/40 transition-colors"
                >
                  <TD>
                    <IdLink to={`/runs/${r.id}`}>#{r.id}</IdLink>
                  </TD>
                  <TDMuted>{r.created_at.replace("T", " ").slice(0, 19)}</TDMuted>
                  <TDMono>{r.config.models?.join(", ")}</TDMono>
                  <TD>{r.config.suites?.join(", ")}</TD>
                  <TD className="text-right">
                    <SuccessCount>{r.n_successes}</SuccessCount>
                    <TotalCount>/{r.n_attempts}</TotalCount>
                  </TD>
                  <TD>
                    <StatusBadge status={r.status} />
                  </TD>
                  <TD className="text-right pr-3">
                    <DeleteBtn
                      onClick={() => onDelete(r.id)}
                      disabled={busy === r.id}
                      title={t("dashboard.deleteRun")}
                      aria-label={t("dashboard.deleteRun")}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                        <path d="M10 11v6M14 11v6" />
                        <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
                      </svg>
                    </DeleteBtn>
                  </TD>
                </tr>
              ))
            )}
          </TBody>
        </Table>
      </Card>
    </Section>
  );
}
