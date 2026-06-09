import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { fetchRuns, type RunSummary } from "../../api";
import Alert from "../../components/Alert";
import { PrimaryRouterLink } from "../../components/Button";
import PageHeader from "../../components/PageHeader";
import ModelsChart from "./ModelsChart";
import RunsSection from "./RunsSection";
import { PageWrap } from "./style";

export default function Dashboard() {
  const { t } = useTranslation();
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refetchRuns = async () => {
    try {
      const r = await fetchRuns();
      setRuns(r);
    } catch (e) {
      setErr(String(e));
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const r = await fetchRuns();
        setRuns(r);
      } catch (e) {
        setErr(String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <PageWrap>
      <PageHeader
        title={t("dashboard.title")}
        subtitle={t("dashboard.subtitle")}
        actions={
          <PrimaryRouterLink to="/launcher">
            {t("dashboard.newRun")}
          </PrimaryRouterLink>
        }
      />

      {err && <Alert>{t("common.error")}: {err}</Alert>}

      <ModelsChart />

      <RunsSection runs={runs} loading={loading} onDeleted={refetchRuns} />
    </PageWrap>
  );
}
