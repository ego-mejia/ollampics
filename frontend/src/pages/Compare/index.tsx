import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";
import {
  fetchCompare,
  fetchCompareOptions,
  type CompareResponse,
  type ModelBrief,
} from "../../api";
import Alert from "../../components/Alert";
import CompareHero from "./CompareHero";
import CompareSelector from "./CompareSelector";
import CompareTable from "./CompareTable";
import { PageWrap } from "./style";

export default function Compare() {
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();
  const [options, setOptions] = useState<ModelBrief[]>([]);
  const [data, setData] = useState<CompareResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const a = params.get("a");
  const b = params.get("b");

  useEffect(() => {
    fetchCompareOptions()
      .then(setOptions)
      .catch((e) => setErr(String(e)));
  }, []);

  useEffect(() => {
    if (!a || !b || a === b) {
      setData(null);
      return;
    }
    setLoading(true);
    fetchCompare(a, b)
      .then(setData)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, [a, b]);

  const setSelection = (na: string | null, nb: string | null) => {
    const next = new URLSearchParams(params);
    if (na) next.set("a", na);
    else next.delete("a");
    if (nb) next.set("b", nb);
    else next.delete("b");
    setParams(next, { replace: true });
  };

  return (
    <PageWrap>
      <CompareHero />
      {err && <Alert>{err}</Alert>}
      <CompareSelector options={options} valueA={a} valueB={b} onChange={setSelection} />
      {loading && <p className="text-fg-dim">{t("common.loading")}</p>}
      {!loading && !data && a && b && a === b && (
        <Alert>{t("compare.sameModel")}</Alert>
      )}
      {!loading && !data && (!a || !b) && (
        <p className="text-fg-dim">{t("compare.pickPair")}</p>
      )}
      {!loading && data && <CompareTable data={data} />}
    </PageWrap>
  );
}
