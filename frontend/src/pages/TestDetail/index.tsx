import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { fetchTestDetail, type SuiteDetail } from "../../api";
import Alert from "../../components/Alert";
import RagPanel from "./RagPanel";
import TasksList from "./TasksList";
import {
  BackLink,
  Desc,
  Icon,
  PageTitle,
  PageWrap,
  TitleRow,
} from "./style";

export default function TestDetail() {
  const { t } = useTranslation();
  const { suite } = useParams();
  const [detail, setDetail] = useState<SuiteDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!suite) return;
    fetchTestDetail(suite)
      .then(setDetail)
      .catch((e) => setErr(String(e)));
  }, [suite]);

  if (err) return <PageWrap><Alert>{err}</Alert></PageWrap>;
  if (!detail) return <PageWrap><p className="text-fg-dim">{t("common.loading")}</p></PageWrap>;

  const label = t(`tests.suites.${detail.name}.label`, detail.label);
  const description = t(`tests.suites.${detail.name}.description`, detail.description);

  return (
    <PageWrap>
      <BackLink to="/tests">← {t("tests.title")}</BackLink>
      <TitleRow>
        <Icon>{detail.icon}</Icon>
        <PageTitle>{label}</PageTitle>
      </TitleRow>
      <Desc>{description}</Desc>

      {detail.name === "rag" ? <RagPanel /> : <TasksList detail={detail} />}
    </PageWrap>
  );
}
