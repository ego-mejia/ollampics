import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import {
  deleteRun,
  fetchRun,
  openRunWebSocket,
  type RunDetail,
  type RunEvent,
} from "../../api";
import Badge from "../../components/Badge";
import AttemptsTable from "./AttemptsTable";
import SummaryCards from "./SummaryCards";
import {
  BackLink,
  DeleteBtn,
  MetaRow,
  PageTitle,
  PageWrap,
  TitleRow,
} from "./style";

const REFRESH_DEBOUNCE_MS = 250;

export default function RunDetailPage() {
  const { t } = useTranslation();
  const { runId } = useParams();
  const navigate = useNavigate();
  const [run, setRun] = useState<RunDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [wsState, setWsState] = useState<"connecting" | "open" | "closed">("connecting");
  const [deleting, setDeleting] = useState(false);

  const onDelete = async () => {
    if (!run) return;
    if (!window.confirm(t("dashboard.confirmDelete", { id: run.id }))) return;
    setDeleting(true);
    try {
      await deleteRun(run.id);
      navigate("/");
    } catch (e) {
      window.alert(String(e));
      setDeleting(false);
    }
  };

  useEffect(() => {
    if (!runId) return;
    const id = Number(runId);
    let cancelled = false;
    let pendingRefresh: ReturnType<typeof setTimeout> | null = null;

    const refresh = async () => {
      try {
        const data = await fetchRun(id);
        if (!cancelled) setRun(data);
      } catch (e) {
        if (!cancelled) setErr(String(e));
      }
    };

    // Debounce refreshes triggered by WS events — high-frequency `task.finished`
    // bursts shouldn't trigger N HTTP fetches.
    const scheduleRefresh = () => {
      if (pendingRefresh) return;
      pendingRefresh = setTimeout(() => {
        pendingRefresh = null;
        refresh();
      }, REFRESH_DEBOUNCE_MS);
    };

    // Initial full load
    refresh();

    // Open WebSocket subscription
    const ws = openRunWebSocket(
      id,
      (evt: RunEvent) => {
        if (cancelled) return;
        // Any of these events warrant a refetch of the full detail.
        const triggers = new Set([
          "ws.connected",
          "task.started",
          "task.finished",
          "task.skipped",
          "suite.finished",
          "model.finished",
          "run.finished",
        ]);
        if (evt.event === "ws.connected") setWsState("open");
        if (triggers.has(evt.event)) scheduleRefresh();
      },
      () => {
        if (!cancelled) setWsState("closed");
      }
    );

    ws.onerror = () => {
      if (!cancelled) setWsState("closed");
    };

    return () => {
      cancelled = true;
      if (pendingRefresh) clearTimeout(pendingRefresh);
      try {
        ws.close();
      } catch {
        // ignore
      }
    };
  }, [runId]);

  if (err)
    return (
      <PageWrap>
        <p className="text-brand-red">
          {t("common.error")}: {err}
        </p>
      </PageWrap>
    );
  if (!run)
    return (
      <PageWrap>
        <p className="text-fg-dim">{t("common.loading")}</p>
      </PageWrap>
    );

  const live = run.status === "running" || run.status === "queued";

  return (
    <PageWrap>
      <BackLink to="/">← {t("nav.dashboard")}</BackLink>
      <TitleRow>
        <PageTitle>
          {t("run.title")} #{run.id}
        </PageTitle>
        {live ? (
          <Badge variant="live">
            {t("run.live")} · {run.status}
          </Badge>
        ) : (
          <Badge variant="success">{run.status}</Badge>
        )}
        {live && (
          <span className="text-xs text-fg-dim">
            WS: {wsState === "open" ? "●" : wsState === "connecting" ? "○" : "✕"}
          </span>
        )}
        {!live && (
          <DeleteBtn
            onClick={onDelete}
            disabled={deleting}
            title={t("dashboard.deleteRun")}
            aria-label={t("dashboard.deleteRun")}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
              <path d="M10 11v6M14 11v6" />
            </svg>
            {deleting ? t("dashboard.deleting") : t("dashboard.deleteRun")}
          </DeleteBtn>
        )}
      </TitleRow>
      <MetaRow>
        {run.created_at.replace("T", " ").slice(0, 19)}
        {run.notes && ` · ${run.notes}`}
      </MetaRow>

      <SummaryCards attempts={run.n_attempts} successes={run.n_successes} />
      <AttemptsTable attempts={run.attempts} live={live} />
    </PageWrap>
  );
}
