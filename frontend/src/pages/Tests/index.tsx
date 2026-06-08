import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { fetchTests, type SuiteCard } from "../../api";
import Alert from "../../components/Alert";
import PageHeader from "../../components/PageHeader";
import TestCard from "./TestCard";
import { Grid, PageWrap } from "./style";

export default function Tests() {
  const { t } = useTranslation();
  const [cards, setCards] = useState<SuiteCard[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTests()
      .then(setCards)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <PageWrap>
      <PageHeader title={t("tests.title")} subtitle={t("tests.subtitle")} />
      {err && <Alert>{err}</Alert>}
      {loading ? (
        <p className="text-fg-dim">{t("common.loading")}</p>
      ) : (
        <Grid>
          {cards.map((c) => (
            <TestCard key={c.name} card={c} />
          ))}
        </Grid>
      )}
    </PageWrap>
  );
}
